# Day 43 — listxattr / removexattr

> **正文：** [docs/day-43.md](../../docs/day-43.md)  
> **分析：** [day-43-analysis.md](day-43-analysis.md)

## listxattr (#240)
- 入口：`namei` → `vn_listxattr` → `VNOP_LISTXATTR`
- 一句话：列出对象上所有扩展属性名（NUL 分隔）

## removexattr (#238)
- 入口：`copyinstr` 名 + `namei` → `vn_removexattr` → `VNOP_REMOVEXATTR`
- 一句话：按名字删除一个扩展属性

## 今日对比
- 共同点：都经 vnode xattr 包装层；补全 get/set 四件套
- 最大差异：列名 vs 删单个键
