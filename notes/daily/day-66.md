# Day 66 — thread_selfid / thread_selfusage / ledger / csrctl / ulock_wait / ulock_wake

> **正文：** [docs/day-66.md](../../docs/day-66.md)  
> **分析：** [day-66-analysis.md](day-66-analysis.md)

## 归属（今日起强制标注）

| 调用 | # | 标签 |
|------|---|------|
| thread_selfid | 372 | BSD→Mach |
| thread_selfusage | 482 | BSD→Mach |
| ledger | 373 | BSD→Mach |
| csrctl | 483 | BSD |
| ulock_wait / ulock_wake | 515 / 516 | BSD→Mach |

> 六个都在 BSD `sysent`；无 Mach trap。Mach = 实现落到 task/thread。

## 一句话
- thread_*：当前线程 id / CPU 用量  
- ledger：task 资源账本  
- csrctl：SIP/CSR  
- ulock_*：用户态锁内核 wait/wake（os_unfair_lock）
