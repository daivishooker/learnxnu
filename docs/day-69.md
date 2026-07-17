# 第六十九天（Day 69）正文

学这五个：**`psynch_rw_longrdlock` / `psynch_rw_yieldwrlock` / `psynch_cvclrprepost` / `bsdthread_create` / `bsdthread_terminate`**  
源码：`xnu/` = **xnu-12377.121.6**

**归属：全部 BSD→Mach（经 pthread shim / pthread.kext）**  
- 入口：BSD `sysent`  
- 实现：`pthread_shims.c` → `pthread_functions->…`  
- `bsdthread_terminate` 在转发前还有一点 XNU 侧预处理（workq 标签、join 用 ulock 兼容）

今天两块：

1. **psynch 扫尾**：rwlock 变体 + cond 清 prepost  
2. **线程生命周期入口**：`pthread_create` / 线程退出背后的 `bsdthread_*`

---

## 今天目标

1. 找到编号 **297 / 298 / 312 / 360 / 361**  
2. 能标：**BSD→Mach**  
3. 知道 `longrdlock` 在现网 kext 里基本是死槽；`yieldwrlock` / `cvclrprepost` 的用途直觉  
4. 能说：`pthread_create` → `bsdthread_create`；线程退出 → `bsdthread_terminate`  

笔记：[`notes/daily/day-69.md`](../notes/daily/day-69.md)  
分析：[`notes/daily/day-69-analysis.md`](../notes/daily/day-69-analysis.md)

---

## 总表

| 名字 | # | 标签 | 作用 |
|------|---|------|------|
| psynch_rw_longrdlock | **297** | BSD→Mach | 历史「长读者」等待槽；现行 libpthread kext 常直接 `ESRCH` |
| psynch_rw_yieldwrlock | **298** | BSD→Mach | 写锁等待变体（yield 策略） |
| psynch_cvclrprepost | **312** | BSD→Mach | 清掉 cond/mutex 上挂着的 prepost 唤醒 |
| bsdthread_create | **360** | BSD→Mach | 创建用户线程（`pthread_create` 内核侧） |
| bsdthread_terminate | **361** | BSD→Mach | 终止当前线程并回收栈/port/join 通知 |

旁注：`psynch_rw_unlock2`(#309) 本树 shim 返回 `ENOTSUP`，不必再开一天。

---

## 1. psynch 扫尾

### longrdlock / yieldwrlock

与 Day 68 的 `rdlock`/`wrlock` 同形：用户态 rwlock 地址 + 代数 → kext。

| | 日常路径（Day 68） | 今天 |
|--|-------------------|------|
| 读 | `psynch_rw_rdlock` | `longrdlock`：旧语义槽，现行实现多半不用 |
| 写 | `psynch_rw_wrlock` | `yieldwrlock`：写者等待的另一种策略入口 |

记住：**读写锁主路径仍是 rd/wr/unlock**；今天这两个是边角/历史。

### cvclrprepost

条件变量协议里，有时内核会「提前记一笔唤醒」（prepost），避免 waiter 刚好错过 signal。  
当用户态发现这笔 prepost 已经不需要了，就调 `psynch_cvclrprepost` **清掉**，防止脏状态留下。

```text
cvwait / cvsignal 主路径（Day 67）
  └─ 偶发：用户态发现需清 prepost → psynch_cvclrprepost
```

你几乎不会直接调它；跟着 `pthread_cond_*` 内部走。

---

## 2. bsdthread_create / bsdthread_terminate

[`pthread_shims.c`](../xnu/bsd/pthread/pthread_shims.c)：

```c
bsdthread_create(...) {
    return pthread_functions->bsdthread_create(p, func, func_arg, stack, pthread, flags, retval);
}

bsdthread_terminate(...) {
    /* workq 线程：先 workq_thread_terminate */
    /* join：若 sema_or_ulock 不像 port，则当成 ulock 地址延后唤醒 */
    return pthread_functions->bsdthread_terminate(...);
}
```

用户层对应：

```text
pthread_create
  → 用户态备好栈 / pthread_t 结构
  → bsdthread_create（内核真正把 Mach thread 拉起来跑）

线程函数返回 / pthread_exit
  → bsdthread_terminate
  → 回收栈范围、处理 thread port、叫醒 join 方（信号量或 ulock）
```

和 Day 65 `workq_*` 的关系：

| | `bsdthread_create` | `workq_*` |
|--|--------------------|-----------|
| 谁用 | 普通 `pthread_create` | GCD / libpthread 工人池 |
| 线程寿命 | 随该 pthread | 内核管理的工人，可复用 |

---

## 3. 和前几天的拼图

```text
Day 67  psynch mutex/cond     — 锁与条件变量慢路径
Day 68  psynch_rw_*           — 读写锁慢路径
Day 69  psynch 边角 + bsdthread — 扫尾 + 线程创建/退出
Day 65  workq_*               — 工人池（另一条造线程路）
Day 66  ulock / thread_selfid — 轻量锁与线程 id
```

---

## 用户层 Demo

> 不直接调 `bsdthread_*` / `psynch_*`。用 `pthread_create` + `pthread_join` 演示创建/汇合（Darwin 上会走到今天的 create/terminate）。

```c
#include <pthread.h>
#include <stdio.h>

static void *worker(void *arg) {
    int n = *(int *)arg;
    printf("worker got %d\n", n);
    return (void *)(long)(n + 1);
}

int main(void) {
    pthread_t t;
    int arg = 41;
    void *ret = NULL;

    if (pthread_create(&t, NULL, worker, &arg) != 0) {
        perror("pthread_create");
        return 1;
    }
    if (pthread_join(t, &ret) != 0) {
        perror("pthread_join");
        return 1;
    }

    printf("join got %ld\n", (long)ret);
    printf("pthread_create/join ok (bsdthread_* is Darwin kernel path)\n");
    printf("label: BSD→Mach via pthread_shims → pthread.kext\n");
    printf("day69 ok\n");
    return 0;
}
```

```bash
cc -o day69_demo day69_demo.c -lpthread && ./day69_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能标 BSD→Mach  
- [ ] 能说 longrdlock 近乎死槽、cvclrprepost 清 prepost  
- [ ] 能说 create/terminate 对应 pthread_create/退出  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-69.md`

下一步：Day 70 → `bsdthread_register` / `bsdthread_ctl` + pthread 取消相关（`__disable_threadsignal` / `__pthread_markcancel` / `__pthread_canceled`）
