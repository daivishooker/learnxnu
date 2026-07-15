# learnxnu

学习 Apple XNU 内核的笔记与源码仓库。

## Day 1–7 在这里（第 1 周）

- **Day 1：** [docs/day-01.md](docs/day-01.md) · [分析](notes/daily/day-01-analysis.md)（`getpid` / `getppid` / `getuid`）
- **Day 2：** [docs/day-02.md](docs/day-02.md) · [分析](notes/daily/day-02-analysis.md)（`geteuid` / `getgid` / `getegid`）
- **Day 3：** [docs/day-03.md](docs/day-03.md) · [分析](notes/daily/day-03-analysis.md)（`issetugid` / `getdtablesize`）
- **Day 4：** [docs/day-04.md](docs/day-04.md) · [分析](notes/daily/day-04-analysis.md)（`open` / `close` / `access`）
- **Day 5：** [docs/day-05.md](docs/day-05.md) · [分析](notes/daily/day-05-analysis.md)（`read` / `write` / `lseek`）
- **Day 6：** [docs/day-06.md](docs/day-06.md) · [分析](notes/daily/day-06-analysis.md)（`dup` / `dup2`）
- **Day 7：** [docs/day-07.md](docs/day-07.md) · [分析](notes/daily/day-07-analysis.md)（`stat64` / `fstat64` / `lstat64`）
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
