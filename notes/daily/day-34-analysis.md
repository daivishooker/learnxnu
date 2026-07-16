# 源码分析：Day 34（sync / fsync）

基于 `xnu-12377.121.6`。刷盘：全系统 vs 单文件。

---

## 1. 心智模型

```text
sync:
  所有可写 mount → VFS_SYNC(mp)

fsync(fd):
  fd → vnode → VNOP_FSYNC(vp, MNT_WAIT)
```

脏数据多在 UBC/缓冲层；这两条是「请落稳」的显式入口。

---

## 2. sync

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
vfs_iterate → sync_callback
  跳过只读
  VFS_SYNC(mp, waitfor, …)
```

---

## 3. fsync / fdatasync

```
fsync        → fsync_common(..., MNT_WAIT)
fdatasync    → fsync_common(..., MNT_DWAIT)
fp_getfvp → VNOP_FSYNC
```

Day 14 已写过 fsync；今天补上与 sync 的对照。

---

## 4. 建议点开

1. `syscalls.master` — 36 / 95（及 187）  
2. `vfs_syscalls.c` — `sync` / `sync_callback` / `fsync_common`  

验收：能画两条刷盘路径；能说范围差别。
