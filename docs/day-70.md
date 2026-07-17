# 第七十天（Day 70）正文

学这五个：**`bsdthread_register` / `bsdthread_ctl` / `__disable_threadsignal` / `__pthread_markcancel` / `__pthread_canceled`**  
源码：`xnu/` = **xnu-12377.121.6**

**归属（要分开标）：**

| 调用 | 标签 | 落点 |
|------|------|------|
| bsdthread_register | **BSD→Mach** | `pthread_shims.c` → `pthread_functions->bsdthread_register[2]`（pthread.kext） |
| bsdthread_ctl | **BSD→Mach** | **不在 kext 表里**；XNU [`pthread_workqueue.c`](../xnu/bsd/pthread/pthread_workqueue.c) 直接实现（QoS / workq 控制） |
| __disable_threadsignal | **BSD** | [`kern_sig.c`](../xnu/bsd/kern/kern_sig.c)：给当前 `uthread` 打标志 |
| __pthread_markcancel | **BSD→Mach** | `kern_sig.c`：标取消 + 可能 `thread_abort_safely` |
| __pthread_canceled | **BSD** | `kern_sig.c`：查/改当前线程取消状态 |

对照 Day 69：`create`/`terminate` 是造线程、收线程；今天是 **进程级 pthread 注册、QoS 控制、取消协作**。

---

## 今天目标

1. 找到编号 **366 / 478 / 331 / 332 / 333**  
2. 能分开标：register→kext；ctl→XNU workq；取消三件套→`kern_sig.c`  
3. 知道 `pthread_cancel` 用户层背后会走到 markcancel / canceled  
4. 对照 Day 18：`__pthread_kill` 是信号；今天是 **取消（cancel）**，不是同一条路  

笔记：[`notes/daily/day-70.md`](../notes/daily/day-70.md)  
分析：[`notes/daily/day-70-analysis.md`](../notes/daily/day-70-analysis.md)

---

## 总表

| 名字 | # | 标签 | 作用 |
|------|---|------|------|
| bsdthread_register | **366** | BSD→Mach | 进程启动时向内核登记 pthread 入口/workq 回调/TSD 等 |
| bsdthread_ctl | **478** | BSD→Mach | 杂项控制：QoS override、set_self、workq 信号许可等 |
| __disable_threadsignal | **331** | BSD | 当前线程不再收信号，并禁用取消 |
| __pthread_markcancel | **332** | BSD→Mach | 给目标线程打「请取消」标记（可 abort 等待点） |
| __pthread_canceled | **333** | BSD | 当前线程：查询/启用/禁用取消处理，或确认已取消 |

---

## 1. bsdthread_register（#366）

进程里 libpthread 初始化时调用一次（不是每个 `pthread_create` 都调）。

登记内容直觉上包括：

- 新线程从哪段用户代码起步（`threadstart`）  
- workqueue 线程入口（`wqthread`）  
- 栈提示、dispatch queue 偏移、TSD 偏移等  

```c
bsdthread_register(...) {
    /* 把用户指针转成内核可信形式 */
    if (pthread_functions->version >= 1)
        return pthread_functions->bsdthread_register2(...);
    else
        return pthread_functions->bsdthread_register(...);
}
```

一句话：**先 register 告诉内核「pthread 怎么跑」，再 create 真正造线程。**

---

## 2. bsdthread_ctl（#478）

`cmd + arg1/2/3` 的多路开关，实现在 XNU `bsdthread_ctl()`，**不走** `pthread_functions`（表项已是 `__unused_was_bsdthread_ctl`）。

常见用途（见 [`bsdthread_private.h`](../xnu/bsd/pthread/bsdthread_private.h)）：

- QoS 临时抬升 / 撤销（override）  
- `SET_SELF`：调自己的优先级 / voucher  
- workq 是否允许 kill / 信号掩码等  

用户层多由 libpthread / libdispatch 内部调用，不是日常手写 API。

---

## 3. 取消三件套（#331 / #332 / #333）

POSIX `pthread_cancel` 不是「立刻杀线程」，而是：

```text
A 调 pthread_cancel(B)
  → 内核 __pthread_markcancel(B 的 thread port)
  → B.uu_flag |= UT_CANCEL
  → 若 B 在可取消点，可 thread_abort_safely 打断等待

B 跑到取消点 / 用户态检查
  → __pthread_canceled(action=0) 等
  → 确认后进入取消清理，最终线程退出
```

| 调用 | 谁调用 | 干什么 |
|------|--------|--------|
| `__pthread_markcancel` | 取消方（对目标 port） | 打 `UT_CANCEL`，必要时 abort |
| `__pthread_canceled` | 当前线程自己 | action=1/2 开/关取消；action=0 确认并标 `UT_CANCELED` |
| `__disable_threadsignal` | 当前线程 | `UT_NO_SIGMASK \| UT_CANCELDISABLE`：别再投信号、也别取消 |

和 Day 18 `__pthread_kill` 对比：

| | `__pthread_kill` | `__pthread_markcancel` |
|--|------------------|------------------------|
| 语义 | 投递**信号** | 请求 **pthread 取消** |
| 用户 API | `pthread_kill` | `pthread_cancel` |
| 结果 | 跑 signal handler（若未屏蔽） | 在取消点退出并跑 cleanup |

---

## 用户层 Demo

> 不直接调私有 syscall。用 `pthread_cancel` + 可取消的 `pthread_cond_wait` 演示取消协作。

```c
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  c = PTHREAD_COND_INITIALIZER;

static void *worker(void *arg) {
    (void)arg;
    pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
    pthread_setcanceltype(PTHREAD_CANCEL_DEFERRED, NULL);

    pthread_mutex_lock(&m);
    /* cond_wait 是经典取消点；Darwin 上取消可走到 markcancel/canceled */
    pthread_cond_wait(&c, &m);
    pthread_mutex_unlock(&m);
    printf("should not reach here\n");
    return NULL;
}

int main(void) {
    pthread_t t;
    void *ret = NULL;

    if (pthread_create(&t, NULL, worker, NULL) != 0) {
        perror("pthread_create");
        return 1;
    }
    usleep(100 * 1000); /* 让 worker 进入 wait */
    if (pthread_cancel(t) != 0) {
        perror("pthread_cancel");
        return 1;
    }
    if (pthread_join(t, &ret) != 0) {
        perror("pthread_join");
        return 1;
    }

    if (ret == PTHREAD_CANCELED) {
        printf("worker canceled ok\n");
    } else {
        printf("unexpected join status\n");
        return 1;
    }
    printf("label: markcancel/canceled are Darwin kernel cancel path\n");
    printf("day70 ok\n");
    return 0;
}
```

```bash
cc -o day70_demo day70_demo.c -lpthread && ./day70_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能分开标 register / ctl / 取消三件套的落点  
- [ ] 能说 cancel ≠ kill  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-70.md`

下一步：Day 71 → `__semwait_signal` / `iopolicysys` / `process_policy` / `sys_settid` / `gettid`
