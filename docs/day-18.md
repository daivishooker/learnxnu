# 第十八天（Day 18）正文

学这两个：**`sigaltstack` / `__pthread_kill`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 17：已经会装处理、改屏蔽、看未决。  
今天补两块更具体的能力：**信号换一套栈跑**，以及**对准某一个线程发信号**。

---

## 今天目标

1. 找到编号 **53 / 328**  
2. 理解 `sigaltstack`：给当前线程登记“备用信号栈”  
3. 理解 `__pthread_kill`：按线程 Mach port 定向投递信号  
4. 能对比 `kill(进程)` vs `__pthread_kill(线程)`

笔记：[`notes/daily/day-18.md`](../notes/daily/day-18.md)  
分析：[`notes/daily/day-18-analysis.md`](../notes/daily/day-18-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sigaltstack | **53** | 设置/查询备用信号栈 |
| __pthread_kill | **328** | 向指定线程发信号 |

---

## 1. sigaltstack（#53）——换地方跑 handler

平常信号来了，handler 往往还在**当前线程自己的栈**上跑。  
但有时这很危险：比如栈快溢出了，再在同一栈上跑 handler，可能再炸一次。

所以可以事先准备一块**另一块内存当信号栈**：

```text
普通栈：日常函数调用
备用信号栈：某些信号的 handler 改到这里跑（需配合 SA_ONSTACK）
```

[`kern_sig.c`](../xnu/bsd/kern/kern_sig.c)：

```c
sigaltstack(nss, oss) {
    uth = current_uthread()
    if (oss) copyout 当前 uu_sigstk
    if (nss) {
        copyin 新栈描述（基址、大小、flags）
        校验大小等
        uth->uu_sigstk = ss
        标记 UT_ALTSTACK
    }
}
```

生活类比：  
平时在书桌写作业（普通栈）；门铃响了，你走到门口玄关处理（备用栈），书桌再乱也不影响开门。

要点：

- 记在**当前线程**的 `uu_sigstk`  
- 要真正用上，装 handler 时还得带 **`SA_ONSTACK`**（Day 17 `sigaction` 的 flags）  
- `SA_DISABLE` 可关掉备用栈  

---

## 2. __pthread_kill（#328）——对准一个线程敲

Day 13 的 `kill`：对着**整个进程**敲门。  
多线程时，信号常由进程里某个合适的线程去接。

`__pthread_kill` 更狠、更准：指定**哪一个线程**收这个信号。

```c
__pthread_kill(thread_port, sig) {
    target = port_name_to_thread(thread_port)  // Mach 线程口 → thread
    if (!target) → ESRCH
    psignal_uthread(target, sig)              // 投到该线程
}
```

对照：

| | `kill` | `__pthread_kill` |
|--|--------|------------------|
| 目标 | 进程（pid） | **线程**（Mach thread port） |
| 投递 | `psignal(进程, …)` | `psignal_uthread(线程, …)` |
| 用户库 | `kill(2)` | 常被 `pthread_kill(3)` 包装 |

生活类比：  
`kill` = 朝一栋楼喊；`__pthread_kill` = 敲某一户的门。

（workqueue 等特殊线程可能不允许杀，今天知道有限制即可。）

---

## 今日对比

| | sigaltstack | __pthread_kill |
|--|-------------|----------------|
| 干什么 | 配置“handler 用哪块栈” | 向指定线程投递信号 |
| 和 Day 17 | 配合 `SA_ONSTACK` | 配合已装好的 `sigaction` |
| 和 Day 13 | — | 比 `kill` 更细的投递目标 |

---

## 用户层 Demo

`sigaltstack` 备好备用栈；同进程内用 `pthread_kill` 给当前线程发信号（用户层入口，内核侧对应 `__pthread_kill`）。

```c
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static void on_usr1(int sig) { (void)sig; write(STDOUT_FILENO, "alt\n", 4); }

int main(void) {
    stack_t ss = {0};
    ss.ss_sp = malloc(SIGSTKSZ);
    ss.ss_size = SIGSTKSZ;
    if (sigaltstack(&ss, NULL) != 0) { perror("sigaltstack"); return 1; }

    struct sigaction sa = {0};
    sa.sa_handler = on_usr1;
    sa.sa_flags = SA_ONSTACK;
    sigaction(SIGUSR1, &sa, NULL);
    pthread_kill(pthread_self(), SIGUSR1);
    free(ss.ss_sp);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 53 / 328  
- [ ] 能说备用栈解决什么问题（如栈溢出时跑 handler）  
- [ ] 能说 pthread_kill 对准线程，kill 对准进程  
- [ ] 填好 `notes/daily/day-18.md`

下一步：Day 19 → [`select` / `poll` / `kevent`](day-19.md)
