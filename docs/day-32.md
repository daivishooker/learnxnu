# 第三十二天（Day 32）正文

学这两个：**`setrlimit` / `getrlimit`（回顾）**  
源码：`xnu/` = **xnu-12377.121.6**

Day 21 只看过 `getrlimit`；今天补上 **`setrlimit`**，并把「上限」和 Day 30 的「已用量」对照清楚。

生活类比：

1. `getrlimit`：看护栏有多高（soft / hard）  
2. `setrlimit`：调整护栏（抬高 hard 通常要特权）

---

## 今天目标

1. 找到编号 **195 / 194**  
2. 理解 `rlimit`：`rlim_cur`（soft）与 `rlim_max`（hard）  
3. 理解 `setrlimit` → `dosetrlimit`：校验、权限、按 `which` 生效  
4. 能对比：rlimit（上限）vs rusage（已用）  

笔记：[`notes/daily/day-32.md`](../notes/daily/day-32.md)  
分析：[`notes/daily/day-32-analysis.md`](../notes/daily/day-32-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| setrlimit | **195** | 设置某类资源上限 |
| getrlimit | **194** | 查询某类资源上限 |

常见 `which`：`RLIMIT_NOFILE`（FD 数）、`RLIMIT_STACK`、`RLIMIT_CPU`、`RLIMIT_DATA`…

---

## 1. getrlimit（#194）——回顾：读上限

[`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：

```c
getrlimit(which, rlp) {
    if (which 非法) → EINVAL
    lim = proc_limitget(p, which)   // soft + hard
    copyout(&lim, rlp)
}
```

结构：

```c
struct rlimit {
    rlim_t rlim_cur;  // soft：当前生效上限
    rlim_t rlim_max;  // hard：soft 不能超过它；抬高常要 root
};
```

---

## 2. setrlimit（#195）——改上限

```c
setrlimit(which, rlp) {
    copyin → alim
    dosetrlimit(p, which, &alim)
}

dosetrlimit(...) {
    soft 不能 > hard → EINVAL
    抬高 hard（或 soft 超过旧 hard）→ 要特权，否则 EPERM
    switch (which) {
      RLIMIT_CPU / STACK / NOFILE / DATA … 各自接到计时器、VM、FD 表等
    }
    写回进程的 plimit
}
```

要点：

| 规则 | 含义 |
|------|------|
| soft ≤ hard | 始终成立 |
| 普通用户 | 多半只能**降低** hard，或在 hard 内调 soft |
| root | 可以抬高 hard |
| 已超限 | 有的资源若当前用量已超新上限 → 可能 `EINVAL` |

---

## 3. 三套「资源」对照

| 接口 | 问的是什么 |
|------|------------|
| `getrlimit` / `setrlimit` | **上限**（护栏） |
| `getrusage`（Day 30） | **已用掉多少**（账单） |
| `getpriority`（Day 31） | **调度谦让**（nice），不是 rlimit |

```text
例如 RLIMIT_NOFILE = 最多能开多少 FD
getrusage 不直接等于「现在开了几个」；那是另一类统计/计数
```

---

## 用户层 Demo

先 `getrlimit` 再尝试降低 `RLIMIT_NOFILE` 软限制（勿把硬限制乱抬高）。

```c
#include <stdio.h>
#include <sys/resource.h>

int main(void) {
    struct rlimit rl;
    if (getrlimit(RLIMIT_NOFILE, &rl) != 0) { perror("getrlimit"); return 1; }
    printf("nofile soft=%llu hard=%llu\n",
           (unsigned long long)rl.rlim_cur,
           (unsigned long long)rl.rlim_max);
    if (rl.rlim_cur > 32) {
        rl.rlim_cur = 32;
        if (setrlimit(RLIMIT_NOFILE, &rl) != 0) perror("setrlimit");
    }
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 195 / 194  
- [ ] 能说 soft / hard  
- [ ] 能说抬高 hard 常要特权  
- [ ] 能对比 rlimit vs rusage  
- [ ] 填好 `notes/daily/day-32.md`

下一步：Day 33 → [`sys_flock`](day-33.md)
