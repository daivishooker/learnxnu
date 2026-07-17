# 第六十六天（Day 66）正文

学这六个：**`thread_selfid` / `thread_selfusage` / `ledger` / `csrctl` / `ulock_wait` / `ulock_wake`**  
源码：`xnu/` = **xnu-12377.121.6**

从今天起正文**标明 BSD / Mach**：

| 标签 | 含义 |
|------|------|
| **BSD** | 走 `syscalls.master` → `sysent[]`（今天六个都是） |
| **Mach** | 走 Mach trap 表（`mach_trap_table`），不是本表编号 |
| **BSD→Mach** | BSD 入口，内部立刻用 `task`/`thread` 等 Mach 对象 |

> 注意：在 `syscalls.master` 里出现的都是 **BSD syscall**。下面「落到 Mach」指实现依赖 osfmk，不是说它变成 Mach trap。

---

## 今天目标

1. 找到编号 **372 / 482 / 373 / 483 / 515 / 516**  
2. 能标出每个调用的 BSD / BSD→Mach  
3. 理解 `ulock_*`：用户态锁（如 os_unfair_lock）的内核等待/唤醒  
4. 理解 `ledger`：查 task 资源账本  

笔记：[`notes/daily/day-66.md`](../notes/daily/day-66.md)  
分析：[`notes/daily/day-66-analysis.md`](../notes/daily/day-66-analysis.md)

---

## 总表

| 名字 | # | 入口层 | 实现落点 | 作用 |
|------|---|--------|----------|------|
| thread_selfid | **372** | BSD | **BSD→Mach**（经 pthread shim → thread） | 当前线程 ID |
| thread_selfusage | **482** | BSD | **BSD→Mach**（`thread_get_runtime_self`） | 当前线程 CPU 用量 |
| ledger | **373** | BSD | **BSD→Mach**（`task` ledger） | 读进程/任务资源账本 |
| csrctl | **483** | BSD | **BSD**（`kern_csr.c`） | SIP/CSR 配置查询与检查 |
| ulock_wait | **515** | BSD | **BSD→Mach**（thread wait / turnstile） | 用户锁等待 |
| ulock_wake | **516** | BSD | **BSD→Mach** | 用户锁唤醒 |

---

## 1. thread_selfid（#372）— BSD→Mach

[`pthread_shims.c`](../xnu/bsd/pthread/pthread_shims.c)：

```c
thread_selfid(...) {
    return pthread_functions->thread_selfid(p, retval);
}
```

BSD 入口，经 pthread 内核接口落到当前 **Mach thread** 的稳定 ID。用户少直接调，多经 libpthread。

---

## 2. thread_selfusage（#482）— BSD→Mach

[`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：

```c
thread_selfusage(...) {
    *retval = thread_get_runtime_self();  // Mach thread 运行时间
}
```

返回当前线程累计运行时间一类用量（纳秒量级，视实现）。

---

## 3. ledger（#373）— BSD→Mach

[`sys_generic.c`](../xnu/bsd/kern/sys_generic.c)：

```c
ledger(cmd, arg1, arg2, arg3) {
    proc_find(pid) → task = proc_task(proc)
    // 可选 MAC：mac_proc_check_ledger
    switch (cmd) {
      LEDGER_INFO / ENTRY_INFO / TEMPLATE_INFO →
        ledger_info / ledger_get_task_entry_info_multiple ...
    }
}
```

**Ledger** = task 上的资源账本（内存、CPU 等条目）。BSD 包一层，数据在 Mach `task` 侧。

---

## 4. csrctl（#483）— BSD

[`kern_csr.c`](../xnu/bsd/kern/kern_csr.c)：

```c
csrctl(op, ...) {
    CSR_SYSCALL_CHECK → 检查某 CSR 能力是否允许
    CSR_SYSCALL_GET_ACTIVE_CONFIG → 读当前 SIP/CSR 配置
}
```

纯平台/BSD 路径，问 **System Integrity Protection** 相关配置；与 Mach IPC 无直接关系。

---

## 5. ulock_wait / ulock_wake（#515 / #516）— BSD→Mach

[`sys_ulock.c`](../xnu/bsd/kern/sys_ulock.c)：

```c
sys_ulock_wait → sys_ulock_wait2
  按 opcode：UL_UNFAIR_LOCK / UL_COMPARE_AND_WAIT …
  用户地址上的值不匹配则睡眠等待（可绑定 owner thread）

sys_ulock_wake → ulock_wake(task, ...)
  唤醒等在同一用户锁地址上的线程
```

支撑 **os_unfair_lock** 等用户态锁：快路径在用户态 CAS，争用时进内核 wait/wake。内部用 Mach `thread`/`task` 与等待队列。

---

## 用户层 Demo

> 多为 Darwin SPI。Demo 在非 Apple 上 skip；Apple 上可试 `thread_selfid`（若 SDK 暴露）。

```c
#include <stdio.h>
#include <unistd.h>

#if defined(__APPLE__)
#include <pthread.h>
/* thread_selfid 为私有 syscall；用 pthread 线程 id 示意「线程身份」 */
#endif

int main(void) {
#if defined(__APPLE__)
    uint64_t tid = 0;
    (void)pthread_threadid_np(NULL, &tid);
    printf("pthread_threadid_np=%llu (userspace view; kernel has thread_selfid)\n",
           (unsigned long long)tid);
#else
    printf("day66: Darwin BSD syscalls (thread_selfid/ledger/csrctl/ulock) — skip\n");
#endif
    printf("day66 ok\n");
    printf("label note: all six are BSD sysent entries; "
           "most drop into Mach task/thread except csrctl\n");
    return 0;
}
```

```bash
cc -o day66_demo day66_demo.c && ./day66_demo
```

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能标 BSD vs BSD→Mach（无纯 Mach trap）  
- [ ] 能说 ulock 服务用户态锁争用  
- [ ] 能说 ledger 是 task 账本  
- [ ] 填好 `notes/daily/day-66.md`

下一步：Day 67 → `psynch_mutexwait` / `psynch_mutexdrop` / `psynch_cvwait` / `psynch_cvsignal` / `psynch_cvbroad`（BSD→Mach，pthread 同步）
