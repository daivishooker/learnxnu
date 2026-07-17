# 每日系统调用计划（每天 2–3 个）

基于仓库内源码：`xnu/`（**xnu-12377.121.6**）。

节奏：**每天只学 2 或 3 个 syscall**。先跟完共用入口，再按表推进。不要一天啃整张 `sysent`。

---

## 每天固定流程（约 1–2 小时）

对当天每个调用，按同一模板走完：

1. 在 `xnu/bsd/kern/syscalls.master` 找到编号与原型  
2. 找到 handler 实现（通常在 `xnu/bsd/kern/` 或相关子系统）  
3. 画一条最短调用链：用户态 stub → 陷阱 → 分发 → handler → 返回  
4. 标出：参数、`copyin`/`copyout`、用到的 `proc`/`fileproc`/`vnode` 等对象  
5. 若方便：写 10 行 C 调用它，用 `dtruss` 对一下编号  
6. 在 `notes/daily/day-NN.md` 写半页笔记（复制下方模板即可）

### 笔记模板

```markdown
# Day N — syscallA / syscallB [/ syscallC]

## syscallA (#num)
- master 行：
- handler 文件/函数：
- 调用链（5 步以内）：
- 关键对象 / 锁 / copyin：
- 一句话结论：

## 今日对比
- 三者共同点：
- 最大差异：
```

---

## 第 0 天（只做一次）：共用入口

不计入「每天 2–3 个」，但必须先做。

| 任务 | 看哪里 |
|------|--------|
| BSD 表从哪来 | `xnu/bsd/kern/syscalls.master` |
| 用户态 stub | `xnu/libsyscall/` |
| Mach 侧对照（概念即可） | `xnu/osfmk/` 下 trap 相关 |

产出：一张图 —— 用户态 → `svc`/`syscall` → 分发 → `sysent[n].sy_call` → 返回。

---

## 日程表（每天 2–3 个）

### 第 1 周：身份与最简返回（练手感）

| 天 | 数量 | 系统调用 | # | 当天重点 |
|----|------|----------|---|----------|
| Day 1 | 3 | `getpid` / `getppid` / `getuid` | 20 / 39 / 24 | 无参数、只读 `proc` → **正文：[day-01.md](day-01.md)** |
| Day 2 | 3 | `geteuid` / `getgid` / `getegid` | 25 / 47 / 43 | 凭证字段从哪读 → **正文：[day-02.md](day-02.md)** |
| Day 3 | 2 | `issetugid` / `getdtablesize` | 327 / 89 | 安全标志；FD 表大小 → **正文：[day-03.md](day-03.md)** |
| Day 4 | 3 | `open` / `close` / `access` | 5 / 6 / 33 | 路径 → vnode；FD 分配/释放 → **正文：[day-04.md](day-04.md)** |
| Day 5 | 3 | `read` / `write` / `lseek` | 3 / 4 / 199 | `fileproc`、UIO、偏移 → **正文：[day-05.md](day-05.md)** |
| Day 6 | 2 | `dup` / `dup2` | 41 / 90 | FD 表操作 → **正文：[day-06.md](day-06.md)** |
| Day 7 | 3 | `stat64` / `fstat64` / `lstat64` | 338 / 339 / 340 | 元数据；路径 vs FD vs 不跟随链接 → **正文：[day-07.md](day-07.md)** |

**第 1 周验收：** 能独立讲清 `open → read → close` 三条链，并指出 `getpid` 与 `open` 复杂度差在哪。

---

### 第 2 周：路径、目录、进程生命周期

