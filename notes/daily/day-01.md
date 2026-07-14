# Day 01 — getpid / getppid / getuid

> **第一天正文（带源码指引）：** [docs/day-01.md](../../docs/day-01.md)  
> 源码树：`xnu/`（xnu-12377.121.6）

下面是自学填写区；也可直接对照正文抄结论。

## getpid (#20)
- master 行：`20 AUE_GETPID ... { int getpid(void); }`
- handler 文件/函数：`xnu/bsd/kern/kern_prot.c` → `getpid()`
- 调用链（5 步以内）：stub → 陷阱 → sysent[20] → `getpid` → `*retval = proc_getpid(p)`
- 关键对象 / 锁 / copyin：`proc_t p`；无 copyin
- 一句话结论：返回当前进程 PID，成功返回 0

## getppid (#39)
- master 行：`39 AUE_GETPPID ... { int getppid(void); }`
- handler 文件/函数：`xnu/bsd/kern/kern_prot.c` → `getppid()`
- 调用链（5 步以内）：stub → 陷阱 → sysent[39] → `getppid` → `*retval = p->p_ppid`
- 关键对象 / 锁 / copyin：读 `proc.p_ppid`；无 copyin
- 一句话结论：父 PID 是当前 proc 上的字段

## getuid (#24)
- master 行：`24 AUE_GETUID ... { int getuid(void); }`
- handler 文件/函数：`xnu/bsd/kern/kern_prot.c` → `getuid()`
- 调用链（5 步以内）：stub → 陷阱 → sysent[24] → `getuid` → `*retval = kauth_getruid()`
- 关键对象 / 锁 / copyin：kauth 凭证；无 copyin
- 一句话结论：返回 real uid，不直接读 proc 字段

## 今日对比
- 三者共同点：无用户参数、只读、`return 0`、结果在 `*retval`
- 最大差异：PID 来自 `proc`；UID 来自 kauth 凭证
