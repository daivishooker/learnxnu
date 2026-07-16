# 第十七天（Day 17）正文

学这三个：**`sigaction` / `sigprocmask` / `sigpending`**  
源码：`xnu/` = **xnu-12377.121.6**

离开内存映射，进入**信号**：Day 13 的 `kill` 是投递入口；今天学接收侧——怎么安装处理、怎么屏蔽、怎么看未决信号。

---

## 今天目标

1. 找到编号 **46 / 48 / 52**  
2. 理解 `sigaction`：为某个信号设定处理动作（默认 / 忽略 / handler）  
3. 理解 `sigprocmask`：当前线程的信号屏蔽字  
4. 理解 `sigpending`：查看已挂起、尚未递送的信号

笔记：[`notes/daily/day-17.md`](../notes/daily/day-17.md)  
分析：[`notes/daily/day-17-analysis.md`](../notes/daily/day-17-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sigaction | **46** | 查询/设置某信号的处理动作 |
| sigprocmask | **48** | 查询/修改信号屏蔽掩码 |
| sigpending | **52** | 取出当前未决信号集 |

---

## 1. sigaction（#46）

[`kern_sig.c`](../xnu/bsd/kern/kern_sig.c)：

```c
sigaction(signum, nsa, osa) {
    if (signum 非法或 SIGKILL/SIGSTOP) → EINVAL
    if (osa)  copyout 旧动作（handler、mask、flags）
    if (nsa)  copyin 新动作 → setsigvec(...)
}
```

处理动作三种常见形态：

| `sa_handler` | 含义 |
|--------------|------|
| `SIG_DFL` | 默认（很多是终止进程） |
| `SIG_IGN` | 忽略 |
| 函数地址 | 用户自定义 handler |

要点：

- **`SIGKILL` / `SIGSTOP` 不能改**（不能装 handler、不能忽略）  
- 动作记在进程的 **`sigacts` / `p_sigcatch` / `p_sigignore`** 等  
- 和 Day 13 对上：`kill` → `psignal` 投递；递送时看这里装的是什么  

`SA_RESTART`、`SA_SIGINFO`、`SA_NOCLDWAIT` 等 flags 先知道有即可，不必一天啃完。

---

## 2. sigprocmask（#48）

```c
sigprocmask(how, mask, omask) {
    old = 当前 uthread->uu_sigmask
    if (mask) {
        copyin 新掩码
        switch (how) {
          SIG_BLOCK:   屏蔽字 |= mask
          SIG_UNBLOCK: 屏蔽字 &= ~mask
          SIG_SETMASK: 屏蔽字 = mask
        }
        // 会剔除不能屏蔽的（如 KILL/STOP 一类）
        signal_setast(...)  // 可能触发再检查待递送信号
    }
    if (omask) copyout(old)
}
```

要点：

- **屏蔽 ≠ 忽略**：挡住的信号常常会先**挂起**，解开后再递送  
- 掩码在 **当前线程** 的 `uu_sigmask`（多线程时每线程可不同）  
- `SIGKILL` / `SIGSTOP` 通常仍挡不住  

场景：临界区里先 `SIG_BLOCK`，干完再 `SIG_UNBLOCK`，避免半截被打断。

---

## 3. sigpending（#52）

```c
sigpending(osv) {
    pendlist = 当前线程 uu_siglist（去掉不能泄露的位）
    copyout → 用户
}
```

要点：

- 看的是**已经到了、但还没递送给 handler 的信号**（常因被 mask）  
- 只读查询，不改变处理动作  

---

## 今日对比

| | sigaction | sigprocmask | sigpending |
|--|-----------|-------------|------------|
| 改处理方式？ | 是 | 否 | 否 |
| 改屏蔽？ | 否（handler 里可另有 mask） | 是 | 否 |
| 看未决？ | 否 | 否 | 是 |

串起来：

```text
kill 投递 → 若被 mask：进 pending
         → 未 mask：按 sigaction 的动作处理（DFL/IGN/handler）
```

---

## 做完打勾

- [ ] 找到 46 / 48 / 52  
- [ ] 能说 sigaction 装动作；KILL/STOP 不能改  
- [ ] 能说 mask 挂起 vs IGN 忽略  
- [ ] 能说 sigpending 看 uu_siglist  
- [ ] 填好 `notes/daily/day-17.md`

下一步：Day 18 → `sigaltstack` / `__pthread_kill`
