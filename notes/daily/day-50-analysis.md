# 源码分析：Day 50（mknod / mkfifo）

基于 `xnu-12377.121.6`。设备节点与命名管道。

---

## 1. 心智模型

```text
mknod(path, mode, dev):
  S_IFIFO → mkfifo1
  否则 suser → CREATE → VCHR/VBLK + va_rdev → vn_create

mkfifo(path, mode):
  CREATE → VFIFO → vn_create
```

---

## 2. mknod

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
mknodat_internal
  FIFO 短路到 mkfifo1
  suser 检查
  nameiat CREATE
  仅 S_IFCHR / S_IFBLK
  authorize → vn_create
```

---

## 3. mkfifo

```
mkfifo1
  nameiat CREATE；已存在 EEXIST
  va_type = VFIFO
  vn_authorize_create → vn_create
```

---

## 4. 建议点开

1. `syscalls.master` — 14 / 132  
2. `vfs_syscalls.c` — `mknod` / `mknodat_internal` / `mkfifo` / `mkfifo1`  

验收：能说特权边界与 FIFO 转交；Demo 至少跑通 mkfifo。
