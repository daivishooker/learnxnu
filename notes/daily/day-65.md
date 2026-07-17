# Day 65 — proc_info / csops / csops_audittoken / workq_open / workq_kernreturn

> **正文：** [docs/day-65.md](../../docs/day-65.md)  
> **分析：** [day-65-analysis.md](day-65-analysis.md)

## proc_info (#336)
- 入口：`proc_info_internal` 按 callnum 分流
- 一句话：进程信息/控制总闸（libproc 背后）

## csops / csops_audittoken (#169 / #170)
- 入口：`csops_internal`；token 版需 audittoken
- 一句话：代码签名状态与 blob；防 PID 复用

## workq_open / workq_kernreturn (#367 / #368)
- 入口：分配/操作进程 workqueue；要线程等
- 一句话：libpthread/GCD 线程池内核侧

## 今日对比
- 共同点：偏 Darwin SPI，用户少直接调用
- 最大差异：查进程 vs 代码签名 vs 线程池
