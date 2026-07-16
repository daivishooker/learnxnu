# Day 26 — shm_open / shm_unlink / mmap（回顾）

> **正文：** [docs/day-26.md](../../docs/day-26.md)  
> **分析：** [day-26-analysis.md](day-26-analysis.md)

## shm_open (#266)
- 入口：`posix_shm.c` → 名字缓存 + `falloc` + `pshmops`
- 一句话：打开/创建命名共享内存，返回 FD

## shm_unlink (#267)
- 入口：`pshm_cache_search` → `pshm_unlink_internal`
- 一句话：按名字摘链；已打开/已映射可继续用

## mmap (#197) 回顾
- 入口：`kern_mman.c` → `DTYPE_PSXSHM` → `pshm_mmap`
- 一句话：MAP_SHARED 把同一 memory object 映进进程 VA

## 今日对比
- 共同点：都围绕命名共享内存对象的生命周期
- 最大差异：拿 FD / 摘名字 / 映进地址空间
