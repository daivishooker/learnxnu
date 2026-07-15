# Day 06 — dup / dup2

> **正文：** [docs/day-06.md](../../docs/day-06.md)  
> **分析：** [day-06-analysis.md](day-06-analysis.md)

## dup (#41)
- 入口：`kern_descrip.c` → `sys_dup` → `fdalloc` → `finishdup`
- 关键：新 `fileproc` 的 `fp_glob` = 旧的；`fg_ref`
- 一句话：复制 fd 表项，共享同一打开文件状态（含偏移）

## dup2 (#90)
- 入口：`sys_dup2` → `dup2`
- 关键：指定目标 fd；占用则先 close；`from==to` 直接成功；仍 `finishdup`
- 一句话：把 from 精确复制到 to 号

## 今日对比
- 共同点：最终都 `finishdup`，共享 `fileglob`/`fg_offset`
- 差异：dup 自动选号；dup2 指定号并可覆盖已打开目标
- 回扣 Day 5：一个 fd 上 lseek，另一个 dup fd 同步变
