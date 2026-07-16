# Day 23 — accept / connect / socketpair

> **正文：** [docs/day-23.md](../../docs/day-23.md)  
> **分析：** [day-23-analysis.md](day-23-analysis.md)

## accept (#30)
- 入口：`uipc_syscalls.c` → `accept_nocancel`
- 一句话：从监听队列摘已连接 socket，`falloc` 成新 FD

## connect (#98)
- 入口：`file_socket` → `connectit` → `soconnectlock` → `pru_connect`
- 一句话：给本端 socket 连上对端地址

## socketpair (#135)
- 入口：两个 `socreate` + 两个 `falloc` + `soconnect2`
- 一句话：一次创建一对已互连的 socket FD

## 今日对比
- 共同点：都围绕「把两端接上」；仍经 socket / FD
- 最大差异：接听取新对象 / 主动拨号 / 本地成对互连
