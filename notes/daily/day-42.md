# Day 42 — getxattr / setxattr

> **正文：** [docs/day-42.md](../../docs/day-42.md)  
> **分析：** [day-42-analysis.md](day-42-analysis.md)

## getxattr (#234)
- 入口：`namei` → `vn_getxattr` → `VNOP_GETXATTR`
- 一句话：按名字读扩展属性值

## setxattr (#236)
- 入口：`namei` → `vn_setxattr` → `VNOP_SETXATTR`
- 一句话：按名字写扩展属性值

## 今日对比
- 共同点：路径 → vnode → xattr VNOP；键值型元数据
- 最大差异：读 vs 写；CREATE/REPLACE 只在写侧有意义
