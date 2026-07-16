# 第三十天（Day 30）正文

学这两个：**`getrusage` / `gettimeofday`**  
源码：`xnu/` = **xnu-12377.121.6**

第 5 周第二天：不问网络对象，问内核两件大事——**我这个进程花了多少资源**，以及**现在几点（墙钟）**。

生活类比：

1. `getrusage`：查自己的「工时单」（用户态 CPU、内核态 CPU、缺页…）  
2. `gettimeofday`：看墙上的钟（日历时间；Darwin 还可顺带拿 Mach 绝对时间）

---

## 今天目标

1. 找到编号 **117 / 116**  
2. 理解 `getrusage`：从 `proc`/`task` 汇总 `rusage`，`who` 选自己或已回收子进程  
3. 理解 `gettimeofday`：读日历时间 copyout；可选 timezone / mach absolute time  
4. 能对比：进程资源账 vs 系统墙钟  

笔记：[`notes/daily/day-30.md`](../notes/daily/day-30.md)  
分析：[`notes/daily/day-30-analysis.md`](../notes/daily/day-30-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getrusage | **117** | 查询进程（或子进程累计）资源使用 |
| gettimeofday | **116** | 查询当前墙钟时间 |

---

## 1. getrusage（#117）——我的资源账单

[`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：

```c
getrusage(who, rusage) {
    switch (who) {
    case RUSAGE_SELF:
        calcru(p, &utime, &stime)   // 从 Mach task 汇总 CPU 等
        填 p->p_stats->p_ru
        break;
    case RUSAGE_CHILDREN:
        取 p->p_stats->p_cru       // 已 wait 回收的子进程累计
        break;
    }
    copyout(rusage 结构)
}
```

要点：

| `who` | 含义 |
|-------|------|
| `RUSAGE_SELF` | 当前进程自己 |
| `RUSAGE_CHILDREN` | 已终结并被 wait 掉的子进程累计 |

`calcru` 会问 Mach `task`（用户/系统时间、缺页、RSS 峰值等），再放进 BSD 的 `rusage`。  
和 Day 21 `getrlimit` 对照：limit 是**上限**；rusage 是**已用掉多少**。

---

## 2. gettimeofday（#116）——墙上几点

[`kern_time.c`](../xnu/bsd/kern/kern_time.c)：

```c
gettimeofday(tp, tzp, mach_absolute_time) {
    clock_gettimeofday_and_absolute_time(&secs, &usecs, &mach_time)
    若 tp：copyout timeval（秒 + 微秒）
    若 tzp：copyout timezone（历史字段，少用）
    若 mach_absolute_time：copyout Mach 绝对时间嘀嗒
}
```

要点：

- 读的是**系统日历时间**（可被 `settimeofday` 等改，改通常要特权）  
- Darwin 这个 syscall 多一个可选输出：`mach_absolute_time`（单调递增的机器时间基数，适合测间隔）  
- 今天跟到「从时钟子系统读出 → copyout」即可  

---

## 今日串起来

```text
getrusage     → 问「这个 proc/task 花了多少」
gettimeofday  → 问「现在系统认为几点」
```

| 调用 | 数据从哪来 |
|------|------------|
| getrusage | `proc` 统计 + Mach `task_info` / recount |
| gettimeofday | 日历时钟（+ 可选 Mach absolute） |

两者都很「只读查询」：几乎无复杂对象生命周期，适合练**统计字段从哪汇总、怎么 copyout**。

---

## 用户层 Demo

`gettimeofday` 读墙钟；`getrusage` 看本进程用户/系统 CPU 时间。

```c
#include <stdio.h>
#include <sys/resource.h>
#include <sys/time.h>

int main(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    printf("sec=%ld usec=%d\n", (long)tv.tv_sec, (int)tv.tv_usec);
    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    printf("utime=%ld.%06d\n",
           (long)ru.ru_utime.tv_sec, (int)ru.ru_utime.tv_usec);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 117 / 116  
- [ ] 能说 RUSAGE_SELF vs CHILDREN  
- [ ] 能说 getrusage 接 Mach task 统计  
- [ ] 能说 gettimeofday 读墙钟并 copyout  
- [ ] 填好 `notes/daily/day-30.md`

下一步：Day 31 → [`getpriority` / `setpriority`](day-31.md)
