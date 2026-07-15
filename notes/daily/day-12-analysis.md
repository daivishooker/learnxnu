# 源码分析：Day 12（execve / exit）

基于 `xnu-12377.121.6`。地址空间替换与进程终结。

---

## 1. 心智模型

```text
fork 之后常见路径：

  子进程 ──execve──► 同一 pid，新程序从入口跑
       │
       └──exit──► SZOMB 僵尸 ──wait4──► 父拿到状态，槽位释放

对照：
  fork   = 复制一份「还在跑旧代码」的进程
  execve = 不造新 pid（用户语义），换掉代码/数据/栈
  exit   = 主动结束；资源大半已清，只留瘦 proc 给 wait
```

---

## 2. execve 主路径

[`kern_exec.c`](../../xnu/bsd/kern/kern_exec.c)：

```
execve
  → __mac_execve
       分配/填充 image_params（fname / argv / envp）
       cloneproc(..., CLONEPROC_EXEC)
         // 新 task + 新 proc + 新 thread；先不对用户可见
       exec_activate_image(imgp)
         execargs_alloc / exec_save_path
         namei → vnode
         按 execsw[] 试 activator：
           exec_mach_imgact  // Mach-O MH_EXECUTE
           exec_fat_imgact   // 多架构，选一片再重读
           exec_shell_imgact // #! 解释器
         （Mach-O）load_machfile → 新 vm_map；摆用户栈字符串
       成功：proc_exec_switch_task(旧, 新, …)
         新映像接管该 pid；旧 task 收尾
       失败：返回 errno，调用者程序继续
```

**教学重点（本树特有）：**  
经典教材写「原地换地址空间」；现代 XNU 的 `execve` 走 **`CLONEPROC_EXEC` 影子进程再切换**，失败时可更干净地回退。用户仍应记住：**成功 = 旧用户代码再也跑不到**。

**image activator：** 表在 `execsw[]`，按顺序试；`-1` 表示「不是我这种，让下一个试」。

---

## 3. exit 主路径

[`kern_exit.c`](../../xnu/bsd/kern/kern_exit.c)：

```
exit（syscall，noreturn）
  → exit1 → exit_with_reason
       proc_transstart（与并发 exec/exit 互斥）
       标 P_LEXIT，写 p_xstat = W_EXITCODE(rval, 0)
       proc_prepareexit
       task_terminate_internal(task)
  最后一个线程终止时 → proc_exit
       已是僵尸的孩子：内核可直接 reap
       仍活着的孩子：reparent → initproc（launchd），并可 SIGCHLD
       自己：allproc → zombproc，p_stat = SZOMB
       给父进程 SIGCHLD（除非 P_NOCLDWAIT 等特殊情况）
```

和 Day 11 的 `wait4` 对上：`exit` 造出可报告状态；`wait4` 把它收掉。

**不会「卡在 exit 里等」：** `exit` 本身走完终结；父进程若不 `wait*`，僵尸会占 `nprocs`，那是另一件事（前面问答已讲过）。

---

## 4. 和 fork / wait4 串起来

| 调用 | 角色 |
|------|------|
| `fork` | 出新 pid，两份执行流 |
| `execve` | 子进程换成目标程序 |
| `exit` | 目标程序结束（或中途失败退出） |
| `wait4` | 父回收状态 |

Day 13 的 `posix_spawn` 往往把「创建 + 若干属性 + 类 exec」合成一步，少踩 `fork`/`vfork` 的坑。

---

## 5. 建议点开的文件

1. `syscalls.master` — 1 / 59  
2. `kern_exec.c` — `execve` / `__mac_execve` 开头到 `exec_activate_image`  
3. `kern_exec.c` — `execsw[]` 与 `exec_mach_imgact` 里对 `MH_EXECUTE` 的检查  
4. `kern_exit.c` — `exit` / `exit_with_reason` / `proc_exit` 里进 `zombproc` 的段落  

验收：能口述「fork 出子 → execve 换程序 → exit 变僵尸 → wait4 回收」。
