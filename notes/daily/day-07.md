# Day 07 — stat64 / fstat64 / lstat64

> **正文：** [docs/day-07.md](../../docs/day-07.md)  
> **分析：** [day-07-analysis.md](day-07-analysis.md)

## stat64 (#338)
- 入口：`vfs_syscalls.c` → `fstatat_internal(..., FOLLOW)`
- 一句话：按路径取元数据，跟随最后一级符号链接

## fstat64 (#339)
- 入口：`kern_descrip.c` → `sys_fstat64` → `fstat`
- 一句话：按 fd 取元数据，不解析路径；vnode/socket/pipe 等分支

## lstat64 (#340)
- 入口：`fstatat_internal(..., AT_SYMLINK_NOFOLLOW)`
- 一句话：按路径取元数据，不跟随最后一级符号链接

## 今日对比
| | 输入 | 跟随 symlink |
|--|------|--------------|
| stat64 | path | 是 |
| lstat64 | path | 否 |
| fstat64 | fd | n/a |

## 第 1 周小结
身份查询 → FD 限制/污染标志 → open/close/access → read/write/lseek → dup → stat  
下一步进入目录与路径操作（Day 8+）。
