# 源码分析：Day 68（psynch rwlock）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
BSD sysent: psynch_rw_rdlock / wrlock / unlock
  → pthread_shims.c
  → pthread_functions->psynch_rw_*   (pthread.kext)
  → Mach thread 睡眠/唤醒（turnstile 回调）

BSD sysent: psynch_rw_upgrade / downgrade
  → pthread_shims.c 直接 return 0（不进 kext）
```

---

## 2. 编号

| # | 名字 | 备注 |
|---|------|------|
| 306 | psynch_rw_rdlock | 转发 kext |
| 307 | psynch_rw_wrlock | 转发 kext |
| 308 | psynch_rw_unlock | 转发 kext |
| 300 | psynch_rw_upgrade | stub |
| 299 | psynch_rw_downgrade | stub |

旁支：297 `longrdlock`、298 `yieldwrlock`、309 `unlock2`→`ENOTSUP`。

---

## 3. 建议点开

1. `syscalls.master` — 299 / 300 / 306–308  
2. `pthread_shims.c` — `psynch_rw_*`（对比 stub vs 转发）  
3. `pthread_shims.h` — `pthread_functions_s` 里有 rd/wr/unlock，无 upgrade/downgrade 指针  
4. 对照 Day 67 mutex/cond

验收：能说读写锁语义 + stub 事实 + 与 mutex 同属 psynch 地址模型。
