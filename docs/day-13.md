# 第十三天（Day 13）正文

学这两个：**`posix_spawn` / `kill`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 11–12：已经会 `fork → execve → wait4 / exit`。  
今天看 Darwin 上更常用的**一步创建进程**，以及**信号投递入口** `kill`。

---

## 今天目标

1. 找到编号 **244 / 37**  
2. 理解 `posix_spawn` ≈「创建子进程 + 装映像」，少走用户态 `fork` 中间态  
3. 知道默认 spawn 与 `POSIX_SPAWN_SETEXEC`（类 exec）两条路  
4. 理解 `kill`：按 pid/`cansignal` 找到目标，再 `psignal`

笔记：[`notes/daily/day-13.md`](../notes/daily/day-13.md)  
分析：[`notes/daily/day-13-analysis.md`](../notes/daily/day-13-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| posix_spawn | **244** | 创建新进程并加载指定程序（可带 file actions / attr） |
| kill | **37** | 向进程（或进程组）投递信号 |

---

## 1. posix_spawn（#244）

[`kern_exec.c`](../xnu/bsd/kern/kern_exec.c)：

```c
posix_spawn(父, path, adesc, argv, envp) {
    填 image_params
    copyin 属性描述符（file_actions、spawnattr…）若有

    若没有 POSIX_SPAWN_SETEXEC：   // 默认：真·spawn
        fork1(..., PROC_CREATE_SPAWN)  // 新 proc/task，不继承父内存
        应用 file_actions / 端口 / 信号等属性
        exec_activate_image(...)       // 装 Mach-O / Fat / #!
        父：copyout 子 pid，自己继续跑

    若有 POSIX_SPAWN_SETEXEC：      // 「带选项的 execve」
        cloneproc(..., CLONEPROC_EXEC)
        exec_activate_image(...)
        proc_exec_switch_task(...)     // 自己变成新程序
}
```

要点：

- **用户态不必先 fork 再 exec**：一步完成，父进程拿到子 pid  
- **默认路径**：新进程从一开始就不跑父代码，避免多线程 `fork` 的坑  
- **属性**：可在子进程真正跑起来前改 FD、信号掩码、进程组等  
- **SETEXEC**：语义接近 `execve`（换自己），不是再造一个给用户看的新 pid  

对比：

| | fork + execve | posix_spawn（默认） |
|--|---------------|---------------------|
| 几次 syscall | 至少 2 | 1 |
| 子进程是否短暂跑父代码 | 是 | 否 |
| 装映像 | `exec_activate_image` | 同一套 |

---

## 2. kill（#37）

[`kern_sig.c`](../xnu/bsd/kern/kern_sig.c)：

```c
kill(调用者, pid, signum, posix) {
    if (signum 非法) → EINVAL
    if (pid > 0) {
        p = proc_find(pid)
        找不到：若是僵尸 → 成功(0)；否则 ESRCH
        !cansignal(...) → EPERM
        if (signum) psignal(p, signum)
    } else {
        // 0 / -1 / 负 pid → 进程组广播，走 killpg1
    }
}
```

要点：

- **入口**：用户态「发信号」的主 syscall  
- **权限**：`cansignal` 决定能不能打这个目标  
- **真正投递**：`psignal`（后面 Day 17 信号处理再展开）  
- **pid 约定**：`>0` 单进程；`0` 本进程组；`-1` 广播；`< -1` 指定进程组  

和 Day 11–12 的关系：子进程退出时内核给父发 **`SIGCHLD`**，也是信号路径；`kill` 是用户主动走同一套投递机制。

---

## 今日对比

| | posix_spawn | kill |
|--|-------------|------|
| 造/换进程？ | 是（默认造新；SETEXEC 换自己） | 否 |
| 主对象 | 新映像 / 新 `proc` | 已有 `proc` + 信号号 |
| 成功后父进程 | 默认继续跑，拿到子 pid | 继续跑 |

---

## 做完打勾

- [ ] 找到 244 / 37  
- [ ] 能说 spawn 默认 = fork1(SPAWN) + activate，不必用户态 fork  
- [ ] 能说 kill → cansignal → psignal  
- [ ] 填好 `notes/daily/day-13.md`

下一步：Day 14 → `pipe` / `fcntl` / `fsync`
