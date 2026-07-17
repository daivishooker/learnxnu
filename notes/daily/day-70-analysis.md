# 源码分析：Day 70（register / ctl / cancel）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
bsdthread_register → pthread_shims → pthread_functions (kext)

bsdthread_ctl → pthread_workqueue.c::bsdthread_ctl (XNU 本地 switch)

__disable_threadsignal / __pthread_markcancel / __pthread_canceled
  → kern_sig.c（uthread 标志；markcancel 可 abort 目标线程）
```

---

## 2. 编号

| # | 名字 |
|---|------|
| 366 | bsdthread_register |
| 478 | bsdthread_ctl |
| 331 | __disable_threadsignal |
| 332 | __pthread_markcancel |
| 333 | __pthread_canceled |

---

## 3. 建议点开

1. `syscalls.master` — 331–333 / 366 / 478  
2. `pthread_shims.c` — `bsdthread_register`  
3. `pthread_workqueue.c` — `bsdthread_ctl`  
4. `kern_sig.c` — 取消三件套  
5. 对照 Day 18 `__pthread_kill`、Day 69 `bsdthread_create`

验收：能说三条落点不同 + cancel vs kill。
