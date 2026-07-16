# 第十九天（Day 19）正文

学这三个：**`select` / `poll` / `kevent`**  
源码：`xnu/` = **xnu-12377.121.6**

离开信号，进入**多路 IO**：同时盯多个 FD，哪个可读/可写再处理——不用每个 FD 傻等阻塞。

生活类比：你同时盯好几扇门（socket/管道…），有人敲门再去开，而不是站在一扇门前死等。

---

## 今天目标

1. 找到编号 **93 / 230 / 363**  
2. 理解三代接口各自怎么描述“要盯的 FD”  
3. 知道本树里 `poll` 会落到 **kqueue/kevent**  
4. 为 Day 20 的 `kevent64` / `kevent_qos` 打底

笔记：[`notes/daily/day-19.md`](../notes/daily/day-19.md)  
分析：[`notes/daily/day-19-analysis.md`](../notes/daily/day-19-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| select | **93** | 用三组 fd_set 位图等可读/可写/异常 |
| poll | **230** | 用 `pollfd[]` 数组等事件 |
| kevent | **363** | 在 **kqueue** 上注册/收取事件 |

---

## 1. select（#93）——位图三代里最老

[`sys_generic.c`](../xnu/bsd/kern/sys_generic.c)：

```c
select(nd, in, ou, ex, tv)
  → select_nocancel → select_internal
       copyin 三份位图（读/写/异常）
       selprocess：扫 FD、注册等待；有就绪就返回，否则睡到超时
```

你传入：

- `nd`：关心的最大 fd+1  
- `in` / `ou` / `ex`：三张位图（哪些 FD 想读/写/异常）  
- `tv`：超时（可为 NULL）

返回后位图被改成“真正就绪的那些”。

缺点直觉：FD 很大时位图又大又要反复 copyin/copyout；每次调用都要重交一整套兴趣集。

---

## 2. poll（#230）——数组更直观

```c
poll(fds, nfds, timeout)
  copyin pollfd[]
  // 本树实现：内部建临时 kqueue，把 poll 事件转成 kevent 注册
  等事件 → 填 revents → copyout
```

每个 `pollfd`：`fd` + 想看的 `events` + 内核填的 `revents`（`POLLIN`/`POLLOUT`…）。

比 select 清晰：一对一项，不玩大位图。  
本树亮点：**用户还在调 poll，内核已经用 kqueue 实现。**

---

## 3. kevent（#363）——Darwin 主力事件口

先有一个 **kqueue**（通常 `kqueue()` 得到一个 FD），再：

```c
kevent(kq_fd, changelist, nchanges, eventlist, nevents, timeout)
  → 拿到 kqueue
  → kevent_internal：
       处理 changelist：EV_ADD/DELETE… 注册/改 knote
       从队列取出就绪事件 → eventlist
```

和 select/poll 的关键差别：

| | select / poll | kevent |
|--|---------------|--------|
| 兴趣集 | **每次调用都带齐** | 存在 **kqueue 里**，可增量改 |
| 能盯的 | 主要是 FD 读写 | FD + 进程/信号/定时器…（filter） |
| 扩展 | 老接口 | Darwin 上继续演变成 kevent64/qos |

`changelist` = 本次要改的注册；`eventlist` = 本次取回的事件。

---

## 今日对比（三代）

```text
select  位图，老而通用
poll    数组，更清晰；本树内部 → kqueue
kevent  持久队列 + 过滤器；现代服务器常用
```

| | select | poll | kevent |
|--|--------|------|--------|
| 描述兴趣 | fd_set 位图 | pollfd[] | kevent 变更列表 |
| 状态存在哪 | 每次调用 | 每次调用 | **kqueue 对象** |
| 本树实现文件 | `sys_generic.c` | 同左（转 kevent） | `kern_event.c` |

---

## 做完打勾

- [ ] 找到 93 / 230 / 363  
- [ ] 能说三者都是“等多个 IO 就绪”  
- [ ] 能说 kevent 靠持久 kqueue；select/poll 每次重交兴趣  
- [ ] 知道本树 poll → kqueue  
- [ ] 填好 `notes/daily/day-19.md`

下一步：Day 20 → [`kevent64` / `kevent_qos`](day-20.md)
