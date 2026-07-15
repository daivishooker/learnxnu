# Day 05 — read / write / lseek

> **正文：** [docs/day-05.md](../../docs/day-05.md)  
> **分析：** [day-05-analysis.md](day-05-analysis.md)

## read (#3)
- 入口：`sys_generic.c` → `read` → `read_internal` → `readv_internal` → `fo_read`
- 关键：fd→fileproc；用户 buf 打成 UIO_READ；`*retval`=字节数
- 一句话：按当前文件偏移（或下层逻辑）把数据 copyout 到用户缓冲

## write (#4)
- 入口：`write` → `write_internal` → `fo_write`
- 关键：对称的 UIO_WRITE
- 一句话：从用户缓冲 copyin 写出

## lseek (#199)
- 入口：`vfs_syscalls.c` → `lseek`
- 关键：改 `fp->fp_glob->fg_offset`；pipe/tty → ESPIPE
- 一句话：只调整偏移，不搬数据

## 今日对比
- read/write 碰缓冲区 + 多态 `fo_*`；lseek 只改 `fg_offset`
- 普通 read 与 pread：一个用当前偏移，一个带显式 offset（可选了解）
