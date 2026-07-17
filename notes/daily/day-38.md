# Day 38 — setattrlist / fgetattrlist

> **正文：** [docs/day-38.md](../../docs/day-38.md)  
> **分析：** [day-38-analysis.md](day-38-analysis.md)

## setattrlist (#221)
- 入口：`namei` → `setattrlist_internal` → copyin 属性袋 → `vnode_setattr`
- 一句话：按 attrlist 写路径对象的可设属性

## fgetattrlist (#228)
- 入口：FD → vnode → `getattrlist_internal`（与路径版读汇合）
- 一句话：已打开对象上按需读属性

## 今日对比
- 共同点：都用 attrlist 点菜；都落在 vnode 元数据
- 最大差异：写 vs 读；路径查找 vs FD
