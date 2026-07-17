# Day 57 — linkat / getattrlistat / setattrlistat / renameatx_np / mkfifoat / mknodat

> **正文：** [docs/day-57.md](../../docs/day-57.md)  
> **分析：** [day-57-analysis.md](day-57-analysis.md)

## linkat (#471)
- 入口：`linkat_internal`；双 `nameiat(fd1/fd2)` → LINK
- 一句话：相对目录 FD 建硬链接

## getattrlistat (#476) / setattrlistat (#524)
- 入口：`getattrlistat_internal` / `setattrlistat` → nameiat(dirfd) → 原 attrlist 逻辑
- 一句话：Day 37/38 的 dirfd 版

## renameatx_np (#488)
- 入口：`renameat_internal(..., flags)`；EXCL/SWAP 等
- 一句话：带策略开关的 renameat

## mkfifoat (#553) / mknodat (#554)
- 入口：`mkfifo1(fd)` / `mknodat_internal(fd)`（FIFO 可转交）
- 一句话：Day 50 的 dirfd 版；设备节点仍要特权

## 今日对比
- 共同点：都是 `*at` 扫尾；cwd 版汇入同一 internal
- 最大差异：命名空间增删改名 vs attrlist setattr vs 特殊 vnode 创建
