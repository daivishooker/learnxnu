# Day 67 — psynch_mutexwait / mutexdrop / cvwait / cvsignal / cvbroad

> **正文：** [docs/day-67.md](../../docs/day-67.md)  
> **分析：** [day-67-analysis.md](day-67-analysis.md)

## 归属
- 全部 **BSD→Mach**：`sysent` → `pthread_shims.c` → `pthread_functions`（pthread.kext）

## 一句话
- mutexwait/drop：pthread_mutex 内核慢路径  
- cvwait/signal/broad：pthread_cond 内核慢路径  
- 用户调 pthread API，不直接调 psynch_*
