# 第六十七天（Day 67）正文

学这五个：**`psynch_mutexwait` / `psynch_mutexdrop` / `psynch_cvwait` / `psynch_cvsignal` / `psynch_cvbroad`**  
源码：`xnu/` = **xnu-12377.121.6**

**归属：全部 BSD→Mach（经 pthread shim / pthread.kext）**  
- 入口：BSD `sysent`（`syscalls.master`）  
- 实现：`pthread_shims.c` 转到 `pthread_functions->…`（pthread 内核扩展注册的函数指针）  
- 底下睡眠/唤醒用 Mach `thread` 等原语  

对照 Day 66：`ulock_*` ≈ unfair lock 的 futex；今天的 `psynch_*` ≈ **pthread mutex / cond 的内核慢路径**。

---

## 今天目标

1. 找到编号 **301 / 302 / 305 / 304 / 303**  
2. 能标：**BSD→Mach**（shim → pthread.kext）  
3. 分清 mutex 等待/放下 vs cond wait/signal/broadcast  
4. 知道用户调的是 `pthread_mutex_*` / `pthread_cond_*`，不是直接 syscall  

笔记：[`notes/daily/day-67.md`](../notes/daily/day-67.md)  
分析：[`notes/daily/day-67-analysis.md`](../notes/daily/day-67-analysis.md)

---

## 总表

| 名字 | # | 标签 | 作用 |
|------|---|------|------|
| psynch_mutexwait | **301** | BSD→Mach | mutex 争用时内核等待 |
| psynch_mutexdrop | **302** | BSD→Mach | mutex 释放侧内核配合 |
| psynch_cvwait | **305** | BSD→Mach | cond 等待（可带超时） |
| psynch_cvsignal | **304** | BSD→Mach | cond 唤醒一个 |
| psynch_cvbroad | **303** | BSD→Mach | cond 广播唤醒 |

---

## 1. 公共入口形态

[`pthread_shims.c`](../xnu/bsd/pthread/pthread_shims.c)：

```c
psynch_mutexwait(...) {
    return pthread_functions->psynch_mutexwait(p, mutex, mgen, ugen, tid, flags, retval);
}
// mutexdrop / cvwait / cvsignal / cvbroad 同理：一律函数指针转发
```

`pthread_kext_register()` 在加载时填好 `pthread_functions` 表——和 MAC「挂函数指针」类似，但是 **pthread 专用 shim**。

参数里的 `mgen` / `ugen` / `cvlsgen` 等是用户态与内核协商用的**代数/序列号**，用来发现锁状态在进内核前后是否已变（避免惊扰/虚假等待）。

---

## 2. Mutex：wait / drop

```text
用户态 pthread_mutex_lock
  快路径：用户态原子拿到锁 → 不进内核
  慢路径：psynch_mutexwait → 睡眠直到可持锁

用户态 pthread_mutex_unlock
  若有等待者 → psynch_mutexdrop 等配合唤醒
```

像 futex/ulock：无竞争不进内核；有竞争才 `wait`/`drop`。

---

## 3. Cond：wait / signal / broadcast

```text
pthread_cond_wait
  → 原子释放 mutex + psynch_cvwait（可 sec/nsec 超时）
  → 被唤醒后再重新争 mutex

pthread_cond_signal   → psynch_cvsignal（可指定 thread_port）
pthread_cond_broadcast → psynch_cvbroad
```

经典「条件变量 + 互斥锁」配对；内核侧保证 wait 与 mutex 放下的衔接。

---

## 4. 和 ulock 的分工（直觉）

| | ulock（Day 66） | psynch（今天） |
|--|-----------------|----------------|
| 典型用户 | `os_unfair_lock` | `pthread_mutex` / `pthread_cond` |
| 模型 | 地址 + 期望值 | 带 generation 的 pthread 同步对象 |
| 入口 | BSD `sys_ulock_*` | BSD `psynch_*` → pthread.kext |

---

## 用户层 Demo

> 不直接调 `psynch_*`（私有）。用可移植的 pthread mutex/cond 演示「会走到同步慢路径」的语义。

```c
#include <pthread.h>
#include <stdio.h>

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  c = PTHREAD_COND_INITIALIZER;
static int ready = 0;

static void *worker(void *arg) {
    (void)arg;
    pthread_mutex_lock(&m);
    ready = 1;
    pthread_cond_signal(&c);
    pthread_mutex_unlock(&m);
    return NULL;
}

int main(void) {
    pthread_t t;

    pthread_mutex_lock(&m);
    if (pthread_create(&t, NULL, worker, NULL) != 0) {
        perror("pthread_create");
        return 1;
    }
    while (!ready) {
        pthread_cond_wait(&c, &m); /* 争用/等待时 Darwin 可进 psynch_cvwait */
    }
    pthread_mutex_unlock(&m);

    pthread_join(t, NULL);
    printf("pthread mutex/cond ok (psynch_* is kernel slow-path on Darwin)\n");
    printf("label: BSD→Mach via pthread_shims → pthread.kext\n");
    printf("day67 ok\n");
    return 0;
}
```

```bash
cc -o day67_demo day67_demo.c -lpthread && ./day67_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能标 BSD→Mach（shim → pthread.kext）  
- [ ] 能说与 ulock 的分工  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-67.md`

下一步：**[Day 68](day-68.md)** → `psynch_rw_*` 读写锁族（BSD→Mach）
