# 源码分析：Day 53（openat / fstatat64）

基于 `xnu-12377.121.6`。`*at` 打开与取元数据。

---

## 1. 心智模型

```text
openat(dirfd, path):
  openat_internal → nameiat(dirfd) → 打开逻辑 → 新 FD

fstatat64(dirfd, path):
  nameiat(dirfd) → vn_stat → copyout stat64
```

---

## 2. openat

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
open / open_nocancel → openat_internal(..., AT_FDCWD)
openat → openat_internal(..., uap->fd)
```

---

## 3. fstatat64

```
fstatat_internal(..., isstat64=1, fd, flag)
  FOLLOW/NOFOLLOW 由 AT_SYMLINK_NOFOLLOW*
  nameiat；vn_stat；打包用户 stat 结构
```

`stat64`/`lstat64`/`fstat64` 也汇入同一 internal（不同参数组合）。

---

## 4. 建议点开

1. `syscalls.master` — 463 / 470  
2. `vfs_syscalls.c` — `openat_internal` / `fstatat_internal`  
3. 对照 Day 4 `open`、Day 7 `stat64`  

验收：能说 *at 相对 dirfd 的意义；Demo 能跑。
