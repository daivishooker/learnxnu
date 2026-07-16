# 源码分析：Day 19（select / poll / kevent）

基于 `xnu-12377.121.6`。多路 IO 三代接口。

---

## 1. 心智模型

```text
问题：同时盯很多 FD，哪个有数据/能写再处理

select：三张位图（读/写/异常）
poll：  一张表（每个 FD 一行）
kevent：一个邮箱（kqueue），事先订阅，有事再取信
```

---

## 2. select 主路径

[`sys_generic.c`](../../xnu/bsd/kern/sys_generic.c)：

```
select → select_nocancel
  解析 timeval → deadline
  select_internal
    copyin in/ou/ex 位图
    selcount / selprocess
      第一趟：看谁已就绪、谁要睡
      未就绪：等待；醒后再扫
    结果写回用户位图，*retval = 就绪个数
```

线程侧有 `uu_select` 缓存位图空间，避免每次狂分配。

---

## 3. poll 主路径（本树特色）

```
poll_nocancel
  kqueue_alloc(临时)
  copyin pollfd[]
  每个感兴趣的 events → kevent_register(EVFILT_READ/WRITE…)
  等待 / 收集 → 填 revents
  copyout；释放临时 kqueue
```

教学结论：**API 是 poll，引擎已是 kevent。**  
说明 kqueue 才是 Darwin 上统一的等待原语。

---

## 4. kevent 主路径

[`kern_event.c`](../../xnu/bsd/kern/kern_event.c)：

```
kevent(kqfd, changelist, nchanges, eventlist, nevents, timeout)
  kevent_get_kqfile → 拿到 kqueue
  kevent_internal
    应用 changelist（EV_ADD / EV_DELETE / EV_ENABLE…）
    等待并取出最多 nevents 个就绪事件 → eventlist
```

核心对象：

- **kqueue**：事件队列（常对应一个 FD）  
- **knote**：一条注册（某 filter + ident，如某 FD 可读）  

Day 20 会看 `kevent64` / `kevent_qos`：同一家族的演进。

---

## 5. 三代怎么选（学习用）

| 场景 | 更常见 |
|------|--------|
| 老代码 / 极简 | select / poll |
| macOS/iOS 新代码 | **kqueue + kevent*** |
| 要进程退出、信号、定时器等同队列 | kevent（filter） |

---

## 6. 建议点开的文件

1. `syscalls.master` — 93 / 230 / 363  
2. `sys_generic.c` — `select_internal`、`poll_nocancel` 里 `kevent_register`  
3. `kern_event.c` — `kevent` / `kevent_internal` 注释  

验收：能画“盯多扇门”；能说 kevent 的状态在 kqueue 里。
