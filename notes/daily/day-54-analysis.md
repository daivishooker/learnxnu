# 源码分析：Day 54（renameat / unlinkat）

基于 `xnu-12377.121.6`。`*at` 重命名与删除。

---

## 1. 心智模型

```text
renameat(fromfd, from, tofd, to):
  nameiat 源 + nameiat 目标 → VNOP_RENAME

unlinkat(dirfd, path, flag):
  AT_REMOVEDIR → rmdirat_internal
  否则 unlinkat_internal → VNOP_REMOVE
```

---

## 2. 汇合关系

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
rename  → renameat_internal(AT_FDCWD, AT_FDCWD)
renameat → renameat_internal(fromfd, tofd)
unlink  → unlinkat_internal(AT_FDCWD)
unlinkat → unlinkat_internal 或 rmdirat_internal
```

---

## 3. 建议点开

1. `syscalls.master` — 465 / 472  
2. `vfs_syscalls.c` — `renameat_internal` / `unlinkat_internal`  
3. 对照 Day 9 / Day 10  

验收：能串起 openat/fstatat/renameat/unlinkat；Demo 能跑。
