# Day 46 — truncate / ftruncate

> **正文：** [docs/day-46.md](../../docs/day-46.md)  
> **分析：** [day-46-analysis.md](day-46-analysis.md)

## truncate (#200)
- 入口：`namei` → `truncate_internal` → `vnode_setattr(va_data_size)`
- 一句话：按路径改文件逻辑长度

## ftruncate (#201)
- 入口：`fp_lookup` → `FILEGLOB_DTYPE` 分流 →（vnode）`truncate_internal`
- 一句话：按 FD 截断；shm 另走 pshm_truncate

## 今日对比
- 共同点：validate RLIMIT_FSIZE；改 size 属性
- 最大差异：路径总走 vnode；FD 先按 dtype 分流
