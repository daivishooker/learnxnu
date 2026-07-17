# 源码分析：Day 47（pathconf / fpathconf）

基于 `xnu-12377.121.6`。路径/FD 配置查询。

---

## 1. 心智模型

```text
pathconf(path, name):
  namei → vn_pathconf → VNOP_PATHCONF（或内核固定答案）

fpathconf(fd, name):
  fp → SOCKET/PIPE: 仅 _PC_PIPE_BUF
       VNODE: vn_pathconf
       other: EINVAL
```

---

## 2. pathconf

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c) →  
[`vn_pathconf`](../../xnu/bsd/vfs/vfs_vnops.c)：部分 `name` 直接填 retval，默认 `VNOP_PATHCONF`。

---

## 3. fpathconf

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c) 中 `sys_fpathconf`：  
按 `fp->f_type`（与 fileglob dtype 同类信息）分流。

---

## 4. 建议点开

1. `syscalls.master` — 191 / 192  
2. `vfs_syscalls.c` — `pathconf`  
3. `kern_descrip.c` — `sys_fpathconf`  
4. `vfs_vnops.c` — `vn_pathconf`  
5. `sys/unistd.h` — `_PC_*`  

验收：能说与 ftruncate 分流同构；Demo 能跑。
