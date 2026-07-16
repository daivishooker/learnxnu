# 第二十七天（Day 27）正文

学这两个：**`ptrace` / `sysctl`（安全相关回顾）**  
源码：`xnu/` = **xnu-12377.121.6**

今天重点不是把每个调试请求或每个 OID 背完，而是看清：**谁能碰谁、系统拿什么卡权限。**

生活类比：

1. `ptrace`：调试器要「接手」另一个进程——内核先查你有没有资格  
2. `sysctl`：问/改系统配置树——很多节点只读，写要特权（Day 21 骨架，今天补安全感）

---

## 今天目标

1. 找到编号 **26 / 202**  
2. 理解 `ptrace`：attach / deny_attach / 操作被跟踪进程的主路径与权限关卡  
3. 回顾 `sysctl`：MIB 树读写 + 节点自身的权限策略  
4. 能说清：调试接口与配置接口都是**强门禁**的控制面  

笔记：[`notes/daily/day-27.md`](../notes/daily/day-27.md)  
分析：[`notes/daily/day-27-analysis.md`](../notes/daily/day-27-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| ptrace | **26** | 进程调试 / 跟踪控制 |
| sysctl | **202** | 读/写内核 sysctl 节点（回顾） |

---

## 1. ptrace（#26）——调试接口，先过安检

[`mach_process.c`](../xnu/bsd/kern/mach_process.c)：

```c
ptrace(req, pid, addr, data) {
    // 几种特殊请求先处理：
    PT_DENY_ATTACH  → 给自己打 P_LNOATTACH（拒绝被 attach）
    PT_TRACE_ME     → 让父进程跟踪自己
    PT_ATTACH       → 去跟踪别人：kauth CANTRACE / MAC 等

    // 禁止搞 kernel / launchd（pid < 2）
    // 其它请求：目标必须已被你跟踪、且已停止
    switch (req) { PT_DETACH / PT_CONTINUE / … }
}
```

权限直觉（`cantrace` / `kauth_authorize_process`）：

| 关卡 | 意思 |
|------|------|
| 不能跟自己 | 无效 |
| 已被跟踪 / `P_LNOATTACH` | 忙或不允许 |
| 属主 / setuid / root | 别人的进程或提权进程常跟不了 |
| MAC（如有） | `mac_proc_check_debug` 再卡一层 |
| pid &lt; 2 | 系统关键进程直接 `EPERM` |

`PT_DENY_ATTACH`：进程自我声明「别 attach 我」；强行碰可能让调试方吃瘪（实现里甚至可对调试方 `SIGSEGV`）。

今天验收：能说「ptrace = 调试控制面 + 多层权限」；不必背每个 `PT_*`。

---

## 2. sysctl（#202）——配置树回顾（安全视角）

Day 21 已走过主路径：

```c
sysctl(name[], namelen, old, oldlenp, new, newlen) {
    copyin MIB
    userland_sysctl(...)   // 找节点 → 读 old / 写 new
}
```

今天补一句边界：

- **读**：很多信息对普通用户开放（如部分 `hw.*`）；敏感项会限  
- **写**：改内核参数通常要特权；节点 handler 自己检查  
- 和 `ptrace` 一样：入口统一，**真正门禁在节点/策略里**

别展开整棵树；记住「MIB → 查找 → handler（带权限）」。

---

## 3. 今日对比（安全控制面）

| | ptrace | sysctl |
|--|--------|--------|
| 作用对象 | 某个**进程** | 系统**配置节点** |
| 危险点 | 读内存、控执行、信号 | 改全局行为/泄敏感信息 |
| 门禁 | kauth / MAC / NOATTACH / 属主 | 节点权限 / root 等 |
| 学习深度 | 跟到 attach 与 cantrace | 回顾分发 + 写要特权 |

```text
两者都是：syscall 很「宽」，内核用策略把危险操作收窄。
```

---

## 用户层 Demo

`ptrace` 在 macOS 上常用于防调试探测；`sysctl` 读进程信息作对照。示例只做只读探测，不 attach 别人。

```c
#include <stdio.h>
#include <sys/sysctl.h>
#include <sys/types.h>
#include <unistd.h>
/* #include <sys/ptrace.h>  — Apple: PT_DENY_ATTACH */

int main(void) {
    /* 可选：ptrace(PT_DENY_ATTACH, 0, 0, 0); */
    int mib[4] = { CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid() };
    struct kinfo_proc kp;
    size_t len = sizeof(kp);
    if (sysctl(mib, 4, &kp, &len, NULL, 0) == 0)
        printf("self pid=%d\n", kp.kp_proc.p_pid);
    else
        perror("sysctl");
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 26 / 202  
- [ ] 能说 ptrace attach 要过权限；DENY_ATTACH 防被跟  
- [ ] 能说 sysctl 是 MIB 树，写多要特权  
- [ ] 能对比：调试门禁 vs 配置门禁  
- [ ] 填好 `notes/daily/day-27.md`

下一步：Day 28 → [查漏补缺](day-28.md)