| 天 | 数量 | 系统调用 | # | 当天重点 |
|----|------|----------|---|----------|
| Day 8 | 3 | `chdir` / `fchdir` / getcwd 相关* | 12 / 13 / — | 当前目录；*getcwd 非独立 syscall → **正文：[day-08.md](day-08.md)** |
| Day 9 | 3 | `mkdir` / `rmdir` / `unlink` | 136 / 137 / 10 | 目录项变更 → **正文：[day-09.md](day-09.md)** |
| Day 10 | 2 | `rename` / `link` | 128 / 9 | 命名空间；硬链接 → **正文：[day-10.md](day-10.md)** |
| Day 11 | 3 | `fork` / `vfork` / `wait4` | 2 / 66 / 7 | 进程创建与等待；`proc`/`task` → **正文：[day-11.md](day-11.md)** |
| Day 12 | 2 | `execve` / `exit` | 59 / 1 | 地址空间替换；进程终结 → **正文：[day-12.md](day-12.md)** |
| Day 13 | 2 | `posix_spawn` / `kill` | 244 / 37 | 现代创建进程；信号投递入口 → **正文：[day-13.md](day-13.md)** |
| Day 14 | 3 | `pipe` / `fcntl` / `fsync` | 42 / 92 / 95 | 管道两端；FD 控制；刷盘 → **正文：[day-14.md](day-14.md)** |

**第 2 周验收：** 能画 `fork → execve → wait4` 与 `posix_spawn` 的对比图。

---

### 第 3 周：内存、信号、多路 IO

| 天 | 数量 | 系统调用 | # | 当天重点 |
|----|------|----------|---|----------|
| Day 15 | 3 | `mmap` / `munmap` / `mprotect` | 197 / 73 / 74 | Mach VM 交汇点 → **正文：[day-15.md](day-15.md)** |
| Day 16 | 2 | `msync` / `madvise` | 65 / 75 | 同步与建议 → **正文：[day-16.md](day-16.md)** |
| Day 17 | 3 | `sigaction` / `sigprocmask` / `sigpending` | 46 / 48 / 52 | 信号处理安装与掩码 → **正文：[day-17.md](day-17.md)** |
| Day 18 | 2 | `sigaltstack` / `__pthread_kill` | 53 / 328 | 信号栈；线程定向信号 → **正文：[day-18.md](day-18.md)** |
| Day 19 | 3 | `select` / `poll` / `kevent` | 93 / 230 / 363 | 多路复用三代 → **正文：[day-19.md](day-19.md)** |
| Day 20 | 2 | `kevent64` / `kevent_qos` | 369 / 374 | Darwin 事件口演进 → **正文：[day-20.md](day-20.md)** |
| Day 21 | 3 | `ioctl` / `sysctl` / `getrlimit` | 54 / 202 / 194 | 杂项控制面；别深挖每个 cmd → **正文：[day-21.md](day-21.md)** |

**第 3 周验收：** 能说明 `mmap` 如何接到 `osfmk` VM；能对比 `poll` vs `kevent`。

---

### 第 4 周：套接字与可选加深（仍每天 2–3 个）

| 天 | 数量 | 系统调用 | # | 当天重点 |
|----|------|----------|---|----------|
| Day 22 | 3 | `socket` / `bind` / `listen` | 97 / 104 / 106 | 套接字生命周期前半 → **正文：[day-22.md](day-22.md)** |
| Day 23 | 3 | `accept` / `connect` / `socketpair` | 30 / 98 / 135 | 连接建立；本地双端 → **正文：[day-23.md](day-23.md)** |
| Day 24 | 3 | `sendmsg` / `recvmsg` / `getsockopt` 相关 | 28 / 27 / 118 | 消息路径；选项可略读 → **正文：[day-24.md](day-24.md)** |
| Day 25 | 2 | `shutdown` / `close`（回顾套接字 FD） | 134 / 6 | 半关闭 vs 释放 → **正文：[day-25.md](day-25.md)** |
| Day 26 | 3 | `shm_open` / `shm_unlink` / `mmap`（回顾） | 266 / 267 / 197 | POSIX shm → **正文：[day-26.md](day-26.md)** |
| Day 27 | 2 | `ptrace` / `sysctl`（回顾安全相关） | 26 / 202 | 调试接口边界 → **正文：[day-27.md](day-27.md)** |
| Day 28 | 2–3 | 自选：本周卡住的 2–3 个重读 | — | 查漏补缺日 → **正文：[day-28.md](day-28.md)** |

