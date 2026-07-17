# Day 40 — clonefileat / fclonefileat

> **正文：** [docs/day-40.md](../../docs/day-40.md)  
> **分析：** [day-40-analysis.md](day-40-analysis.md)

## clonefileat (#462)
- 入口：`nameiat` 源 → `clonefile_internal` → `VNOP_CLONEFILE`
- 一句话：按路径在同卷上克隆出新名字

## fclonefileat (#517)
- 入口：源 FD → 同一 `clonefile_internal`
- 一句话：已打开对象上做克隆（可读 FD）

## 今日对比
- 共同点：同卷 CoW 风格克隆；目标不得已存在
- 最大差异：源用路径 vs 源用 FD
