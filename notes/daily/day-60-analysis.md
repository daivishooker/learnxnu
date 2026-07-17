# 源码分析：Day 60（凭证变更）

基于 `xnu-12377.121.6`。[`kern_prot.c`](../../xnu/bsd/kern/kern_prot.c)

---

## 1. 心智模型

```text
real / effective / saved  (uid 与 gid 各一套)

seteuid/setegid: 只动 effective
setuid/setgid:   非特权≈改 e*；特权可改齐 r/e/s
setreuid/setregid: 分别指定 r 与 e（-1=不动）

全部 → kauth_cred_proc_update(..., PROC_SETTOKEN_SETUGID, ...)
```

---

## 2. 权限直觉

- root（`suser` 过）：几乎可设任意  
- 普通进程：目标必须是当前已持有的 ruid/euid/svuid（或 gid 对应项）之一  
- 乱升权 → `EPERM`

---

## 3. 建议点开

1. `syscalls.master` — 23 / 181 / 183 / 182 / 126 / 127  
2. `kern_prot.c` — 六个 handler + 注释里的规则  
3. 对照 Day 1–3 的 get* / `issetugid`

验收：能讲清三角身份与 seteuid 丢特权模式；Demo 能跑。
