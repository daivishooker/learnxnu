# 源码分析：Day 67（psynch mutex/cond）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
BSD sysent: psynch_*
  → pthread_shims.c
  → pthread_functions->psynch_*   (pthread.kext 注册)
  → Mach thread 睡眠/唤醒
```

---

## 2. 编号

| # | 名字 |
|---|------|
| 301 | psynch_mutexwait |
| 302 | psynch_mutexdrop |
| 303 | psynch_cvbroad |
| 304 | psynch_cvsignal |
| 305 | psynch_cvwait |

---

## 3. 建议点开

1. `syscalls.master` — 301–305  
2. `pthread_shims.c` — 转发  
3. `pthread_shims.h` — `pthread_functions_s` / `pthread_kext_register`  
4. 对照 Day 66 `ulock_*`

验收：能说 shim 表 + 与 ulock 分工。
