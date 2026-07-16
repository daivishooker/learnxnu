# 源码分析：Day 27（ptrace / sysctl）

基于 `xnu-12377.121.6`。调试与配置接口的安全边界（略读）。

---

## 1. 心智模型

```text
ptrace：
  调试者进程 ──req──→ 内核
                 权限？→ 目标 proc 标 P_LTRACED / 停住 / 读写控

sysctl：
  用户 ──MIB──→ 树节点 handler
                 可读？可写？→ copyout / copyin 改内核状态
```

计划要求：**到分发与门禁即可**，不深挖每个 PT 命令或每个 OID。

---

## 2. ptrace 主路径

[`mach_process.c`](../../xnu/bsd/kern/mach_process.c)：

```
PT_DENY_ATTACH
  若已在被跟踪 → 直接异常退出路径
  否则 SET P_LNOATTACH

PT_TRACE_ME
  标自己 P_LTRACED；父为 tracer（含 MAC check）

PT_ATTACH（及 ATTACHEXC）
  pid < 2 → EPERM
  kauth_authorize_process(KAUTH_PROCESS_CANTRACE, …)
    内部常落到 cantrace：属主/setuid/root、已跟踪、NOATTACH、MAC…
  成功：目标 P_LTRACED，SIGSTOP 等

其它 req（DETACH/CONTINUE/…）
  目标须已被你跟踪且 SSTOP
```

`cantrace` 是「能不能跟」的集中检查，值得点开扫一眼条件列表。

---

## 3. sysctl 回顾

[`kern_newsysctl.c`](../../xnu/bsd/kern/kern_newsysctl.c)：

```
copyin name[namelen]
sysctl_create_user_req
userland_sysctl → 查找 + handler
回写 oldlen
```

安全点：handler / 注册标志决定谁能读、谁能写；今天不枚举节点。

---

## 4. 和前几天控制面对照

| 接口 | Day | 门禁直觉 |
|------|-----|----------|
| ioctl | 21 | 对象实现 + 权限 |
| sysctl | 21/27 | 节点策略 |
| ptrace | 27 | 进程调试策略（最「对人对进程」） |
| getsockopt | 24 | socket 选项级 |

---

## 5. 建议点开的文件

1. `syscalls.master` — 26 / 202  
2. `mach_process.c` — `ptrace` 开头、`PT_ATTACH`、`cantrace`  
3. `kern_newsysctl.c` — `sysctl` → `userland_sysctl`  

验收：能讲「为什么随便 attach 会失败」；能说 sysctl 写不是谁都能改。
