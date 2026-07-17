# 源码分析：Day 65（proc_info / csops / workq）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
proc_info(callnum, ...) → switch → listpids / pidinfo / ...

csops / csops_audittoken → csops_internal(ops)
  STATUS → proc csflags copyout
  其它 → entitlements / cdhash / mark* ...

workq_open → 进程 workqueue 结构
workq_kernreturn(options) → reqthreads / 设优先级 / ...
```

---

## 2. 建议点开

1. `syscalls.master` — 336 / 169 / 170 / 367 / 368  
2. `proc_info.c` — `proc_info_internal`  
3. `kern_proc.c` — `csops_internal`  
4. `pthread_workqueue.c` — `workq_open` / `workq_kernreturn`

验收：能各说一句用途与入口；理解多为库封装。
