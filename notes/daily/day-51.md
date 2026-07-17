# Day 51 — chflags / fchflags

> **正文：** [docs/day-51.md](../../docs/day-51.md)  
> **分析：** [day-51-analysis.md](day-51-analysis.md)

## chflags (#34)
- 入口：`namei` → `chflags1` → `vnode_setattr(va_flags)`
- 一句话：按路径设置 BSD 文件标志

## fchflags (#35)
- 入口：`file_vnode` → 同一 `chflags1`
- 一句话：按 vnode FD 设置文件标志

## 今日对比
- 共同点：都落到 va_flags；成功后可同步 VE_APPENDONLY
- 最大差异：路径 vs FD；与 chmod 的 rwx 权限不同层
