# 源码分析：Day 66（线程 / ledger / CSR / ulock）

基于 `xnu-12377.121.6`。

---

## 1. BSD vs Mach 标注约定

```text
BSD        = syscalls.master 入口 + 主要逻辑在 bsd/
BSD→Mach   = syscalls.master 入口，核心用 task/thread/vm（osfmk）
Mach trap  = mach_trap_table，不在本表（今天没有）
```

---

## 2. 入口文件

| 调用 | 文件 |
|------|------|
| thread_selfid | `bsd/pthread/pthread_shims.c` |
| thread_selfusage | `bsd/kern/kern_resource.c` → `thread_get_runtime_self`（osfmk） |
| ledger | `bsd/kern/sys_generic.c` → task ledger |
| csrctl | `bsd/kern/kern_csr.c` |
| ulock_* | `bsd/kern/sys_ulock.c` |

---

## 3. 验收

能给每个调用贴 BSD 或 BSD→Mach；理解 ulock 与 unfair lock 关系。
