# Day 16 — msync / madvise

> **正文：** [docs/day-16.md](../../docs/day-16.md)  
> **分析：** [day-16-analysis.md](day-16-analysis.md)

## msync (#65)
- 入口：`kern_mman.c` → `msync` → `msync_nocancel` → `mach_vm_msync`
- 一句话：同步或失效已 mmap 区间；文件共享映射的“区间版 fsync”

## madvise (#75)
- 入口：`madvise` → `mach_vm_behavior_set`
- 一句话：对映射区间给出访问建议（WILLNEED / DONTNEED / SEQUENTIAL…），多为 advisory

## 今日对比
- 共同点：都操作已映射的 VA 区间，BSD 薄包装进 Mach VM
- 最大差异：msync 要同步/失效；madvise 只建议用法
