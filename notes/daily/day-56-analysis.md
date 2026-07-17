# 源码分析：Day 56（fchmodat / fchownat）

基于 `xnu-12377.121.6`。`*at` 改权限与属主。

---

## 1. 心智模型

```text
fchmodat(dirfd, path, mode, flag):
  va_mode = mode & ALLPERMS
  nameiat(dirfd) → chmod_vnode → vnode_setattr

fchownat(dirfd, path, uid, gid, flag):
  nameiat(dirfd) → vn_chown_internal → vnode_setattr
```

---

## 2. 汇合关系

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
chmod   → fchmodat_internal(AT_FDCWD, flag=0)
fchmodat → fchmodat_internal(fd, flag)
chown   → fchownat_internal(AT_FDCWD, flag=0)
lchown  → fchownat_internal(AT_FDCWD, AT_SYMLINK_NOFOLLOW)
fchownat → fchownat_internal(fd, flag)
```

`fchmod` / `fchown` 不走路径：`file_vnode(fd)` → 同一套 setattr。

---

## 3. 建议点开

1. `syscalls.master` — 467 / 468  
2. `vfs_syscalls.c` — `fchmodat_internal` / `chmodat` / `fchownat_internal`  
3. 对照 Day 44 `chmod`/`chown`、Day 53–55 `*at`

验收：能串起 chmod→fchmodat、chown/lchown→fchownat；Demo 能跑。
