# Day 09 — mkdir / rmdir / unlink

> **正文：** [docs/day-09.md](../../docs/day-09.md)  
> **分析：** [day-09-analysis.md](day-09-analysis.md)

## mkdir (#136)
- 入口：`mkdir` → `mkdir1at`（CREATE / OP_MKDIR）
- 细节：`mode & ~fd_cmask`；已存在 → EEXIST
- 一句话：在父目录下创建新目录名

## rmdir (#137)
- 入口：`rmdir` → `rmdirat_internal` → `vn_rmdir`
- 一句话：删除空目录对应的目录项

## unlink (#10)
- 入口：`unlink` → `unlinkat_internal`
- 一句话：删除路径上的名字（链接）；一般不用于删目录

## 今日对比
- 都改命名空间，不改 cwd  
- mkdir 创建；unlink/rmdir 删除（对象类型不同）
