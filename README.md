# learnxnu

学习 Apple XNU 内核的笔记与源码仓库。

## 第一天在这里（先点这个）

- **Day 1 正文：** [docs/day-01.md](docs/day-01.md)（`getpid` / `getppid` / `getuid`）
- Day 1 笔记： [notes/daily/day-01.md](notes/daily/day-01.md)
- 完整每日日程： [docs/DAILY_SYSCALL_PLAN.md](docs/DAILY_SYSCALL_PLAN.md)

若 GitHub 打开的是 `main` 还看不到：请切换到分支 `cursor/daily-syscall-plan-a8ed`，或打开 PR https://github.com/daivishooker/learnxnu/pull/3

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
