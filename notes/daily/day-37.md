# Day 37 — getdirentries64 / getattrlist

> **正文：** [docs/day-37.md](../../docs/day-37.md)  
> **分析：** [day-37-analysis.md](day-37-analysis.md)

## getdirentries64 (#344)
- 入口：`getdirentries_common` → `vnode_readdir64` / `VNOP_READDIR`
- 一句话：从目录 FD 读一批目录项

## getattrlist (#220)
- 入口：`vfs_attrlist.c` → copyin attrlist → 路径 vnode → 打包属性
- 一句话：按需取路径对象的属性袋

## 今日对比
- 共同点：都经 VFS/vnode
- 最大差异：枚举目录内容 vs 查单个对象属性
