# learnxnu

学习 Apple XNU 内核的笔记与源码仓库。

## Day 1–54 在这里

- **Day 1–7（第 1 周）：** 见下方历史条目 / [日程](docs/DAILY_SYSCALL_PLAN.md)
- **Day 1：** [docs/day-01.md](docs/day-01.md) · [分析](notes/daily/day-01-analysis.md)
- **Day 2：** [docs/day-02.md](docs/day-02.md) · [分析](notes/daily/day-02-analysis.md)
- **Day 3：** [docs/day-03.md](docs/day-03.md) · [分析](notes/daily/day-03-analysis.md)
- **Day 4：** [docs/day-04.md](docs/day-04.md) · [分析](notes/daily/day-04-analysis.md)
- **Day 5：** [docs/day-05.md](docs/day-05.md) · [分析](notes/daily/day-05-analysis.md)
- **Day 6：** [docs/day-06.md](docs/day-06.md) · [分析](notes/daily/day-06-analysis.md)
- **Day 7：** [docs/day-07.md](docs/day-07.md) · [分析](notes/daily/day-07-analysis.md)
- **Day 8：** [docs/day-08.md](docs/day-08.md) · [分析](notes/daily/day-08-analysis.md)（`chdir` / `fchdir`，兼 getcwd）
- **Day 9：** [docs/day-09.md](docs/day-09.md) · [分析](notes/daily/day-09-analysis.md)（`mkdir` / `rmdir` / `unlink`）
- **Day 10：** [docs/day-10.md](docs/day-10.md) · [分析](notes/daily/day-10-analysis.md)（`link` / `rename`；硬链 vs 软链）
- **Day 11：** [docs/day-11.md](docs/day-11.md) · [分析](notes/daily/day-11-analysis.md)（`fork` / `vfork` / `wait4`）
- **Day 12：** [docs/day-12.md](docs/day-12.md) · [分析](notes/daily/day-12-analysis.md)（`execve` / `exit`）
- **Day 13：** [docs/day-13.md](docs/day-13.md) · [分析](notes/daily/day-13-analysis.md)（`posix_spawn` / `kill`）
- **Day 14：** [docs/day-14.md](docs/day-14.md) · [分析](notes/daily/day-14-analysis.md)（`pipe` / `fcntl` / `fsync`）
- **Day 15：** [docs/day-15.md](docs/day-15.md) · [分析](notes/daily/day-15-analysis.md)（`mmap` / `munmap` / `mprotect`）
- **Day 16：** [docs/day-16.md](docs/day-16.md) · [分析](notes/daily/day-16-analysis.md)（`msync` / `madvise`）
- **Day 17：** [docs/day-17.md](docs/day-17.md) · [分析](notes/daily/day-17-analysis.md)（`sigaction` / `sigprocmask` / `sigpending`）
- **Day 18：** [docs/day-18.md](docs/day-18.md) · [分析](notes/daily/day-18-analysis.md)（`sigaltstack` / `__pthread_kill`）
- **Day 19：** [docs/day-19.md](docs/day-19.md) · [分析](notes/daily/day-19-analysis.md)（`select` / `poll` / `kevent`）
- **Day 20：** [docs/day-20.md](docs/day-20.md) · [分析](notes/daily/day-20-analysis.md)（`kevent64` / `kevent_qos`）
- **Day 21：** [docs/day-21.md](docs/day-21.md) · [分析](notes/daily/day-21-analysis.md)（`ioctl` / `sysctl` / `getrlimit`）
- **Day 22：** [docs/day-22.md](docs/day-22.md) · [分析](notes/daily/day-22-analysis.md)（`socket` / `bind` / `listen`）
- **Day 23：** [docs/day-23.md](docs/day-23.md) · [分析](notes/daily/day-23-analysis.md)（`accept` / `connect` / `socketpair`）
- **Day 24：** [docs/day-24.md](docs/day-24.md) · [分析](notes/daily/day-24-analysis.md)（`sendmsg` / `recvmsg` / `getsockopt`）
- **Day 25：** [docs/day-25.md](docs/day-25.md) · [分析](notes/daily/day-25-analysis.md)（`shutdown` / `close`）
- **Day 26：** [docs/day-26.md](docs/day-26.md) · [分析](notes/daily/day-26-analysis.md)（`shm_open` / `shm_unlink` / `mmap`）
- **Day 27：** [docs/day-27.md](docs/day-27.md) · [分析](notes/daily/day-27-analysis.md)（`ptrace` / `sysctl`）
- **Day 28：** [docs/day-28.md](docs/day-28.md) · [分析](notes/daily/day-28-analysis.md)（第 4 周查漏补缺）
- **Day 29：** [docs/day-29.md](docs/day-29.md) · [分析](notes/daily/day-29-analysis.md)（`getsockname` / `getpeername` / `setsockopt`）
- **Day 30：** [docs/day-30.md](docs/day-30.md) · [分析](notes/daily/day-30-analysis.md)（`getrusage` / `gettimeofday`）
- **Day 31：** [docs/day-31.md](docs/day-31.md) · [分析](notes/daily/day-31-analysis.md)（`getpriority` / `setpriority`）
- **Day 32：** [docs/day-32.md](docs/day-32.md) · [分析](notes/daily/day-32-analysis.md)（`setrlimit` / `getrlimit`）
- **Day 33：** [docs/day-33.md](docs/day-33.md) · [分析](notes/daily/day-33-analysis.md)（`sys_flock`）
- **Day 34：** [docs/day-34.md](docs/day-34.md) · [分析](notes/daily/day-34-analysis.md)（`sync` / `fsync`）
- **Day 35：** [docs/day-35.md](docs/day-35.md) · [分析](notes/daily/day-35-analysis.md)（`statfs64` / `fstatfs64`）
- **Day 36：** [docs/day-36.md](docs/day-36.md) · [分析](notes/daily/day-36-analysis.md)（`getfsstat64`）
- **Day 37：** [docs/day-37.md](docs/day-37.md) · [分析](notes/daily/day-37-analysis.md)（`getdirentries64` / `getattrlist`）
- **Day 38：** [docs/day-38.md](docs/day-38.md) · [分析](notes/daily/day-38-analysis.md)（`setattrlist` / `fgetattrlist`）
- **Day 39：** [docs/day-39.md](docs/day-39.md) · [分析](notes/daily/day-39-analysis.md)（`exchangedata` / `copyfile`）
- **Day 40：** [docs/day-40.md](docs/day-40.md) · [分析](notes/daily/day-40-analysis.md)（`clonefileat` / `fclonefileat`）
- **Day 41：** [docs/day-41.md](docs/day-41.md) · [分析](notes/daily/day-41-analysis.md)（`searchfs` / `fsgetpath`）
- **Day 42：** [docs/day-42.md](docs/day-42.md) · [分析](notes/daily/day-42-analysis.md)（`getxattr` / `setxattr`）
- **Day 43：** [docs/day-43.md](docs/day-43.md) · [分析](notes/daily/day-43-analysis.md)（`listxattr` / `removexattr`）
- **Day 44：** [docs/day-44.md](docs/day-44.md) · [分析](notes/daily/day-44-analysis.md)（`chmod` / `chown`）
- **Day 45：** [docs/day-45.md](docs/day-45.md) · [分析](notes/daily/day-45-analysis.md)（`utimes` / `futimes`）
- **Day 46：** [docs/day-46.md](docs/day-46.md) · [分析](notes/daily/day-46-analysis.md)（`truncate` / `ftruncate`）
- **Day 47：** [docs/day-47.md](docs/day-47.md) · [分析](notes/daily/day-47-analysis.md)（`pathconf` / `fpathconf`）
- **Day 48：** [docs/day-48.md](docs/day-48.md) · [分析](notes/daily/day-48-analysis.md)（`readlink` / `readlinkat`）
- **Day 49：** [docs/day-49.md](docs/day-49.md) · [分析](notes/daily/day-49-analysis.md)（`symlink` / `symlinkat`）
- **Day 50：** [docs/day-50.md](docs/day-50.md) · [分析](notes/daily/day-50-analysis.md)（`mknod` / `mkfifo`）
- **Day 51：** [docs/day-51.md](docs/day-51.md) · [分析](notes/daily/day-51-analysis.md)（`chflags` / `fchflags`）
- **Day 52：** [docs/day-52.md](docs/day-52.md) · [分析](notes/daily/day-52-analysis.md)（`getattrlistbulk` / `fsctl`）
- **Day 53：** [docs/day-53.md](docs/day-53.md) · [分析](notes/daily/day-53-analysis.md)（`openat` / `fstatat64`）
- **Day 54：** [docs/day-54.md](docs/day-54.md) · [分析](notes/daily/day-54-analysis.md)（`renameat` / `unlinkat`）
- **Day 55：** [docs/day-55.md](docs/day-55.md) · [分析](notes/daily/day-55-analysis.md)（`mkdirat` / `faccessat`）
- **Day 56：** [docs/day-56.md](docs/day-56.md) · [分析](notes/daily/day-56-analysis.md)（`fchmodat` / `fchownat`）
- **Day 57：** [docs/day-57.md](docs/day-57.md) · [分析](notes/daily/day-57-analysis.md)（`*at` 扫尾：linkat / getattrlistat / … / mknodat）
- **Day 58：** [docs/day-58.md](docs/day-58.md) · [分析](notes/daily/day-58-analysis.md)（`f*xattr` / `fsetattrlist` / `getdirentriesattr`）
- **Day 59：** [docs/day-59.md](docs/day-59.md) · [分析](notes/daily/day-59-analysis.md)（`sendfile` / `fdatasync` / `sendto` / `recvfrom` / …）
- **Day 60：** [docs/day-60.md](docs/day-60.md) · [分析](notes/daily/day-60-analysis.md)（`setuid` / `seteuid` / `setreuid` 与 gid 对称三项）
- **Day 61：** [docs/day-61.md](docs/day-61.md) · [分析](notes/daily/day-61-analysis.md)（`getgroups` / `setgroups` / `initgroups` / `getlogin` / `setlogin` / `chroot`）
- **Day 62：** [docs/day-62.md](docs/day-62.md) · [分析](notes/daily/day-62-analysis.md)（`getpgrp` / `setpgid` / `setsid` / `getpgid` / `getsid`）
- **Day 63：** [docs/day-63.md](docs/day-63.md) · [分析](notes/daily/day-63-analysis.md)（`umask` / `mlock` / `munlock` / `mlockall` / `munlockall`）
- **Day 64：** [docs/day-64.md](docs/day-64.md) · [分析](notes/daily/day-64-analysis.md)（`revoke` / `acct` / `gethostuuid` / `minherit` / `swapon`）
- **Day 65：** [docs/day-65.md](docs/day-65.md) · [分析](notes/daily/day-65-analysis.md)（`proc_info` / `csops` / `workq_*`）
- **Day 66：** [docs/day-66.md](docs/day-66.md) · [分析](notes/daily/day-66-analysis.md)（`thread_selfid` / `ledger` / `csrctl` / `ulock_*`；标 BSD/Mach）
- **Day 67：** [docs/day-67.md](docs/day-67.md) · [分析](notes/daily/day-67-analysis.md)（`psynch_*` mutex/cond；BSD→Mach）
- **Day 68：** [docs/day-68.md](docs/day-68.md) · [分析](notes/daily/day-68-analysis.md)（`psynch_rw_*`；BSD→Mach，upgrade/downgrade stub）
- **Day 69：** [docs/day-69.md](docs/day-69.md) · [分析](notes/daily/day-69-analysis.md)（psynch 扫尾 + `bsdthread_create` / `terminate`）
- **Day 70：** [docs/day-70.md](docs/day-70.md) · [分析](notes/daily/day-70-analysis.md)（`bsdthread_register` / `ctl` + pthread 取消）
- **Day 71：** [docs/day-71.md](docs/day-71.md) · [分析](notes/daily/day-71-analysis.md)（`__semwait_signal` / 策略 / settid·gettid）
- 完整每日日程： [docs/DAILY_SYSCALL_PLAN.md](docs/DAILY_SYSCALL_PLAN.md)
- **剩余 BSD syscall 地图（分组 + 安全优先）：** [docs/REMAINING_SYSCALLS.md](docs/REMAINING_SYSCALLS.md)
- **Mach trap 地图（须单独记账）：** [docs/MACH_TRAPS.md](docs/MACH_TRAPS.md)
- **系统调用安全白皮书（全部 BSD + Mach，SEC 标记 + Demo）：** [docs/SYSCALL_SECURITY_WHITEPAPER.md](docs/SYSCALL_SECURITY_WHITEPAPER.md) · [demos/whitepaper/](demos/whitepaper/)
- **LeoCounter 学习看板（独立线）：** [docs/leocounter/](docs/leocounter/) · 源码 [`projects/leocounter/`](projects/leocounter/)

## XNU 源码（已放入本仓库）

目录 [`xnu/`](xnu/) 是当前最新已发布标签的一份拷贝：

| 项目 | 内容 |
|------|------|
| 版本 | **xnu-12377.121.6** |
| 来源 | [apple-oss-distributions/xnu](https://github.com/apple-oss-distributions/xnu) |
| 说明 | [xnu/SOURCE.md](xnu/SOURCE.md) |
| 许可证 | [xnu/APPLE_LICENSE](xnu/APPLE_LICENSE)（APSL） |

系统调用入口：

- `xnu/bsd/kern/syscalls.master`
- `xnu/libsyscall/`
- `xnu/osfmk/`（Mach traps / 内核入口）

## 目录

```
xnu/                 # 上游 XNU 源码拷贝
docs/                # 学习计划
notes/daily/         # 每日 syscall 笔记
```
