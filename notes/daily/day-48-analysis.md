# 源码分析：Day 48（readlink / readlinkat）

基于 `xnu-12377.121.6`。读取符号链接目标。

---

## 1. 心智模型

```text
readlink / readlinkat:
  nameiat(..., NOFOLLOW) → 必须 VLNK
  VNOP_READLINK → 用户缓冲里的目标路径字符串
```

---

## 2. 内部

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
readlinkat_internal
  lnk_vp 非空（freadlink）：直接用该 vnode
  否则 nameiat(NOFOLLOW)
  v_type != VLNK → EINVAL
  authorize → VNOP_READLINK
```

`readlink` = `AT_FDCWD`；`readlinkat` = 用户 dirfd。

---

## 3. 建议点开

1. `syscalls.master` — 58 / 473  
2. `vfs_syscalls.c` — `readlink` / `readlinkat` / `readlinkat_internal`  
3. 对照 Day 10 硬链/软链笔记（若有）  

验收：能说 NOFOLLOW 为何关键；Demo 能跑。
