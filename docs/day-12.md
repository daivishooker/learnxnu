# 第十二天（Day 12）正文

学这两个：**`execve` / `exit`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 11：昨天会**造进程、等进程**；今天学**换程序**和**主动结束**。

经典三件套：`fork → execve → wait4`。`exit` 是子进程（或任何进程）走完生命周期的出口。

---

## 今天目标

1. 找到编号 **59 / 1**  
2. 理解 `execve`：同一 pid 语义下换成新可执行映像（地址空间被替换）  
3. 理解本树实现：会先 `cloneproc(..., CLONEPROC_EXEC)` 再切换  
4. 理解 `exit`：收资源 → 变僵尸 → 通知父进程；**不回到用户态**

笔记：[`notes/daily/day-12.md`](../notes/daily/day-12.md)  
分析：[`notes/daily/day-12-analysis.md`](../notes/daily/day-12-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| execve | **59** | 用新程序替换当前进程映像 |
| exit | **1** | 结束当前进程（变僵尸，等父 `wait*`） |

---

## 1. execve（#59）

[`kern_exec.c`](../xnu/bsd/kern/kern_exec.c)：

```c
execve(...) {
    // 包装成带 MAC 参数的形态
    return __mac_execve(...);
}

__mac_execve(...) {
    填 image_params（路径、argv、envp…）
    cloneproc(old_task, NULL, p, CLONEPROC_EXEC)  // 新 task/proc/thread（先不可见）
    exec_activate_image(imgp)
      → namei 找可执行文件 vnode
      → 试 image activator：Mach-O → Fat → #! 脚本
      → load_machfile 装进新 map；摆好用户栈（argv/env）
    成功：proc_exec_switch_task … 新映像接管该 pid
    失败：返回 errno，旧程序继续跑
}
```

要点：

- **用户视角**：成功则**不返回**到旧代码；失败才带着 errno 回来  
- **pid 通常不变**：还是「这个进程」，只是程序被换掉  
- **实现上**（本树）：先造影子 `proc`/`task`，激活成功后再切换；比「原地拆 map」更干净  
- **三种映像**：Mach-O 可执行文件、Fat（多架构）、`#!` 解释器脚本  

和 Day 11 对照：`fork` 复制一份继续跑同一代码；`execve` 留着进程身份，换成另一份代码。

---

## 2. exit（#1）

[`kern_exit.c`](../xnu/bsd/kern/kern_exit.c)：

```c
exit(p, uap, retval) {          // noreturn
    exit1(p, W_EXITCODE(rval, 0), retval);
    thread_exception_return();  // 不回到用户态
}

exit1 → exit_with_reason
  标记 P_LEXIT，保存 p_xstat
  proc_prepareexit …
  task_terminate_internal(task)
  // 最后一个线程收尾 → proc_exit
  //   孤儿孩子挂到 initproc；自己进 zombproc，状态 SZOMB
  //   给父进程 SIGCHLD
```

要点：

- **大部分资源当场释放**（地址空间、多数 FD…）  
- **`proc` 骨架留下当僵尸**，等父进程 `wait4`（Day 11）  
- 若自己还有活着的孩子：转养给 `launchd`/`init`  
- 用户态看起来像「调用后进程没了」——内核侧是终止路径，不是普通返回

---

## 今日对比

| | execve | exit |
|--|--------|------|
| pid | 通常保留 | 进程结束（变僵尸直到被收） |
| 地址空间 | **换成新程序** | **拆掉** |
| 成功后回到用户态？ | **否**（跑新入口） | **否** |
| 和 Day 11 | fork 后常见下一步 | 之后要靠 wait4 回收 |

---

## 用户层 Demo

子进程 `execve` 替换映像；失败则 `_exit`。父进程等待即可观察。

```c
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    pid_t pid = fork();
    if (pid == 0) {
        char *argv[] = { "/usr/bin/true", NULL };
        char *envp[] = { NULL };
        execve(argv[0], argv, envp);
        _exit(127);
    }
    int st;
    waitpid(pid, &st, 0);
    printf("execve done, status=%d\n", st);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 59 / 1  
- [ ] 能说 execve：路径 → imgact → 换映像  
- [ ] 能说 exit：终结 → 僵尸 → SIGCHLD  
- [ ] 填好 `notes/daily/day-12.md`

下一步：Day 13 → [`posix_spawn` / `kill`](day-13.md)