### 第 5 周：套接字补全与时间/资源（续学）

原 28 天表已走完；从 Day 29 起按同样节奏续学。

| 天 | 数量 | 系统调用 | # | 当天重点 |
|----|------|----------|---|----------|
| Day 29 | 3 | `getsockname` / `getpeername` / `setsockopt` | 32 / 31 / 105 | 查本端/对端；写选项 → **正文：[day-29.md](day-29.md)** |
| Day 30 | 2 | `getrusage` / `gettimeofday` | 117 / 116 | 资源统计与墙钟时间 → **正文：[day-30.md](day-30.md)** |
| Day 31 | 2 | `getpriority` / `setpriority` | 100 / 96 | 调度优先级查询与设置 → **正文：[day-31.md](day-31.md)** |
| Day 32 | 2 | `setrlimit` / `getrlimit`（回顾） | 195 / 194 | 资源上限：改 vs 查 → **正文：[day-32.md](day-32.md)** |
| Day 33 | 1–2 | `sys_flock` [+ fcntl 锁对照] | 131 / — | 文件劝告锁 → **正文：[day-33.md](day-33.md)** |
| Day 34 | 2 | `sync` / `fsync`（回顾） | 36 / 95 | 刷盘：全系统 vs 单 FD → **正文：[day-34.md](day-34.md)** |
| Day 35 | 2 | `statfs64` / `fstatfs64` | 345 / 346 | 文件系统统计 → **正文：[day-35.md](day-35.md)** |
| Day 36 | 1–2 | `getfsstat64` | 347 | 列举各挂载点统计 → **正文：[day-36.md](day-36.md)** |
| Day 37 | 2 | `getdirentries64` / `getattrlist` | 344 / 220 | 目录枚举与批量属性查询 → **正文：[day-37.md](day-37.md)** |
| Day 38 | 2 | `setattrlist` / `fgetattrlist` | 221 / 228 | 写属性与按 FD 查属性 → **正文：[day-38.md](day-38.md)** |
| Day 39 | 2 | `exchangedata` / `copyfile` | 223 / 227 | 原子交换内容与内核侧拷贝 → **正文：[day-39.md](day-39.md)** |
| Day 40 | 2 | `clonefileat` / `fclonefileat` | 462 / 517 | APFS 风格克隆（写时复制） → **正文：[day-40.md](day-40.md)** |
| Day 41 | 2 | `searchfs` / `fsgetpath` | 225 / 427 | 目录树搜索与 fsid/objid → 路径 → **正文：[day-41.md](day-41.md)** |
| Day 42 | 2 | `getxattr` / `setxattr` | 234 / 236 | 扩展属性读写 → **正文：[day-42.md](day-42.md)** |
| Day 43 | 2 | `listxattr` / `removexattr` | 240 / 238 | 列出与删除扩展属性 |

> **约定（Day 36 起强制，Day 1–35 已补）：** 每天正文须含 **「用户层 Demo」** 可编译短例。

---

## 难度提示（别打乱顺序）

```
简单（Day 1–3）
  getpid 族
    ↓
中等（Day 4–10）
  文件 / 路径
    ↓
较难（Day 11–14）
  fork / exec / spawn
    ↓
难（Day 15–21）
  mmap / 信号 / kevent
    ↓
广（Day 22+）
  网络与 shm
```

若某天某个调用太深（如 `ioctl`、`sysctl`）：**只跟主路径到分发点**，具体命令/OID 留到以后专题，仍算完成当天任务。

---

## 与源码的对应关系

| 你要找的 | 位置 |
|----------|------|
| 编号与名字 | `xnu/bsd/kern/syscalls.master` |
| 生成的 sysent | 构建产物 / 同目录生成逻辑说明见 master 文件头 |
| 用户态包装 | `xnu/libsyscall/` |
| 文件/VFS | `xnu/bsd/vfs/`、`xnu/bsd/kern/kern_descrip.c` 等 |
| 进程 | `xnu/bsd/kern/kern_fork.c`、`kern_exec.c` 等 |
| VM | `xnu/osfmk/vm/` + BSD `mmap` 包装 |

