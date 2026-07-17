# Day 41 — searchfs / fsgetpath

> **正文：** [docs/day-41.md](../../docs/day-41.md)  
> **分析：** [day-41-analysis.md](day-41-analysis.md)

## searchfs (#225)
- 入口：copyin `fssearchblock` → 起点 vnode → `VNOP_SEARCHFS`
- 一句话：让文件系统按条件在卷内搜索（可续搜）

## fsgetpath (#427)
- 入口：`fsgetpath_extended` → `vnode_getfromid` → `build_path`
- 一句话：用 fsid + objid 反查绝对路径

## 今日对比
- 共同点：都是「定位对象」类 VFS 能力，非读写文件内容
- 最大差异：条件批量搜 vs 单对象 ID→路径
