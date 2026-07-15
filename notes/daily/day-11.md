# Day 11 — fork / vfork / wait4

> **正文：** [docs/day-11.md](../../docs/day-11.md)  
> **分析：** [day-11-analysis.md](day-11-analysis.md)

## fork (#2)
- 入口：`kern_fork.c` → `fork` → `fork1` → `cloneproc`
- 一句话：复制出新 proc/task；父返回子 pid，子返回 0；内存多为 COW

## wait4 (#7)
- 入口：`kern_exit.c` → `wait4` → `wait4_nocancel`
- 一句话：等待匹配的子进程（常为僵尸），取退出状态并回收

## vfork (#66)
- 经典：共享地址空间直到 exec/exit，父阻塞
- 本树：可能受 `CONFIG_VFORK` 影响；现代多用 `posix_spawn`
- 一句话：历史优化手段，今天先懂语义即可

## 今日对比
- fork 创建；wait4 回收；vfork 是受限/历史形态的创建
