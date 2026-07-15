# Day 14 — pipe / fcntl / fsync

> **正文：** [docs/day-14.md](../../docs/day-14.md)  
> **分析：** [day-14-analysis.md](day-14-analysis.md)

## pipe (#42)
- 入口：`sys_pipe.c` → `pipe` → `pipepair_alloc` + 两次 `falloc`
- 一句话：造半双工管道，返回读 FD + 写 FD，ops 为 `pipeops`

## fcntl / sys_fcntl (#92)
- 入口：`kern_descrip.c` → `sys_fcntl` → `sys_fcntl_nocancel` → `switch(cmd)`
- 一句话：对已有 FD 发控制命令（dup、CLOEXEC、flags、锁…）

## fsync (#95)
- 入口：`vfs_syscalls.c` → `fsync` → `fsync_common` → `VNOP_FSYNC`
- 一句话：把打开文件刷到稳定存储（文件完整性，`MNT_WAIT`）

## 今日对比
- 共同点：都围着 FD / 文件描述对象转
- 最大差异：pipe 造通道；fcntl 改 FD 属性；fsync 落盘
