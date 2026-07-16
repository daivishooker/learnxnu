# 源码分析：Day 30（getrusage / gettimeofday）

基于 `xnu-12377.121.6`。资源统计与墙钟读取。

---

## 1. 心智模型

```text
getrusage(SELF)
  proc → task（Mach）→ CPU/缺页/RSS…
  → 填 struct rusage → copyout

getrusage(CHILDREN)
  p_stats->p_cru（子进程退出时累加）→ copyout

gettimeofday
  日历时钟 → timeval（+ 可选 timezone / mach_absolute_time）→ copyout
```

---

## 2. getrusage 主路径

[`kern_resource.c`](../../xnu/bsd/kern/kern_resource.c)：

```
RUSAGE_SELF:
  calcru(p, &utime, &stime)
    task_info / recount_task_times → 用户/系统时间等
  更新 p->p_stats->p_ru 后整份拷出
RUSAGE_CHILDREN:
  p->p_stats->p_cru
munge 32/64 → copyout
```

与 `getrlimit`（上限）分工：一个 cap，一个 usage。

---

## 3. gettimeofday 主路径

[`kern_time.c`](../../xnu/bsd/kern/kern_time.c)：

```
clock_gettimeofday_and_absolute_time
copyout timeval
可选 copyout tz、mach_absolute_time
```

写时间走 `settimeofday`（要 entitlement/root/MAC）——今天只读。

---

## 4. 建议点开

1. `syscalls.master` — 117 / 116  
2. `kern_resource.c` — `getrusage` / `calcru`  
3. `kern_time.c` — `gettimeofday`  

验收：能说 SELF/CHILDREN；能说时间从时钟子系统 copyout。
