# Day 33 — sys_flock

> **正文：** [docs/day-33.md](../../docs/day-33.md)  
> **分析：** [day-33-analysis.md](day-33-analysis.md)

## sys_flock (#131)
- 入口：`kern_descrip.c` → `VNOP_ADVLOCK`（`F_FLOCK`）
- 一句话：对 vnode 整文件劝告锁（SH/EX/UN，可选 NB）

## 对照
- fcntl 字节锁：同一 VNOP，`F_POSIX` 等语义
- 劝告：协作进程遵守；不保证强制挡所有读写

## 今日对比
- 与 Day 14 fcntl：锁是 fcntl 家族亲戚
- 与 socket：都是 FD 找对象，但对象是 vnode 锁状态
