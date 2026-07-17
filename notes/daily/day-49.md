# Day 49 — symlink / symlinkat

> **正文：** [docs/day-49.md](../../docs/day-49.md)  
> **分析：** [day-49-analysis.md](day-49-analysis.md)

## symlink (#57)
- 入口：`symlinkat_internal(AT_FDCWD)` → `VNOP_SYMLINK`
- 一句话：创建存目标路径字符串的 VLNK

## symlinkat (#474)
- 入口：同一 internal，dirfd + 相对链接名
- 一句话：相对目录 FD 创建符号链接

## 今日对比
- 共同点：目标串 copyinstr；父目录 CREATE；不要求目标存在
- 最大差异：cwd/绝对路径 vs dirfd 相对
