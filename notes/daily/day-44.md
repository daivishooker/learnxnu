# Day 44 — chmod / chown

> **正文：** [docs/day-44.md](../../docs/day-44.md)  
> **分析：** [day-44-analysis.md](day-44-analysis.md)

## chmod (#15)
- 入口：`fchmodat_internal` → `chmodat` → `chmod_vnode` → `vnode_setattr(va_mode)`
- 一句话：改路径对象的权限位

## chown (#16)
- 入口：`fchownat_internal` → `vn_chown_internal` → `vnode_setattr(uid/gid)`
- 一句话：改路径对象的属主/属组

## 今日对比
- 共同点：namei → 鉴权 → vnode_setattr；改元数据
- 最大差异：mode vs owner；chown 常需特权
