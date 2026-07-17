# 源码分析：Day 69（psynch 扫尾 + bsdthread）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
psynch_rw_longrdlock / yieldwrlock / cvclrprepost
  → pthread_shims → pthread_functions → pthread.kext

bsdthread_create
  → pthread_functions->bsdthread_create

bsdthread_terminate
  →（可选）workq_thread_terminate / 标记 USER_JOIN + ulock
  → pthread_functions->bsdthread_terminate
```

---

## 2. 编号

| # | 名字 |
|---|------|
| 297 | psynch_rw_longrdlock |
| 298 | psynch_rw_yieldwrlock |
| 312 | psynch_cvclrprepost |
| 360 | bsdthread_create |
| 361 | bsdthread_terminate |

---

## 3. 建议点开

1. `syscalls.master` — 297 / 298 / 312 / 360 / 361  
2. `pthread_shims.c` — `bsdthread_create` / `bsdthread_terminate`（含 ulock join 注释）  
3. 对照 Day 67–68 psynch、Day 65 workq、Day 66 ulock  

验收：能说 psynch 边角用途 + create/terminate 与 pthread API 的对应。
