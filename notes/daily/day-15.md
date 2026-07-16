# Day 15 — mmap / munmap / mprotect

> **正文：** [docs/day-15.md](../../docs/day-15.md)  
> **分析：** [day-15-analysis.md](day-15-analysis.md)

## mmap (#197)
- 入口：`kern_mman.c` → `mmap` → `mach_vm_map_kernel`
- 文件映射：`fd` → vnode → `ubc_getobject` → VM control
- 一句话：在进程地址空间建映射；匿名或文件；BSD 调 Mach VM

## munmap (#73)
- 入口：`munmap` → `mach_vm_deallocate_kernel`
- 一句话：拆掉一段虚拟地址上的映射

## mprotect (#74)
- 入口：`mprotect` → `mach_vm_protect`
- 一句话：改一段映射的读写执行权限

## 今日对比
- 共同点：都操作当前进程的 `vm_map`，是 BSD↔Mach VM 交汇点
- 最大差异：mmap 建立；munmap 拆除；mprotect 改保护
