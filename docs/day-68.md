# 第六十八天（Day 68）正文

学这五个：**`psynch_rw_rdlock` / `psynch_rw_wrlock` / `psynch_rw_unlock` / `psynch_rw_upgrade` / `psynch_rw_downgrade`**  
源码：`xnu/` = **xnu-12377.121.6**

**归属：全部挂在 BSD `sysent`；有效路径为 BSD→Mach（经 pthread shim / pthread.kext）**  
- 入口：BSD `syscalls.master`  
- `rdlock` / `wrlock` / `unlock`：`pthread_shims.c` → `pthread_functions->…` → pthread.kext  
- `upgrade` / `downgrade`：本树 shim **直接 stub 返回 0**（不转发 kext）  
- 睡眠/唤醒仍落 Mach `thread` / turnstile

对照 Day 67：mutex/cond 是「一把锁 / 条件变量」；今天是 **读写锁**（多读者或单写者）。

---

## 今天目标

1. 找到编号 **306 / 307 / 308 / 300 / 299**  
2. 能标：**BSD→Mach**（shim → pthread.kext；并知道 upgrade/downgrade 是 stub）  
3. 分清读锁 / 写锁 / 解锁；upgrade/downgrade 在本版本几乎是空壳  
4. 知道用户调的是 `pthread_rwlock_*`，不是直接 syscall  

笔记：[`notes/daily/day-68.md`](../notes/daily/day-68.md)  
分析：[`notes/daily/day-68-analysis.md`](../notes/daily/day-68-analysis.md)

---

## 总表

| 名字 | # | 标签 | 作用 |
|------|---|------|------|
| psynch_rw_rdlock | **306** | BSD→Mach | 读锁争用时内核等待 |
| psynch_rw_wrlock | **307** | BSD→Mach | 写锁争用时内核等待 |
| psynch_rw_unlock | **308** | BSD→Mach | 解锁并唤醒等待者 |
| psynch_rw_upgrade | **300** | BSD（stub） | 读→写升级；本树 shim 直接 `return 0` |
| psynch_rw_downgrade | **299** | BSD（stub） | 写→读降级；本树 shim 直接 `return 0` |

同族旁支（今天不深挖，Day 69 可扫）：`psynch_rw_longrdlock`(#297)、`psynch_rw_yieldwrlock`(#298)、`psynch_rw_unlock2`(#309，`ENOTSUP`)。

---

## 1. 公共入口形态

[`pthread_shims.c`](../xnu/bsd/pthread/pthread_shims.c)：

```c
psynch_rw_rdlock(...) {
    return pthread_functions->psynch_rw_rdlock(p, rwlock, lgenval, ugenval, rw_wc, flags, retval);
}
psynch_rw_wrlock(...) { /* 同上，转发 kext */ }
psynch_rw_unlock(...) { /* 同上，转发 kext */ }

psynch_rw_upgrade(...)   { return 0; }   /* stub */
psynch_rw_downgrade(...) { return 0; }   /* stub */
```

参数里的 `rwlock` 是**用户态** `pthread_rwlock_t` 地址；`lgenval` / `ugenval` / `rw_wc` 是代数与等待计数协商字段——和 Day 67 的 `mgen`/`ugen` 同一类角色。

心智模型与 mutex 相同：

> 权威状态在用户态对象里；内核按**地址**认同一把锁，争用时才建/查等待队列旁路。

---

## 2. 读写锁语义（用户层）

```text
pthread_rwlock_rdlock
  快路径：用户态拿到读锁（可与其他读者共存）→ 不进内核
  慢路径：有写者（或写者在等）→ psynch_rw_rdlock 睡眠

pthread_rwlock_wrlock
  快路径：无人占锁 → 用户态拿到写锁
  慢路径：有读者或写者 → psynch_rw_wrlock 睡眠

pthread_rwlock_unlock
  若有等待者 → psynch_rw_unlock 配合唤醒（读者批醒或写者一个，由协议决定）
```

直觉：

| | 读锁 | 写锁 |
|--|------|------|
| 同时持有 | 多个读者 OK | 独占 |
| 阻塞谁 | 写者要等读者清空 | 新读者/写者都要等 |

---

## 3. upgrade / downgrade 为什么是 stub？

POSIX 有「持读锁升级为写锁 / 写锁降为读锁」的讨论，但 Darwin 这条 syscall 槽位在当前 XNU shim 里**没有接到 `pthread_functions`**，函数体直接成功返回。

学习意义：

- 表项还在 `syscalls.master`（编号 300 / 299）  
- 真正常用的慢路径是 **rdlock / wrlock / unlock**  
- 用户态若需要「读完再独占写」，通常是 **unlock 读锁 → 再 wrlock**（中间窗口要自己保证正确性）

---

## 4. 和 Day 67 mutex 的对照

| | mutex（Day 67） | rwlock（今天） |
|--|-----------------|----------------|
| 用户对象 | `pthread_mutex_t` | `pthread_rwlock_t` |
| 慢路径 | `mutexwait` / `mutexdrop` | `rw_rdlock` / `rw_wrlock` / `rw_unlock` |
| 共享 | 否（独占） | 读共享、写独占 |
| 内核认什么 | 用户态地址 + 代数 | 同上 |

---

## 用户层 Demo

> 不直接调 `psynch_rw_*`（私有）。用 `pthread_rwlock_*` 演示读写锁语义。

```c
#include <pthread.h>
#include <stdio.h>

static pthread_rwlock_t rw = PTHREAD_RWLOCK_INITIALIZER;
static int value = 0;

static void *reader(void *arg) {
    (void)arg;
    pthread_rwlock_rdlock(&rw);
    printf("reader sees %d\n", value);
    pthread_rwlock_unlock(&rw);
    return NULL;
}

static void *writer(void *arg) {
    (void)arg;
    pthread_rwlock_wrlock(&rw);
    value = 42;
    pthread_rwlock_unlock(&rw);
    return NULL;
}

int main(void) {
    pthread_t r1, r2, w;

    /* 先写再读，避免演示里和写者竞态 */
    if (pthread_create(&w, NULL, writer, NULL) != 0) {
        perror("pthread_create writer");
        return 1;
    }
    pthread_join(w, NULL);

    if (pthread_create(&r1, NULL, reader, NULL) != 0 ||
        pthread_create(&r2, NULL, reader, NULL) != 0) {
        perror("pthread_create reader");
        return 1;
    }
    pthread_join(r1, NULL);
    pthread_join(r2, NULL);

    printf("pthread rwlock ok (psynch_rw_* is kernel slow-path on Darwin)\n");
    printf("label: rd/wr/unlock = BSD→Mach; upgrade/downgrade = stub in this xnu\n");
    printf("day68 ok\n");
    return 0;
}
```

```bash
cc -o day68_demo day68_demo.c -lpthread && ./day68_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能标 BSD→Mach，并知道 upgrade/downgrade 是 stub  
- [ ] 能说读共享 / 写独占  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-68.md`

下一步：**[Day 69](day-69.md)** → `psynch_rw_longrdlock` / `yieldwrlock` / `cvclrprepost` + `bsdthread_create` / `bsdthread_terminate`
