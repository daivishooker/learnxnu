# Day 48 — readlink / readlinkat

> **正文：** [docs/day-48.md](../../docs/day-48.md)  
> **分析：** [day-48-analysis.md](day-48-analysis.md)

## readlink (#58)
- 入口：`readlinkat_internal(AT_FDCWD)` → NOFOLLOW → `VNOP_READLINK`
- 一句话：读出符号链接里存的目标路径字符串

## readlinkat (#473)
- 入口：同一 internal，目录 FD + 相对路径
- 一句话：从 dirfd 出发读链接目标

## 今日对比
- 共同点：不跟随；必须是 VLNK
- 最大差异：绝对/cwd 路径 vs 相对 dirfd
