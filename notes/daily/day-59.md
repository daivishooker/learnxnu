# Day 59 — sendfile / fdatasync / sendto / recvfrom / getdirentries / access_extended

> **正文：** [docs/day-59.md](../../docs/day-59.md)  
> **分析：** [day-59-analysis.md](day-59-analysis.md)

## sendfile (#337)
- 入口：正则文件 + 已连接 SOCK_STREAM → 内核发送
- 一句话：文件内容直送套接字

## fdatasync (#187)
- 入口：`fsync_common(..., MNT_DWAIT)`；fsync 用 `MNT_WAIT`
- 一句话：数据完整性刷盘

## sendto (#133) / recvfrom (#29)
- 入口：`sendit` / `recvit`（与 sendmsg/recvmsg 同族）
- 一句话：带可选对端地址的收发

## getdirentries (#196)
- 入口：`getdirentries_common`（旧布局）；64 版见 Day 37
- 一句话：旧 ABI 列目录

## access_extended (#284)
- 入口：批量 copyin 描述符 → 多次 access1
- 一句话：批量权限探测

## 今日对比
- 共同点：多为「已有 FD/socket」上的操作，少拼路径
- 最大差异：VFS 刷盘/列目录 vs 套接字收发 vs 批量 access
