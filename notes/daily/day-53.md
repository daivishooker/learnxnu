# Day 53 — openat / fstatat64

> **正文：** [docs/day-53.md](../../docs/day-53.md)  
> **分析：** [day-53-analysis.md](day-53-analysis.md)

## openat (#463)
- 入口：`openat_internal` → `open1at` / `nameiat(dirfd)`
- 一句话：相对目录 FD 打开；`open` 即 AT_FDCWD 版

## fstatat64 (#470)
- 入口：`fstatat_internal` → `nameiat` → `vn_stat`
- 一句话：相对目录 FD 取 64 位 stat 元数据

## 今日对比
- 共同点：都用 nameiat 从 dirfd 起解析路径
- 最大差异：分配 FD 打开 vs 只读元数据
