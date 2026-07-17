# 源码分析：Day 62（进程组与会话）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
session
  └── pgrp (pgid)
        └── proc (pid, p_pgrpid, p_sessionid)

getpgrp/getpgid/getsid → 读字段
setpgid → enterpgrp(mksess=0)
setsid  → enterpgrp(mksess=1) 新建 session+pgrp
```

---

## 2. 建议点开

1. `syscalls.master` — 81 / 82 / 147 / 151 / 310  
2. `kern_prot.c` — 五个 handler + `setsid_internal`  
3. `kern_proc.c` — `enterpgrp`  
4. 对照 Day 11 `fork`、Day 13 `kill`、Day 61 `getlogin`

验收：能画 session/pgrp/pid；Demo 能跑。
