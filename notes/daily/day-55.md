# Day 55 — mkdirat / faccessat

> **正文：** [docs/day-55.md](../../docs/day-55.md)  
> **分析：** [day-55-analysis.md](day-55-analysis.md)

## mkdirat (#475)
- 入口：`mkdir1at(..., uap->fd)`；`mkdir` 即 `AT_FDCWD` 版
- 一句话：相对目录 FD 创建目录（mode 受 umask）

## faccessat (#466)
- 入口：`faccessat_internal` → `nameiat` → `access1` / `vnode_authorize`
- 一句话：相对目录 FD 探权限；默认 real 身份，`AT_EACCESS` 用 effective

## 今日对比
- 共同点：都从 dirfd 起 nameiat；cwd 版汇入同一 internal
- 最大差异：改命名空间（建目录）vs 只读权限探测
