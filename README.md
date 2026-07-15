# learnxnu

学习 Apple XNU 内核的笔记与源码仓库。

## 第一天 / 第二天在这里

- **Day 1 正文：** [docs/day-01.md](docs/day-01.md)（`getpid` / `getppid` / `getuid`）
- **Day 1 源码分析：** [notes/daily/day-01-analysis.md](notes/daily/day-01-analysis.md)
- **Day 2 正文：** [docs/day-02.md](docs/day-02.md)（`geteuid` / `getgid` / `getegid`）
- **Day 2 源码分析：** [notes/daily/day-02-analysis.md](notes/daily/day-02-analysis.md)
- 完整每日日程： [docs/DAILY_SYSCALL_PLAN.md](docs/DAILY_SYSCALL_PLAN.md)

若还在看旧分支：请切换到 `main`（内容已同步）。

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
