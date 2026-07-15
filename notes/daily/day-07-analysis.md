# 源码分析：Day 7（stat64 / fstat64 / lstat64）

基于 `xnu-12377.121.6`。第 1 周收官：元数据查询。

---

## 1. 为什么是 `*64`？

老 `stat` 结构在大文件/大 inode 上不够用。用户态今天常用的是 **`stat64` 布局**（或兼容包装）。内核用 `isstat64` 开关决定填充哪种结构，再 `copyout`。

学习重点不在结构体每个字段，而在**三条入口如何汇合到 `vn_stat*`**。

---

## 2. 路径类：都进 `fstatat_internal`

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```c
stat64  → fstatat_internal(..., isstat64=1, AT_FDCWD, flag=0)
lstat64 → fstatat_internal(..., isstat64=1, AT_FDCWD, AT_SYMLINK_NOFOLLOW)
```

内部（简化）：

```
NDINIT(..., follow? FOLLOW : NOFOLLOW, path)
nameiat(ndp, AT_FDCWD)     // 路径 → vnode
vn_stat / vn_stat_noauth   // 填 stat 缓冲
copyout 到用户 ub
vnode_put / nameidone
```

| 调用 | follow | 对最后一级 symlink |
|------|--------|-------------------|
| stat64 | FOLLOW | 继续解析到目标 |
| lstat64 | NOFOLLOW | 停在链接本身 |

中间路径分量上的 symlink 行为由 namei 规则决定；**经典用户语义差别就在最后一级**。

---

## 3. fd 类：`sys_fstat64` → `fstat`

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c)：

```
sys_fstat64(fd, ub)
  → fstat(p, fd, ub, ..., isstat64=1)
      → fp_lookup
      → switch (f_type):
           VNODE  → vn_stat(_noauth)
           SOCKET → soo_stat
           PIPE   → pipe_stat
           ...
      → copyout
```

要点：

1. **无路径、无 FOLLOW/NOFOLLOW**  
2. 已打开且可读、又不求扩展安全信息时，可用 `vn_stat_noauth`（略过部分授权，仍用 `fg_cred`）  
3. 非文件 fd（socket 等）也能「stat」出一套兼容字段——类型多态，类似 Day 5 的 `fo_read`

---

## 4. 和前几天的关系

```
Day 4 open  → 得到 fd / vnode
Day 5 read  → 用 fd 搬数据
Day 6 dup   → 共享 fileglob
Day 7 stat  → 问元数据：
                有路径 → namei（跟或不跟链接）
                有 fd   → 直接从 fileproc
```

`access`（Day 4）也是路径检查但不给 fd；`stat*` 则把结果结构 copyout 给用户。

---

## 5. 建议点开的文件

1. `syscalls.master` — 338 / 339 / 340  
2. `vfs_syscalls.c` — `stat64` / `lstat64` 两行包装  
3. `vfs_syscalls.c` — `fstatat_internal` 里 `FOLLOW`/`NOFOLLOW` + `vn_stat`  
4. `kern_descrip.c` — `sys_fstat64` + `fstat` 的 `switch (type)`  

今天验收：画一张表，三列分别是「输入、是否跟随链接、核心函数」。
