# Day 63 — umask / mlock / munlock / mlockall / munlockall

> **正文：** [docs/day-63.md](../../docs/day-63.md)  
> **分析：** [day-63-analysis.md](day-63-analysis.md)

## umask (#60)
- 入口：读写 `p->p_fd.fd_cmask`；创建时 `mode & ~cmask`
- 一句话：进程创建权限掩码

## mlock / munlock (#203 / #204)
- 入口：`vm_map_wire` / `vm_map_unwire`
- 一句话：把地址范围钉在物理内存 / 解开

## mlockall / munlockall (#324 / #325)
- 本树直接 `ENOSYS`
- 一句话：整空间锁定未实现（BSD 包装）

## 今日对比
- 共同点：都是进程级策略（创建掩码 / 内存常驻）
- 最大差异：VFS 创建权限 vs VM wire
