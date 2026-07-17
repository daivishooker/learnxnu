# Day 69 — longrdlock / yieldwrlock / cvclrprepost / bsdthread_create / terminate

> **正文：** [docs/day-69.md](../../docs/day-69.md)  
> **分析：** [day-69-analysis.md](day-69-analysis.md)

## 归属
- 全部 **BSD→Mach**：`sysent` → `pthread_shims.c` → `pthread_functions`（pthread.kext）  
- `bsdthread_terminate` 转发前有 workq / join-ulock 预处理

## 一句话
- longrdlock：历史槽，现行常 ESRCH  
- yieldwrlock：写锁等待变体  
- cvclrprepost：清 cond/mutex 的 prepost  
- bsdthread_create / terminate：`pthread_create` / 线程退出的内核路
