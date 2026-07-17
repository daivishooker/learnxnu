# 第七十一天（Day 71）正文

学这五个：**`__semwait_signal` / `iopolicysys` / `process_policy` / `sys_settid` / `gettid`**  
源码：`xnu/` = **xnu-12377.121.6**

**归属：**

| 调用 | 标签 | 落点 |
|------|------|------|
| __semwait_signal | **BSD→Mach** | [`kern_sig.c`](../xnu/bsd/kern/kern_sig.c) → Mach `semaphore_*wait*` trap |
| iopolicysys | **BSD** | [`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：进程/线程 I/O 与 VFS 策略 |
| process_policy | **BSD→Mach** | [`process_policy.c`](../xnu/bsd/kern/process_policy.c)：进程/线程调度与资源策略（常牵涉 task/thread） |
| sys_settid | **BSD** | [`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)：设**当前线程**覆盖身份（uid/gid） |
| gettid | **BSD** | 同上：读当前线程覆盖身份 |

> **易混警告：** Darwin 的 `gettid` / `settid` **不是** Linux 的「线程 ID」。  
> 线程数字 ID 看 Day 66 `thread_selfid`。今天这对是 **per-thread credential override**（线程级假身份）。

---

## 今天目标

1. 找到编号 **334 / 322 / 323 / 285 / 286**  
2. 能标上表五条标签  
3. 能说 `__semwait_signal` ≈ 用户态 POSIX 同步对 Mach 信号量的封装等待  
4. **绝不**把 Darwin `gettid` 当成 Linux tid  

笔记：[`notes/daily/day-71.md`](../notes/daily/day-71.md)  
分析：[`notes/daily/day-71-analysis.md`](../notes/daily/day-71-analysis.md)

---

## 总表

| 名字 | # | 标签 | 作用 |
|------|---|------|------|
| __semwait_signal | **334** | BSD→Mach | 等 Mach 信号量（可带另一信号量 signal；可超时；可取消点） |
| iopolicysys | **322** | BSD | 设/查 I/O 策略（磁盘优先级、若干 VFS 行为等） |
| process_policy | **323** | BSD→Mach | 设/查进程或线程策略（资源、boost、生命周期等） |
| sys_settid | **285** | BSD | 当前线程假设/撤销覆盖 uid+gid（需特权） |
| gettid | **286** | BSD | 读出当前线程覆盖身份；无覆盖则 `ESRCH` |

旁注：`__semwait_signal_nocancel`(#423) 是无取消点版本；`sys_settid_with_pid`(#311) 用别的进程身份来 assume——Day 72 可接。

---

## 1. __semwait_signal（#334）— BSD→Mach

```text
__semwait_signal
  → __pthread_testcancel（可取消点）
  → __semwait_signal_nocancel
       → semaphore_wait / semaphore_timedwait
         或 semaphore_wait_signal / timedwait_signal（Mach）
```

参数直觉：

- `cond_sem`：要等待的 Mach 信号量 port  
- `mutex_sem`：可选；非 0 时走 wait+signal 组合（放下/叫醒另一把）  
- `timeout` / `relative` / `tv_sec` / `tv_nsec`：要不要超时  

用户层旧路径里，部分 pthread 同步会落到 Mach 信号量 + 这个包装；今天主路径更多是 psynch/ulock，但这条仍在表上。

---

## 2. iopolicysys（#322）— BSD

`cmd` + 用户态参数块（type / scope / policy）。  
典型：`IOPOL_TYPE_DISK` 把当前进程或线程的磁盘 I/O 标成 normal / throttle / important 等。

用户层常经 `setiopolicy_np` 一类包装，不直接裸调。

---

## 3. process_policy（#323）— BSD→Mach

比 I/O 策略更宽：按 `scope`（进程或线程）+ `policy` + `action` 改目标进程/线程的调度与资源行为。

权限：多数情况只能弄自己，或需要特权；部分策略另有 MAC 检查。

---

## 4. sys_settid / gettid（#285 / #286）— BSD

**线程级凭证覆盖**，不是线程号：

```text
默认：线程用进程凭证（tro_realcred == tro_cred）

sys_settid(uid, gid)   // 特权
  → 当前线程换上覆盖凭证（只影响该线程）

gettid(&uid, &gid)
  → 有覆盖：写出覆盖的 ruid/rgid
  → 无覆盖：ESRCH

sys_settid(KAUTH_UID_NONE, …)
  → 撤销覆盖，回到进程凭证
```

和 Day 60 `setuid` 对比：

| | `setuid` 族 | `settid` |
|--|-------------|----------|
| 作用域 | 通常进程凭证 | **当前线程**覆盖 |
| 典型用途 | 改进程身份 | 单线程临时装另一身份办事 |

---

## 用户层 Demo

> 私有 syscall 不便裸调。Demo 只演示「进程凭证可读」；并打印 Darwin `gettid` 语义警告（在 Linux 上也能编译跑）。

```c
#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("process ruid=%d rgid=%d\n", (int)getuid(), (int)getgid());
    printf("note: Darwin gettid/settid = per-thread credential override\n");
    printf("note: NOT Linux gettid() thread id (see Day 66 thread_selfid)\n");
    printf("note: __semwait_signal = BSD wrapper over Mach semaphores\n");
    printf("note: iopolicysys / process_policy = I/O and sched/resource policy\n");
    printf("day71 ok\n");
    return 0;
}
```

```bash
cc -o day71_demo day71_demo.c && ./day71_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能标五条归属  
- [ ] 能说 semwait → Mach semaphore  
- [ ] 能说 Darwin gettid ≠ Linux tid  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-71.md`

下一步：Day 72 → `sys_settid_with_pid` / `shared_region_check_np` / `vm_pressure_monitor` / `getauid` / `setauid`
