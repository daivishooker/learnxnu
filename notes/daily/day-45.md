# Day 45 — utimes / futimes

> **正文：** [docs/day-45.md](../../docs/day-45.md)  
> **分析：** [day-45-analysis.md](day-45-analysis.md)

## utimes (#138)
- 入口：`namei` → `getutimes` → `setutimes` → `vnode_setattr`
- 一句话：按路径改 atime / mtime

## futimes (#139)
- 入口：`file_vnode` → 同一套 `setutimes`
- 一句话：按 vnode FD 改 atime / mtime

## 今日对比
- 共同点：时间进 vnode_attr；汇合 setutimes
- 最大差异：路径 namei vs FD（须为 vnode）
