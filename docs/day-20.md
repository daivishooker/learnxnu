# 第二十天（Day 20）正文

学这两个：**`kevent64` / `kevent_qos`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 19：已经会 `kqueue` + `kevent`。  
今天看同一条路上的两个演进版——结构更大、能力更多，尤其是 Darwin 上的 QoS / workqueue。

---

## 今天目标

1. 找到编号 **369 / 374**  
2. 理解三者关系：`kevent` → `kevent64` → `kevent_qos`  
3. 知道 `kevent64` 仍走 legacy 路径，只是事件结构/flags 升级  
4. 知道 `kevent_qos` 是更现代入口（可接 workqueue 等）

笔记：[`notes/daily/day-20.md`](../notes/daily/day-20.md)  
分析：[`notes/daily/day-20-analysis.md`](../notes/daily/day-20-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| kevent（回顾） | **363** | 经典接口，`struct kevent` |
| kevent64 | **369** | 64 位扩展结构 + flags |
| kevent_qos | **374** | 现代接口，带 QoS/扩展数据能力 |

核心没变：**还是往 kqueue 注册 knote、取就绪事件。**  
变的是事件结构、参数和 Darwin 扩展。

---

## 1. 三代怎么排

```text
kevent     (#363)  老 struct kevent，LEGACY32
    ↓
kevent64   (#369)  struct kevent64_s，多了 flags，仍标 LEGACY64
    ↓
kevent_qos (#374)  struct kevent_qos_s，走 modern 路径
                   可对接 workqueue / 更多 flags / data_out
```

源码里：

- `kevent` / `kevent64` → `kevent_legacy_internal` → `kevent_internal(..., legacy=true)`  
- `kevent_qos` → `kevent_modern_internal` → `kevent_internal(..., legacy=false)`  

所以：**邮箱还是 kqueue；接口一代代加字段、加系统集成。**

---

## 2. kevent64（#369）

[`kern_event.c`](../xnu/bsd/kern/kern_event.c)：

```c
kevent64(fd, changelist, nchanges, eventlist, nevents, flags, timeout)
  flags = (用户 flags) | KEVENT_FLAG_LEGACY64
  → kevent_legacy_internal(...)
```

和 `kevent` 比，你主要多感受到：

| | kevent | kevent64 |
|--|--------|----------|
| 事件结构 | `struct kevent` | `struct kevent64_s`（字段更宽/更全） |
| flags 参数 | 无（在 syscall 形参里） | **有** `unsigned int flags` |
| 超时 | `timespec *` | 同样有 |
| 内核路径 | legacy | legacy（标 LEGACY64） |

用法习惯仍是：

```text
kevent64(kq, &change, 1, NULL, 0, 0, NULL);     // 登记
kevent64(kq, NULL, 0, &event, 1, 0, NULL);     // 取事件
```

先建立「比 kevent 多了 64 位结构和 flags」的印象即可。

---

## 3. kevent_qos（#374）——现代入口

```c
kevent_qos(fd, changelist, nchanges, eventlist, nevents,
           data_out, data_available, flags)
  若 flags 带 WORKQ → 拿进程的 workqueue kqueue
  否则 → 仍按 fd 拿普通 kqueue 文件
  → kevent_modern_internal(...)
```

相对前两代，多出来的直觉：

1. **事件结构是 `kevent_qos_s`**（含 QoS 等相关信息）  
2. **`flags` 更重要**：可走 workqueue 等模式（`KEVENT_FLAG_WORKQ`…）  
3. **`data_out` / `data_available`**：可附带额外数据缓冲区（不只事件头）  
4. 给 **libdispatch / GCD** 这类用户态调度用得很重——事件来了按 QoS 派线程干活  

对学习：不必一天啃完 workqueue；记住——

> `kevent_qos` = 还是 kqueue 事件口，但面向「带优先级/工作队列」的现代 Darwin 运行时。

---

## 今日对比

| | kevent | kevent64 | kevent_qos |
|--|--------|----------|------------|
| 编号 | 363 | 369 | 374 |
| 结构 | kevent | kevent64_s | kevent_qos_s |
| 内核标签 | LEGACY32 | LEGACY64 | modern |
| 典型场景 | 老代码 | 64 位/多 flags | GCD/workq/现代运行时 |

```text
select/poll     → 每次交兴趣表
kevent 家族     → 兴趣留在 kqueue
kevent64/qos    → 同一模型，结构与系统集成升级
```

---

## 做完打勾

- [ ] 找到 369 / 374  
- [ ] 能说三者都操作 kqueue，差别在结构/路径  
- [ ] 能说 kevent64 ≈ legacy 升级版  
- [ ] 能说 kevent_qos 接 QoS/workqueue 方向  
- [ ] 填好 `notes/daily/day-20.md`

下一步：Day 21 → `ioctl` / `sysctl` / `getrlimit`
