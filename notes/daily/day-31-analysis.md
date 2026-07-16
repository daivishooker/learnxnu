# 源码分析：Day 31（getpriority / setpriority）

基于 `xnu-12377.121.6`。nice 优先级查询与设置。

---

## 1. 心智模型

```text
proc.p_nice  ←→  getpriority / setpriority（PRIO_PROCESS）
set 时：donice 校验权限 → 写 p_nice → resetpriority（调度）
```

Darwin 另有 `PRIO_DARWIN_*`（BG、role 等），接 task policy；今天以经典 nice 为主。

---

## 2. getpriority

[`kern_resource.c`](../../xnu/bsd/kern/kern_resource.c)：

```
PRIO_PROCESS: p_nice
PRIO_PGRP: 组内最小 p_nice
PRIO_USER: 同 uid 最小 p_nice
无目标: ESRCH
*retval = low
```

---

## 3. setpriority → donice

```
donice(curp, chgp, n)
  属主/特权检查 → EPERM
  n 夹紧 PRIO_MIN..MAX
  n < 当前 nice 且非 root → EACCES
  MAC mac_proc_check_sched
  chgp->p_nice = n
  resetpriority(chgp)
```

---

## 4. 建议点开

1. `syscalls.master` — 100 / 96  
2. `kern_resource.c` — `getpriority` / `setpriority` / `donice`  

验收：能说 p_nice 是经典锚点；能说提高优先级的权限门槛。
