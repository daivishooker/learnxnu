# 第六十二天（Day 62）正文

学这五个：**`getpgrp` / `setpgid` / `setsid` / `getpgid` / `getsid`**  
源码：`xnu/` = **xnu-12377.121.6**

从「身份凭证」转到**作业控制拓扑**：进程组（process group）与会话（session）。shell 前后台、`Ctrl-C` 打到哪一组，都靠这套。

生活类比：

1. **进程**：一个工人  
2. **进程组**：一个班组（可一起收信号）  
3. **会话**：整趟班车/终端会话（可有一个控制终端）  

---

## 今天目标

1. 找到编号 **81 / 82 / 147 / 151 / 310**  
2. 分清：pid / pgid / sid 三层  
3. 理解 `setsid`：新建会话 + 自己当组长（daemon 常用）  
4. 理解 `setpgid`：把自己或子进程放进某进程组  

笔记：[`notes/daily/day-62.md`](../notes/daily/day-62.md)  
分析：[`notes/daily/day-62-analysis.md`](../notes/daily/day-62-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getpgrp | **81** | 读自己的进程组 ID |
| getpgid | **151** | 读任意 pid 的进程组 ID（0=自己） |
| setpgid | **82** | 设置进程组（作业控制） |
| setsid | **147** | 新建会话并成为会话首领 |
| getsid | **310** | 读会话 ID（会话首领的 pgid；0=自己） |

---

## 1. 三层 ID

```text
session (sid)
  └── process group (pgid)
        └── process (pid)
```

[`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)：

```c
getpgrp()          → p->p_pgrpid
getpgid(pid)       → proc_find → p_pgrpid   // pid==0 用自己
getsid(pid)        → proc_sessionid(...)
```

要点：`getpgrp` ≈ `getpgid(0)`；`getsid` 返回的是会话相关 ID（本树用 `proc_sessionid`）。

---

## 2. setpgid（#82）——调班组

```c
setpgid(pid, pgid) {
    // pid==0 → 自己；pgid==0 → 用目标进程的 pid 当新组号
    // 只能动自己或尚未 exec 的子进程；须同 session
    // 会话首领不能被改组
    enterpgrp(targp, pgid, mksess=0)
}
```

典型用途：shell `fork` 后子进程 `setpgid`，把一条管道里的进程收进同一进程组，便于前后台切换。

---

## 3. setsid（#147）——开新会话

```c
setsid() {
    // 已是组长，或已存在以自己 pid 为号的组 → EPERM
    enterpgrp(p, pid, mksess=1)  // 新建 session + 新建 pgrp
    返回 pid（也是新 sid/pgid）
}
```

`enterpgrp(..., mksess=1)`（[`kern_proc.c`](../xnu/bsd/kern/kern_proc.c)）：

- 新建 `session`，自己当首领  
- 清掉控制终端标志（`P_CONTROLT`）  
- 拷贝旧 session 的 `s_login`（与 Day 61 `getlogin` 相关）  

daemon 经典三步里常有：`fork` → 父退出 → **`setsid`** → 再 `fork`……

---

## 4. 和信号/终端的关系（直觉）

| 概念 | 为啥要有 |
|------|----------|
| 进程组 | `kill(-pgid, sig)` 一类可打整组；终端前台组收 `SIGINT` 等 |
| 会话 | 绑控制终端；挂断时会话收到 `SIGHUP` 等 |

今天只跟到「进出组/会话」的入口，终端 ioctl（`tcsetpgrp` 等）可后补。

---

## 用户层 Demo

```c
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main(void) {
    pid_t pid = getpid();
    pid_t pgid = getpgrp();
    pid_t pgid2 = getpgid(0);
    pid_t sid = getsid(0);
    pid_t c;

    printf("pid=%d getpgrp=%d getpgid(0)=%d getsid(0)=%d\n",
           (int)pid, (int)pgid, (int)pgid2, (int)sid);

    if (pgid != pgid2) {
        fprintf(stderr, "getpgrp != getpgid(0)\n");
        return 1;
    }

    /* 子进程里 setsid：新建会话；成功后已是会话首领，不能再 setpgid */
    c = fork();
    if (c < 0) { perror("fork"); return 1; }
    if (c == 0) {
        if (setsid() < 0) { perror("setsid"); return 1; }
        printf("child setsid ok sid=%d pgid=%d\n",
               (int)getsid(0), (int)getpgrp());
        return 0;
    }
    {
        int st;
        if (waitpid(c, &st, 0) < 0 || !WIFEXITED(st) || WEXITSTATUS(st) != 0) {
            fprintf(stderr, "child failed\n");
            return 1;
        }
    }

    printf("day62 ok\n");
    return 0;
}
```

```bash
cc -o day62_demo day62_demo.c && ./day62_demo
```

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能说 pid / pgid / sid  
- [ ] 能说 setsid 新建会话；setpgid 调组  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-62.md`

下一步：Day 63 → [`umask` / `mlock` 族](day-63.md)