编号以你树里的 `syscalls.master` 为准；上表已按 **xnu-12377.121.6** 核对常见项。

---

## 现在就开始

1. 做完 **第 0 天** 共用入口图  
2. 打开 **[Day 1 正文](day-01.md)**：`getpid` / `getppid` / `getuid`  
3. 路径/命名空间后进入 **[Day 11](day-11.md)**：`fork` / `wait4`（进程）  
4. 接着 **[Day 12](day-12.md)**：`execve` / `exit`（换程序与终结）  
5. 再进入 **[Day 13](day-13.md)**：`posix_spawn` / `kill`  
6. 第 2 周收尾 **[Day 14](day-14.md)**：`pipe` / `fcntl` / `fsync`  
7. 第 3 周内存从 **[Day 15](day-15.md)** 开始：`mmap` / `munmap` / `mprotect`  
8. 接着 **[Day 16](day-16.md)**：`msync` / `madvise`  
9. 信号从 **[Day 17](day-17.md)**：`sigaction` / `sigprocmask` / `sigpending`  
10. 接着 **[Day 18](day-18.md)**：`sigaltstack` / `__pthread_kill`  
11. 多路 IO **[Day 19](day-19.md)**：`select` / `poll` / `kevent`  
12. 接着 **[Day 20](day-20.md)**：`kevent64` / `kevent_qos`  
13. 第 3 周收尾 **[Day 21](day-21.md)**：`ioctl` / `sysctl` / `getrlimit`  
14. 第 4 周网络从 **[Day 22](day-22.md)**：`socket` / `bind` / `listen`  
15. 接着 **[Day 23](day-23.md)**：`accept` / `connect` / `socketpair`  
16. 接着 **[Day 24](day-24.md)**：`sendmsg` / `recvmsg` / `getsockopt`  
17. 接着 **[Day 25](day-25.md)**：`shutdown` / `close`  
18. 接着 **[Day 26](day-26.md)**：`shm_open` / `shm_unlink` / `mmap`  
19. 接着 **[Day 27](day-27.md)**：`ptrace` / `sysctl`  
20. 第 4 周收尾 **[Day 28](day-28.md)**：查漏补缺  
21. 第 5 周从 **[Day 29](day-29.md)**：`getsockname` / `getpeername` / `setsockopt`  
22. 接着 **[Day 30](day-30.md)**：`getrusage` / `gettimeofday`  
23. 接着 **[Day 31](day-31.md)**：`getpriority` / `setpriority`  
24. 接着 **[Day 32](day-32.md)**：`setrlimit` / `getrlimit`  
25. 接着 **[Day 33](day-33.md)**：`sys_flock`  
26. 接着 **[Day 34](day-34.md)**：`sync` / `fsync`  
27. 接着 **[Day 35](day-35.md)**：`statfs64` / `fstatfs64`  
28. 接着 **[Day 36](day-36.md)**：`getfsstat64`  
29. 接着 **[Day 37](day-37.md)**：`getdirentries64` / `getattrlist`  
30. 接着 **[Day 38](day-38.md)**：`setattrlist` / `fgetattrlist`  
31. 接着 **[Day 39](day-39.md)**：`exchangedata` / `copyfile`  
32. 接着 **[Day 40](day-40.md)**：`clonefileat` / `fclonefileat`  
33. 接着 **[Day 41](day-41.md)**：`searchfs` / `fsgetpath`  
34. 接着 **[Day 42](day-42.md)**：`getxattr` / `setxattr`  
35. 对照填写 `notes/daily/day-0N.md`  

完成 Day 7 后再进入第 2 周；不要跳周。下一步：**Day 43** → `listxattr` / `removexattr`。
