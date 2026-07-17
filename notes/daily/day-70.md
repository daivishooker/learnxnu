# Day 70 — bsdthread_register / ctl / disable_threadsignal / markcancel / canceled

> **正文：** [docs/day-70.md](../../docs/day-70.md)  
> **分析：** [day-70-analysis.md](day-70-analysis.md)

## 归属
- `bsdthread_register`：**BSD→Mach**（pthread.kext）  
- `bsdthread_ctl`：**BSD→Mach**（XNU `pthread_workqueue.c`，不走 kext 表）  
- `__disable_threadsignal` / `__pthread_canceled`：**BSD**（`uthread` 标志）  
- `__pthread_markcancel`：**BSD→Mach**（标志 + `thread_abort_safely`）

## 一句话
- register：进程级登记 pthread/workq 入口  
- ctl：QoS / workq 杂项控制  
- markcancel/canceled：`pthread_cancel` 内核协作路径（不是 `pthread_kill`）
