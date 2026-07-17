# 源码分析：Day 63（umask 与 mlock）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
umask → fd_cmask
  open/mkdir/... 创建：mode & ~fd_cmask

mlock(addr,len)   → vm_map_wire_kernel
munlock(addr,len) → vm_map_unwire
mlockall/munlockall → ENOSYS（本树）
```

---

## 2. 建议点开

1. `syscalls.master` — 60 / 203 / 204 / 324 / 325  
2. `vfs_syscalls.c` — `umask1`  
3. `kern_mman.c` — `mlock` / `munlock` / stubs  
4. 对照 Day 9/15/55 创建路径与 mmap

验收：能说 cmask 怎么咬 mode；mlock=wire；Demo 能跑。
