# Day 36 — getfsstat64

> **正文：** [docs/day-36.md](../../docs/day-36.md)  
> **分析：** [day-36-analysis.md](day-36-analysis.md)

## getfsstat64 (#347)
- 入口：`vfs_iterate` → 每 mount `vfs_get_statfs64` → copyout 数组
- 一句话：一次列出多个文件系统统计

## 今日对比
- 与 Day 35：一个 mount vs 一批 mount
- 与 Day 34 sync：都扫挂载列表，一个刷、一个查
