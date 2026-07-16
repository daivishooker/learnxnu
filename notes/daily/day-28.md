# Day 28 — 第 4 周查漏补缺

> **正文：** [docs/day-28.md](../../docs/day-28.md)  
> **分析：** [day-28-analysis.md](day-28-analysis.md)

## 重读 A：套接字索引与连接
- 进程 FD → socket；网络地址 → PCB → socket
- listen 开 so_comp；accept 新 fd；connect 用原 fd

## 重读 B：消息路径
- msghdr 说明书 + iovec 正文；堆在 so_rcv；getsockopt 只读

## 重读 C：收尾
- shutdown 半关闭（方向）；close 释放 FD/引用

## 今日对比
- 共同点：都绕着「本地 socket 对象」转
- 最大差异：建连索引 / 数据搬运 / 生命周期收尾
