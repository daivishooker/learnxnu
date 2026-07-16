# Day 35 — statfs64 / fstatfs64

> **正文：** [docs/day-35.md](../../docs/day-35.md)  
> **分析：** [day-35-analysis.md](day-35-analysis.md)

## statfs64 (#345)
- 入口：`namei` → `v_mount` → `vfs_update_vfsstat` → copyout
- 一句话：按路径查文件系统统计

## fstatfs64 (#346)
- 入口：`file_vnode` → `v_mount` → 同上
- 一句话：按 FD 查文件系统统计

## 今日对比
- 共同点：都落到 mount；结果是 FS 级
- 最大差异：路径查找 vs 已有 FD
