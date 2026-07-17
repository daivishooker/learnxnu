# 第六十五天（Day 65）正文

学这五个：**`proc_info` / `csops` / `csops_audittoken` / `workq_open` / `workq_kernreturn`**  
源码：`xnu/` = **xnu-12377.121.6**

Darwin 味很浓的一天：查进程信息的「总闸」、代码签名操作、以及 libpthread 的内核 workqueue。

生活类比：

1. `proc_info`：一张多功能服务台——列进程、查某个 pid 详情、看 FD……靠 callnum 分流  
2. `csops`：查/改进程的代码签名状态（是否有效、entitlements 等）  
3. `csops_audittoken`：同上，但用 audit token 对齐目标身份，防 pid 复用  
4. `workq_open` / `workq_kernreturn`：给 GCD/libpthread 开工人池、要线程、回内核汇报  

---

## 今天目标

1. 找到编号 **336 / 169 / 170 / 367 / 368**  
2. 理解 `proc_info`：`callnum` switch → 各子命令  
3. 理解 `csops*`：`csops_internal`；token 版防 PID reuse  
4. 理解 workq：进程注册后 `workq_open`，再 `workq_kernreturn` 做队列操作  

笔记：[`notes/daily/day-65.md`](../notes/daily/day-65.md)  
分析：[`notes/daily/day-65-analysis.md`](../notes/daily/day-65-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| proc_info | **336** | 进程信息总入口（多 callnum） |
| csops | **169** | 代码签名查询/操作 |
| csops_audittoken | **170** | 带 audit token 的 csops |
| workq_open | **367** | 初始化进程 workqueue |
| workq_kernreturn | **368** | workqueue 内核往返（要线程等） |

---

## 1. proc_info（#336）

[`proc_info.c`](../xnu/bsd/kern/proc_info.c)：

```c
proc_info(callnum, pid, flavor, arg, buffer, buffersize)
  = proc_info_internal(...)

switch (callnum) {
  PROC_INFO_CALL_LISTPIDS      → proc_listpids
  PROC_INFO_CALL_PIDINFO       → proc_pidinfo
  PROC_INFO_CALL_PIDFDINFO     → proc_pidfdinfo
  PROC_INFO_CALL_PIDRUSAGE     → proc_pid_rusage
  PROC_INFO_CALL_TERMINATE     → ...
  // 还有 dirtycontrol、coalition、dynkqueue 等
}
```

要点：

- libc/`libproc` 的 `proc_listpids`、`proc_pidinfo` 等常落到这里  
- 有安全策略（`proc_security_policy`），不是随便窥探  
- 扩展版：`proc_info_extended_id` #545（可带 unique id 比对）  

---

## 2. csops / csops_audittoken（#169 / #170）

[`kern_proc.c`](../xnu/bsd/kern/kern_proc.c)：

```c
csops(pid, ops, addr, size)
  = csops_internal(..., uaudittoken=NULL)

csops_audittoken(..., uaudittoken)
  = csops_internal(..., uaudittoken)  // token 不可为 NULL
```

常见 `ops`（只记类别）：

| 类 | 例子 |
|----|------|
| 查询 | `CS_OPS_STATUS`、`CDHASH`、`ENTITLEMENTS_BLOB`、`TEAMID` |
| 标记 | `MARKINVALID`、`MARKHARD`、`MARKKILL`（多限自身/特权） |

`CS_OPS_STATUS`：把进程 csflags（及 enforcement/platform 等）copyout。  
带 audittoken：确认目标仍是「那一个」进程实例，减轻 PID 复用竞态。

---

## 3. workq_open / workq_kernreturn（#367 / #368）

[`pthread_workqueue.c`](../xnu/bsd/pthread/pthread_workqueue.c)：

```c
workq_open() {
    进程须已 pthread 注册 (P_LREGISTER)
    若尚无 wq → 分配 workqueue、设默认 QoS/并行度
}

workq_kernreturn(options, item, affinity, prio) {
    switch (options) {
      WQOPS_QUEUE_REQTHREADS  → workq_reqthreads(...)
      WQOPS_QUEUE_REQTHREADS2 → 协作池要线程
      WQOPS_SET_EVENT_MANAGER_PRIORITY → ...
      // 还有回线程、kevent 相关等
    }
}
```

要点：用户一般不直接调；**libpthread / libdispatch** 用它们撑起线程池。须先完成 pthread 用户态注册。

---

## 用户层 Demo

> 这些几乎都是 Darwin SPI。Linux 上无对应 syscall；Demo 在非 Apple 平台打印说明并成功退出。

```c
#include <stdio.h>
#include <unistd.h>

#if defined(__APPLE__)
#include <sys/codesign.h>
/* csops 声明随 SDK；部分需私有头。此处仅示意 STATUS 查询自身。 */
extern int csops(pid_t pid, unsigned int ops, void *useraddr, size_t usersize);
#ifndef CS_OPS_STATUS
#define CS_OPS_STATUS 0
#endif
#endif

int main(void) {
#if defined(__APPLE__)
    uint32_t flags = 0;
    if (csops(getpid(), CS_OPS_STATUS, &flags, sizeof(flags)) != 0) {
        perror("csops STATUS");
        return 1;
    }
    printf("csops STATUS ok flags=0x%x\n", flags);
    printf("proc_info/workq: use libproc / libpthread (not shown)\n");
#else
    printf("day65: Darwin SPI (proc_info/csops/workq) — skip on this OS\n");
#endif
    printf("day65 ok\n");
    return 0;
}
```

```bash
cc -o day65_demo day65_demo.c && ./day65_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能说 proc_info 靠 callnum 分流  
- [ ] 能说 csops_audittoken 防 PID 复用  
- [ ] 能说 workq 服务 libpthread/GCD  
- [ ] 填好 `notes/daily/day-65.md`

下一步：Day 66 → [thread / ledger / csrctl / ulock](day-66.md)（起标注 BSD/Mach）
