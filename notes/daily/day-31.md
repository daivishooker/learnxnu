# Day 31 — getpriority / setpriority

> **正文：** [docs/day-31.md](../../docs/day-31.md)  
> **分析：** [day-31-analysis.md](day-31-analysis.md)

## getpriority (#100)
- 入口：`kern_resource.c`；经典路径读 `p_nice`（组/用户取最小）
- 一句话：查 nice / 相关优先级

## setpriority (#96)
- 入口：`donice` → 写 `p_nice` → `resetpriority`
- 一句话：改 nice；提高优先级常要特权

## 今日对比
- 共同点：都按 which/who 选目标；经典锚点是 p_nice
- 最大差异：只读汇总 vs 写并影响调度
