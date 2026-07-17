# Day 68 — psynch_rw_rdlock / wrlock / unlock / upgrade / downgrade

> **正文：** [docs/day-68.md](../../docs/day-68.md)  
> **分析：** [day-68-analysis.md](day-68-analysis.md)

## 归属
- `rdlock` / `wrlock` / `unlock`：**BSD→Mach**（shim → pthread.kext）  
- `upgrade` / `downgrade`：BSD 入口存在，本树 shim **stub 返回 0**

## 一句话
- 读写锁慢路径：多读者或单写者争用时进内核等  
- 用户调 `pthread_rwlock_*`；内核仍只认用户态地址 + 代数旁路  
- upgrade/downgrade 编号还在，实现是空壳
