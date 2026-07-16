# Day 21 — ioctl / sysctl / getrlimit

> **正文：** [docs/day-21.md](../../docs/day-21.md)  
> **分析：** [day-21-analysis.md](day-21-analysis.md)

## ioctl (#54)
- 入口：`sys_generic.c` → `ioctl` →（通用命令或）`fo_ioctl`
- 一句话：对已打开 FD 按命令码做控制；命令编码带参数大小/方向

## sysctl (#202)
- 入口：`kern_newsysctl.c` → `sysctl` → `userland_sysctl`
- 一句话：按 OID 名字访问内核 sysctl 树，可读可写（视节点）

## getrlimit (#194)
- 入口：`kern_resource.c` → `getrlimit` → `proc_limitget` → copyout
- 一句话：查询当前进程某类资源的 soft/hard 上限

## 今日对比
- 共同点：都是控制/查询面，不是主数据读写路径
- 最大差异：对象分别是 FD、系统树、进程限额
