# Day 27 — ptrace / sysctl（安全回顾）

> **正文：** [docs/day-27.md](../../docs/day-27.md)  
> **分析：** [day-27-analysis.md](day-27-analysis.md)

## ptrace (#26)
- 入口：`mach_process.c` → `PT_ATTACH` / `PT_DENY_ATTACH` / 已跟踪后的操作
- 一句话：调试接口；attach 前过 kauth/MAC 等门禁

## sysctl (#202)
- 入口：`kern_newsysctl.c` → `userland_sysctl`（Day 21 回顾）
- 一句话：配置树读写；写与敏感读受节点权限约束

## 今日对比
- 共同点：宽入口 + 策略收窄的控制面
- 最大差异：盯进程 vs 盯系统参数
