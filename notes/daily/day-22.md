# Day 22 — socket / bind / listen

> **正文：** [docs/day-22.md](../../docs/day-22.md)  
> **分析：** [day-22-analysis.md](day-22-analysis.md)

## socket (#97)
- 入口：`uipc_syscalls.c` → `socket_common` → `falloc` + `socreate`
- 一句话：创建 socket 对象并挂到新 FD（`socketops`）

## bind (#104)
- 入口：`file_socket` → copyin 地址 → `sobindlock`
- 一句话：给 socket 绑定本地 sockaddr

## listen (#106)
- 入口：`file_socket` → `solisten`
- 一句话：进入监听，设置 backlog（面向连接）

## 今日对比
- 共同点：套接字生命周期前半；都经 socket FD
- 最大差异：造端点 / 绑地址 / 开始听
