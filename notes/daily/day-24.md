# Day 24 — sendmsg / recvmsg / getsockopt

> **正文：** [docs/day-24.md](../../docs/day-24.md)  
> **分析：** [day-24-analysis.md](day-24-analysis.md)

## sendmsg (#28)
- 入口：`uipc_syscalls.c` → `sendmsg_nocancel` → `sendit` → `pru_sosend`
- 一句话：按 msghdr 从本地 socket 发出（可带地址/control）

## recvmsg (#27)
- 入口：`recvmsg_nocancel` → `recvit` → `pru_soreceive`
- 一句话：按 msghdr 从本地 socket 接收（可带回地址/control）

## getsockopt (#118)
- 入口：`file_socket` → `sogetoptlock`
- 一句话：按 level/name 读 socket 选项（略读）

## 今日对比
- 共同点：都经 socket FD；收发是数据面，getsockopt 是控制面
- 最大差异：消息接口 vs 选项查询
