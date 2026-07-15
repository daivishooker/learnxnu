# 源码分析：Day 8（chdir / fchdir，兼 getcwd）

基于 `xnu-12377.121.6`。第 2 周第一天：当前工作目录。

---

## 1. cwd 在内核里是什么？

不是「字符串 `/Users/foo`」，而是进程描述符结构里的一个 **目录 vnode 指针**：

```c
p->p_fd.fd_cdir   // 进程级 cwd
uth->uu_cdir      // 可选：每线程 cwd（__pthread_*chdir）
```

相对路径（Day 4 `open("a.txt")`、`AT_FDCWD`）最终都相对这个 vnode 解析。

---

## 2. chdir：路径 → 新 cwd

```
sys_chdir (#12)
  → common_chdir(per_thread=0)
  → NDINIT(OP_CHDIR, FOLLOW, path)
  → chdir_internal
       change_dir(...)     // namei + 必须是目录 + 授权
       vnode_ref(新目录)
       换掉 p->p_fd.fd_cdir
       vnode_rele(旧目录)
```

和 `stat64` 一样先走路径解析；差别是结果不是 copyout 元数据，而是**换进程的 cwd 指针**。

---

## 3. fchdir：目录 fd → 同一 cwd 槽

```
sys_fchdir (#13)
  → fchdir(fd)
       file_vnode(fd)
       v_type 必须是 VDIR，否则 ENOTDIR
       authorize SEARCH
       若目录上有挂载，可能下到 mounted root
       换 p->p_fd.fd_cdir
```

你已 `open(".", O_RDONLY)` 或 `open("/tmp", …)` 拿到的目录 fd，可以不拼路径再切过去——对 `chroot`/沙盒/已打开句柄场景很有用。

---

## 4. 为什么说 getcwd「不是这条主线里的 syscall」？

核对 `bsd/kern/syscalls.master`：**没有** `getcwd` / `__getcwd` 表项。

含义：

1. 内核权威状态是 **vnode**，不是必须缓存的绝对路径字符串（路径可能因 rename/mount 变化）。  
2. 用户态 libc 的 `getcwd()` 是库函数；在 Darwin 上常见实现会借助 **`fcntl(..., F_GETPATH, ...)`**（见 `sys/fcntl.h` 与 `kern_descrip.c` 中 `case F_GETPATH`）从某个目录 fd 反查路径。  
3. 学习计划里写「getcwd 相关*」就是提醒你：**别在 master 里找同名编号；先把 chdir/fchdir 看懂。**

（若你在别的 Unix 上看过 `__getcwd` syscall，那是别的实现；以本树为准。）

---

## 5. 可选：每线程 cwd

`__pthread_chdir` / `__pthread_fchdir` 把目录写到 `uthread.uu_cdir`，并置 `P_THCWD`。  
多数程序只用进程级 `fd_cdir`；知道有这条支线即可。

---

## 6. 建议点开的文件

1. `syscalls.master` — 12 / 13（并确认没有 getcwd）  
2. `vfs_syscalls.c` — `sys_chdir` / `chdir_internal`  
3. `vfs_syscalls.c` — `sys_fchdir` / `fchdir` 开头（VDIR + 换 `fd_cdir`）  
4. （可选）`fcntl.h` 的 `F_GETPATH` + `kern_descrip.c` 对应 case  

验收：能回答「cwd 存的是 vnode；getcwd 字符串从哪一类机制来，而不是 chdir 的返回值」。
