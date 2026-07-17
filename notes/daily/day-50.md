# Day 50 — mknod / mkfifo

> **正文：** [docs/day-50.md](../../docs/day-50.md)  
> **分析：** [day-50-analysis.md](day-50-analysis.md)

## mknod (#14)
- 入口：`mknodat_internal`；设备需 `suser`；`S_IFIFO` → `mkfifo1`
- 一句话：创建设备节点（或转交创建 FIFO）

## mkfifo (#132)
- 入口：`mkfifo1` → `va_type=VFIFO` → `vn_create`
- 一句话：创建命名管道

## 今日对比
- 共同点：CREATE 父目录 + 新 vnode
- 最大差异：设备要特权且带 rdev；FIFO 是 IPC 通道
