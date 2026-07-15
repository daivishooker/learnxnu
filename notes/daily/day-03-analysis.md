# 源码分析：Day 3（issetugid / getdtablesize）

基于 `xnu-12377.121.6`。

---

## 1. issetugid：读进程「特权污染」标志

### handler

[`kern_prot.c`](../../xnu/bsd/kern/kern_prot.c)：

```c
*retval = (p->p_flag & P_SUGID) ? 1 : 0;
```

这是 Day 1–2 以来第一次：**返回值不是身份数字，而是布尔标志**（仍放在 `*retval`，errno 通道仍是 `return 0`）。

### `P_SUGID` 何时置位？

定义：`Has set privileges since last exec`。

常见来源（后续深挖入口）：

1. **exec 了 SUID/SGID 程序** — `kern_exec.c` 里对 SUGID 镜像会 `OSBitOrAtomic(P_SUGID, &p->p_flag)`，并先清再按需置。  
2. **运行中改身份** — 如 `setuid` 路径带 `PROC_SETTOKEN_SETUGID`，改凭证时顺带标污染。

注释强调 Darwin 与 OpenBSD 的细微差别：OpenBSD 偏重 exec 时的 `P_SUGIDEXEC`；XNU 的 `P_SUGID` **把「改过 owners」也算污染**。  
意义：进程若以 root 启动再 `setuid` 成普通用户、中间没 exec，libc 可能已往数据段写过「按 root 环境假设」的东西——程序需要知道自己不可再信任某些状态。

### 和 Day 2 的关系

Day 2 读的是 **此刻** uid/gid 字段；  
`issetugid` 问的是：**自上次 exec 以来，特权身份是否变动过**（历史/安全性问题）。

---

## 2. getdtablesize：FD 表容量上限

### handler

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c)：

```c
*retval = proc_limitgetcur_nofile(p);
```

[`kern_resource.c`](../../xnu/bsd/kern/kern_resource.c) 中该函数取 `RLIMIT_NOFILE` 的当前（软）限制，并受内核 `maxfilesperproc` 一类上限约束。

### 易混点

| 概念 | 是不是 getdtablesize？ |
|------|------------------------|
| 最多能 `open` 多少 FD | ✅ 是（软限制视角） |
| 现在已经打开几个 | ❌ 否 |
| FD 表在内存里的实际分配长度 | ❌ 不一定等于返回值（实现可懒扩展，但上限由此限制） |

Day 4 起学 `open`/`close` 时会反复碰到这个上限（分配 FD 前检查 `proc_limitgetcur_nofile`）。

### 命名

master 里是 `sys_getdtablesize`，避免与用户态符号裸撞名；syscall 编号仍是 89。

---

## 3. 两条链对照

```
issetugid:
  sysent[327] → issetugid → p->p_flag & P_SUGID → 0/1

getdtablesize:
  sysent[89] → sys_getdtablesize → proc_limitgetcur_nofile(p) → rlim
```

两者都：无用户参数、无 `copyin`、成功 `return 0`。  
差异：一个读 **标志位**，一个读 **资源限制对象**。

---

## 4. 建议点开的文件

1. `syscalls.master` — 89 / 327  
2. `kern_prot.c` — `issetugid` / `proc_issetugid`  
3. `sys/proc.h` — `P_SUGID`  
4. `kern_descrip.c` — `sys_getdtablesize`  
5. （可选）`kern_resource.c` — `proc_limitgetcur_nofile`  
6. （可选）`kern_exec.c` 搜 `P_SUGID` — 看 exec 时如何清/置  
