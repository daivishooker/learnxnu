# Day 52 — getattrlistbulk / fsctl

> **正文：** [docs/day-52.md](../../docs/day-52.md)  
> **分析：** [day-52-analysis.md](day-52-analysis.md)

## getattrlistbulk (#461)
- 入口：目录 FD → `VNOP_GETATTRLISTBULK`（或 `readdirattr`）
- 一句话：一次从目录批量取出多条属性袋

## fsctl (#242)
- 入口：`namei` → `fsctl_internal` 按 cmd 分发
- 一句话：面向文件系统的 ioctl 式控制

## 今日对比
- 共同点：都是 Darwin VFS 增强能力
- 最大差异：批量读目录元数据 vs 发 FS 控制命令
