# 源码分析：Day 17（sigaction / sigprocmask / sigpending）

基于 `xnu-12377.121.6`。信号安装、屏蔽与未决查询。

---

## 1. 心智模型

```text
Day 13：kill → cansignal → psignal（投递）

今天：接收侧三件套
  sigaction     这个信号来了干什么？
  sigprocmask   现在哪些信号先别递送？
  sigpending    已经到了、还卡着的有哪些？
```

---

## 2. sigaction 主路径

[`kern_sig.c`](../../xnu/bsd/kern/kern_sig.c)：

```
sigaction
  拒绝 signum≤0 / ≥NSIG / SIGKILL / SIGSTOP
  若 osa：从进程 sigacts 组装旧动作 → copyout
  若 nsa：copyin → setsigvec(p, thread, signum, …)
             更新 p_sigcatch / p_sigignore 等
```

`setsigvec` 大意：

- `SIG_IGN`（或默认即忽略的信号）→ 记入 `p_sigignore`  
- 用户 handler → `p_sigcatch`  
- `SIG_DFL` → 清 catch，按默认属性  

和生命周期接点：`SA_NOCLDWAIT` 等影响子进程僵尸策略（Day 11–12 提过）。

---

## 3. sigprocmask 主路径

```
sigprocmask(how, mask, omask)
  old = current_uthread()->uu_sigmask
  copyin mask（若有）
  SIG_BLOCK / UNBLOCK / SETMASK
    → block_procsigmask / unblock_… / set_…
    （去掉 sigcantmask：KILL/STOP 等）
  signal_setast(current_thread())  // 可能立刻再评估递送
  copyout old → omask
```

**屏蔽 vs 忽略：**

| | `sigprocmask` 挡住 | `SIG_IGN` |
|--|-------------------|-----------|
| 信号还在吗 | 常进 pending，解开后还可递送 | 丢弃/不递送 handler |
| 作用范围 | 当前线程掩码（本实现看 uthread） | 进程对该信号的动作 |

---

## 4. sigpending 主路径

```
sigpending
  pendlist = ut->uu_siglist & ~sigcantmask
  copyout
```

未决集来自线程（及进程侧投递后挂到线程的位）。用于调试或“先看有没有 SIGCHLD 之类再决定 wait”。

---

## 5. 和 kill 串起来

```
kill(pid, sig)
  → psignal
       若目标忽略 → 可能直接没了
       若目标屏蔽 → 记入 pending（siglist）
       否则 → 安排递送 / 跑 handler / 默认终止等
```

递送细节、信号栈、线程定向信号 → Day 18。

---

## 6. 建议点开的文件

1. `syscalls.master` — 46 / 48 / 52  
2. `kern_sig.c` — `sigaction` / `setsigvec` 开头  
3. `kern_sig.c` — `sigprocmask` 的三个 `how`  
4. `kern_sig.c` — `sigpending`  

验收：能口述「装动作 / 改掩码 / 看未决」；能区分 mask 与 IGN。
