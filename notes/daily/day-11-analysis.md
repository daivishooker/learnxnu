# 源码分析：Day 11（fork / vfork / wait4）

基于 `xnu-12377.121.6`。进程创建与等待。

---

## 1. 心智模型

```text
父 proc / task
    │ fork
    ├──────────────────► 子 proc / task（新 pid）
    │
    │ 子 exit → 僵尸 SZOMB
    ▼
  wait4 回收状态，去掉僵尸
```

XNU：**BSD `proc`**（Unix 语义：pid、凭证、fd…）+ **Mach `task`/`thread`**（地址空间、调度）。`fork` 两边都要造。

---

## 2. fork 主路径

[`kern_fork.c`](../../xnu/bsd/kern/kern_fork.c)：

```
fork
  → fork1(..., PROC_CREATE_FORK)
       检查进程数上限 nprocs / 每用户 RLIMIT_NPROC
       cloneproc(..., CLONEPROC_FORK)
         task_create_internal …
         forkproc … 新 BSD proc
       thread_dup(子线程)  // 复制寄存器等，形成「从 fork 返回」的现场
  父返回：*retval = 子 pid
  子稍后：task_clear_return_wait → 在用户态看到返回值 0
```

`retval[1]=0` 等细节配合用户态 stub，区分父/子返回（平台相关）。

内存：fork 语义是复制地址空间；实现上多用 **COW**，页在写入前共享。

---

## 3. wait4 主路径

[`kern_exit.c`](../../xnu/bsd/kern/kern_exit.c)：

```
wait4 → wait4_nocancel
  锁进程列表，遍历自己的 children
  按 pid / WAIT_ANY / 进程组过滤
  找到 SZOMB → 取 status、可选 rusage，reap
  否则 sleep 等待（除非 WNOHANG）
```

和 Day 1 的 `getppid` 对照：父子关系在 `proc` 上；wait 认的是这棵孩子列表。

---

## 4. vfork：经典 vs 本树

**经典意图：** 子马上 `exec`，不想付完整 fork 拷地址空间的成本 → 共享 VM，父暂停。

**本树现实：**

- `syscalls.master` 里 `#66` 包在 `#if CONFIG_VFORK`；否则是 `nosys`  
- 完整独立 `vfork()` 实现不一定还能在 `bsd/kern` 里直接搜到  
- 仍有 `psignal_vfork`、历史 flag 等痕迹  
- 现代创建进程：`posix_spawn`（Day 13）往往更干净

学习建议：把 vfork 当**概念对照**；动手跟代码以 **fork + wait4** 为主。

---

## 5. 建议点开的文件

1. `syscalls.master` — 2 / 7 / 66  
2. `kern_fork.c` — `fork` / `fork1` 的 `PROC_CREATE_FORK` 分支  
3. `kern_fork.c` — `cloneproc` 注释（继承 task/内存）  
4. `kern_exit.c` — `wait4` / `wait4_nocancel` 找 `SZOMB` 那段  

验收：能画「fork 出子 → 子结束变僵尸 → wait4 回收」。
