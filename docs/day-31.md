# 第三十一天（Day 31）正文

学这两个：**`getpriority` / `setpriority`**  
源码：`xnu/` = **xnu-12377.121.6**

接着 Day 30 的「资源账」，今天看**调度相关的 nice 优先级**：查 / 改进程（组/用户）的「nice」值。

生活类比：

1. `getpriority`：问「这些进程里，谁最‘优先’（nice 最小）」  
2. `setpriority`：调某个进程（或一组）的 nice——数字越大通常越谦让 CPU  

（数值习惯：nice 高 → 更“nice”、更愿意让出 CPU；具体调度还接 Mach 侧。）

---

## 今天目标

1. 找到编号 **100 / 96**  
2. 理解经典路径：`PRIO_PROCESS` ↔ `proc->p_nice`  
3. 理解 `setpriority` → `donice` → 写 `p_nice` → `resetpriority`  
4. 知道还有 Darwin 扩展（线程 BG、role 等），今天略读  

笔记：[`notes/daily/day-31.md`](../notes/daily/day-31.md)  
分析：[`notes/daily/day-31-analysis.md`](../notes/daily/day-31-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getpriority | **100** | 查询优先级（nice / Darwin 扩展） |
| setpriority | **96** | 设置优先级 |

`which`（作用范围）常见：

| which | 含义 |
|-------|------|
| `PRIO_PROCESS` | 单个进程（`who=0` 表示自己） |
| `PRIO_PGRP` | 进程组里取/设 |
| `PRIO_USER` | 某 uid 下进程 |
| Darwin 扩展 | 线程 BG、process BG、role…（略） |

---

## 1. getpriority（#100）——查 nice（经典）

[`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：

```c
getpriority(which, who) {
    switch (which) {
    case PRIO_PROCESS:
        p = (who==0) ? 当前 : proc_find(who)
        low = p->p_nice
    case PRIO_PGRP:  扫组内，取最小 p_nice
    case PRIO_USER:  扫同 uid，取最小 p_nice
    // … Darwin 分支略
    }
    *retval = low   // 经 syscall 返回值带回
}
```

要点：

- 对进程组/用户：返回范围内**最低**的 nice（最“优先”的那个）  
- 找不到目标 → `ESRCH`  
- 用户层注意：返回值可以是 -1（合法 nice），要用 `errno` 区分失败  

---

## 2. setpriority（#96）——改 nice（经典）

```c
setpriority(which, who, prio) {
    case PRIO_PROCESS:
        donice(当前, 目标, prio)
    case PRIO_PGRP / PRIO_USER:
        迭代多个进程，分别 donice
}

donice(curp, chgp, n) {
    权限：不能随便改别人的；提高优先级（nice 变小）常要 root
    夹紧到 PRIO_MIN..PRIO_MAX
    chgp->p_nice = n
    resetpriority(chgp)   // 接到调度侧
}
```

权限直觉：

| 操作 | 常见要求 |
|------|----------|
| 改自己/同用户 | 一般可以（受策略约束） |
| 改别人的进程 | 常要特权 |
| nice 往更优先调（数值变小） | 常要 root（`EACCES`） |

---

## 今日串起来

```text
getpriority(PRIO_PROCESS, 0)  → 读自己的 p_nice
setpriority(PRIO_PROCESS, 0, n) → donice → p_nice → resetpriority
```

| 调用 | 内核关键 |
|------|----------|
| getpriority | 读 `p_nice`（或扫一组取最小） |
| setpriority | `donice` 写 `p_nice` + `resetpriority` |

和 Day 30：`getrusage` 看**花了多少**；今天看**调度谦让程度**（nice）。

---

## 做完打勾

- [ ] 找到 100 / 96  
- [ ] 能说 PRIO_PROCESS 对应 p_nice  
- [ ] 能说 set → donice → resetpriority  
- [ ] 知道提高优先级常要特权  
- [ ] 填好 `notes/daily/day-31.md`

下一步：Day 32 → [`setrlimit` / `getrlimit`](day-32.md)
