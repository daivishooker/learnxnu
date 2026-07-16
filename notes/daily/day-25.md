# Day 25 — shutdown / close（套接字回顾）

> **正文：** [docs/day-25.md](../../docs/day-25.md)  
> **分析：** [day-25-analysis.md](day-25-analysis.md)

## shutdown (#134)
- 入口：`uipc_syscalls.c` → `soshutdown` → `soshutdownlock`
- 一句话：关掉读/写/双向，不释放 FD

## close (#6)
- 入口：通用 close → `socketops.fo_close` = `soo_close` → `soclose`
- 一句话：释放 FD；最后引用时拆掉 socket

## 今日对比
- 共同点：都作用在已有 socket 上；收尾相关
- 最大差异：半关闭（方向） vs 释放把手（FD/对象生命周期）
