# Day 19 — select / poll / kevent

> **正文：** [docs/day-19.md](../../docs/day-19.md)  
> **分析：** [day-19-analysis.md](day-19-analysis.md)

## select (#93)
- 入口：`sys_generic.c` → `select` → `select_internal` → `selprocess`
- 一句话：三份 fd 位图 + 超时，等可读/可写/异常

## poll (#230)
- 入口：`poll` → 本树转成临时 kqueue/kevent
- 一句话：pollfd 数组描述兴趣；实现上已靠 kqueue

## kevent (#363)
- 入口：`kern_event.c` → `kevent` → `kevent_internal`
- 一句话：在持久 kqueue 上增删兴趣、取出就绪事件

## 今日对比
- 共同点：多路等待，避免一 FD 阻塞卡死全局
- 最大差异：select/poll 无状态每次重交；kevent 状态留在 kqueue
