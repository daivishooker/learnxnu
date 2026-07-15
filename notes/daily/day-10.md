# Day 10 — link / rename

> **正文：** [docs/day-10.md](../../docs/day-10.md)  
> **分析：** [day-10-analysis.md](day-10-analysis.md)

## 硬链接 vs 符号链接（先记）
- 硬链接 `link`：多一个名字，**共用** vnode  
- 符号链接 `symlink`：有**自己的** `VLNK` vnode，里面是路径字符串

## link (#9)
- 入口：`link` → `linkat_internal` → 两次 namei → `VNOP_LINK`
- 一句话：给已有 vnode 在另一个（或同一）目录下再挂一个名字

## rename (#128)
- 入口：`rename` → `renameat_internal`
- 一句话：把 from 的目录项改成/移到 to（通常同文件系统）

## 今日对比
- link：名字变多；rename：名字搬家（旧名通常没了）
- 回扣：多硬链接 → vnode 可有多个「父目录项」
