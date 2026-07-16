# Day 30 — getrusage / gettimeofday

> **正文：** [docs/day-30.md](../../docs/day-30.md)  
> **分析：** [day-30-analysis.md](day-30-analysis.md)

## getrusage (#117)
- 入口：`kern_resource.c` → `calcru` / `p_ru` / `p_cru` → copyout
- 一句话：查自己或已回收子进程的资源使用

## gettimeofday (#116)
- 入口：`kern_time.c` → `clock_gettimeofday_and_absolute_time` → copyout
- 一句话：读墙钟时间（可选 Mach absolute）

## 今日对比
- 共同点：只读查询；结果 copyout 给用户
- 最大差异：进程资源账 vs 系统日历时间
