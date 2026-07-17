# Day 58 — fgetxattr / fsetxattr / flistxattr / fremovexattr / fsetattrlist / getdirentriesattr

> **正文：** [docs/day-58.md](../../docs/day-58.md)  
> **分析：** [day-58-analysis.md](day-58-analysis.md)

## f*xattr（#235/#237/#241/#239）
- 入口：`file_vnode(fd)` → `vn_{get,set,list,remove}xattr`
- 一句话：路径 xattr 的 FD 版；无 namei，解析类 options → EINVAL

## fsetattrlist (#229)
- 入口：`file_vnode` → `setattrlist_internal`
- 一句话：setattrlist 的已打开 FD 版

## getdirentriesattr (#222)
- 入口：目录 FD → `VNOP_READDIRATTR`
- 一句话：老式「列目录+打包属性」；现代多用 getattrlistbulk

## 今日对比
- 共同点：都从已有 FD 出发，少拼路径
- 最大差异：xattr 键值 vs attrlist 位图 vs 目录批量枚举
