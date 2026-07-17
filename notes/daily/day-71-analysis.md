# 源码分析：Day 71（semwait / policy / tid）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
__semwait_signal → testcancel → Mach semaphore_*wait*
iopolicysys      → kern_resource.c（disk / vfs 策略分支）
process_policy   → process_policy.c（scope/action/policy）
sys_settid/gettid → kern_prot.c（thread_ro 上的凭证覆盖）
```

---

## 2. 编号

| # | 名字 |
|---|------|
| 334 | __semwait_signal |
| 322 | iopolicysys |
| 323 | process_policy |
| 285 | sys_settid |
| 286 | gettid |

---

## 3. 建议点开

1. `syscalls.master` — 285 / 286 / 322 / 323 / 334  
2. `kern_sig.c` — `__semwait_signal_nocancel`  
3. `kern_prot.c` — `gettid` / `kern_settid`（读注释：override identity）  
4. 对照 Day 60 setuid、Day 66 thread_selfid  

验收：能说 Mach 信号量包装 + Darwin tid 语义陷阱。
