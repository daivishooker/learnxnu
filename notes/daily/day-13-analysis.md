# 源码分析：Day 13（posix_spawn / kill）

基于 `xnu-12377.121.6`。现代创建进程与信号投递入口。

---

## 1. 心智模型

```text
经典：
  fork  →  子短暂跑父代码  →  execve 换映像  →  父 wait4

现代（默认 posix_spawn）：
  一次 syscall
    → 内核 fork1(SPAWN) 造空壳子进程（不继承父内存）
    → 应用 file_actions / attr
    → exec_activate_image 装目标程序
    → 父拿到子 pid，继续跑

信号：
  kill(pid, sig) → cansignal → psignal → …（处理留 Day 17）
```

---

## 2. posix_spawn 主路径

[`kern_exec.c`](../../xnu/bsd/kern/kern_exec.c) 里 `posix_spawn`：

```
posix_spawn
  填 image_params（path / argv / envp）
  若 adesc ≠ NULL：copyin 属性描述符
       spawnattr、file_actions、port actions…

  分支 A — 默认（无 SETEXEC）：
    fork1(..., PROC_CREATE_SPAWN)
      新 proc/task/thread；不继承父地址空间
    IMGPF_SPAWN / spawn_no_exec = TRUE
    可选：exec_handle_file_actions 等
    exec_activate_image(imgp)
    父：把子 pid copyout 到用户指针；父不换映像

  分支 B — POSIX_SPAWN_SETEXEC：
    cloneproc(..., CLONEPROC_EXEC)   // 同 Day 12 execve
    IMGPF_EXEC
    exec_activate_image
    proc_exec_switch_task            // 调用者自己变成新程序
```

源码注释把 SETEXEC 说成 **「execve() with options」**：同一套装载，附带 spawn 的属性能力。

**为何比用户态 fork+exec 香（教学结论）：**

1. 一次陷入内核  
2. 子进程不先跑父代码（多线程更安全）  
3. FD 重定向、信号默认动作等可在映像跑起来前设好  

装载器仍复用 Day 12 的 `exec_activate_image` / `execsw[]`（Mach-O / Fat / `#!`）。

---

## 3. kill 主路径

[`kern_sig.c`](../../xnu/bsd/kern/kern_sig.c)：

```
kill(cp, {pid, signum, posix})
  signum ≥ NSIG → EINVAL
  pid > 0:
    proc_find(pid)
      无：若 pzfind 僵尸 → 0（POSIX：杀僵尸算成功）
           否则 ESRCH
    cansignal(调用者, 凭证, 目标, signum) 失败 → EPERM
    signum ≠ 0 → psignal(目标, signum)
  pid == 0 / -1 / < -1:
    killpg1(...)  // 本进程组 / 广播 / 指定组
```

今天只跟到 **投递入口**。信号如何进线程、如何变成 handler/`exit`，放到 Day 17（`sigaction` 等）。

和生命周期的接点：

- `exit` → 父收 `SIGCHLD`（内核 `psignal`）  
- 用户 `kill(子, SIGTERM)` → 同一 `psignal` 家族  

---

## 4. 和 Day 11–12 串起来

| 场景 | 常用组合 |
|------|----------|
| 自己开子进程跑程序 | `posix_spawn`（或 `fork`+`execve`）→ `wait4` |
| 换成自己变程序 | `execve` 或 `posix_spawn`+`SETEXEC` |
| 结束自己 | `exit` |
| 让别人停/死/自定义动作 | `kill` → 对方信号处理或默认终止 |

---

## 5. 建议点开的文件

1. `syscalls.master` — 244 / 37  
2. `kern_exec.c` — `posix_spawn`；搜 `PROC_CREATE_SPAWN`、`POSIX_SPAWN_SETEXEC`  
3. `kern_exec.c` — 成功路径里对 `spawn_no_exec` 的分支（要不要 `proc_exec_switch_task`）  
4. `kern_sig.c` — `kill` / `cansignal` / `psignal` 调用点  

验收：能画「spawn 一步出子」vs「fork+exec」；能说 kill 只是信号入口，权限在 `cansignal`。
