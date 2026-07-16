# Day 29 — getsockname / getpeername / setsockopt

> **正文：** [docs/day-29.md](../../docs/day-29.md)  
> **分析：** [day-29-analysis.md](day-29-analysis.md)

## getsockname (#32)
- 入口：`file_socket` → `pru_sockaddr` → copyout
- 一句话：取本端 sockaddr

## getpeername (#31)
- 入口：需已连接 → `pru_peeraddr` → copyout
- 一句话：取对端 sockaddr

## setsockopt (#105)
- 入口：`SOPT_SET` → `sosetoptlock`（与 getsockopt 对称）
- 一句话：改 socket 选项（略读分发）

## 今日对比
- 共同点：都经 socket FD；查地址或改属性
- 最大差异：本端地址 / 对端地址 / 写选项
