# Day 56 — fchmodat / fchownat

> **正文：** [docs/day-56.md](../../docs/day-56.md)  
> **分析：** [day-56-analysis.md](day-56-analysis.md)

## fchmodat (#467)
- 入口：`fchmodat_internal` → `chmodat` → `chmod_vnode`
- 一句话：相对目录 FD 改 mode（`va_mode`）

## fchownat (#468)
- 入口：`fchownat_internal` → `vn_chown_internal`
- 一句话：相对目录 FD 改 uid/gid；`lchown` 即 NOFOLLOW 特化

## 今日对比
- 共同点：都是 setattr；cwd 版汇入同一 *at_internal
- 最大差异：改权限位 vs 改属主/属组（后者常需特权）
