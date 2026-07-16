# Day 34 — sync / fsync

> **正文：** [docs/day-34.md](../../docs/day-34.md)  
> **分析：** [day-34-analysis.md](day-34-analysis.md)

## sync (#36)
- 入口：`vfs_iterate` → `sync_callback` → `VFS_SYNC`
- 一句话：遍历挂载点，推进各 FS 脏数据

## fsync (#95)
- 入口：`fsync_common(MNT_WAIT)` → `VNOP_FSYNC`
- 一句话：同步单个打开文件的 vnode

## 今日对比
- 共同点：都把脏数据往稳定存储推
- 最大差异：全系统 mount 扫描 vs 单 FD
