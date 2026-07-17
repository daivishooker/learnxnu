# learnxnu

学习 Apple XNU 内核的笔记与源码仓库。

## Day 1–37 在这里

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
- 完整每日日程： [docs/DAILY_SYSCALL_PLAN.md](docs/DAILY_SYSCALL_PLAN.md)

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
