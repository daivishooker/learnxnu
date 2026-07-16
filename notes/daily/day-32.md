# Day 32 — setrlimit / getrlimit

> **正文：** [docs/day-32.md](../../docs/day-32.md)  
> **分析：** [day-32-analysis.md](day-32-analysis.md)

## getrlimit (#194)
- 入口：`proc_limitget` → copyout
- 一句话：读 soft/hard 资源上限

## setrlimit (#195)
- 入口：copyin → `dosetrlimit`（校验 + 按 which 生效）
- 一句话：改上限；抬 hard 常要特权

## 今日对比
- 共同点：都针对进程 plimit 某一 which
- 最大差异：只读 vs 写并可能接到 CPU/VM/FD 子系统
