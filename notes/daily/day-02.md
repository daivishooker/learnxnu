# Day 02 — geteuid / getgid / getegid

> **正文：** [docs/day-02.md](../../docs/day-02.md)  
> **源码分析：** [day-02-analysis.md](day-02-analysis.md)  
> 源码树：`xnu/`（xnu-12377.121.6）

## geteuid (#25)
- master 行：`25 AUE_GETEUID ... { int geteuid(void); }`
- handler：`xnu/bsd/kern/kern_prot.c` → `geteuid()`
- 调用链：stub → 陷阱 → sysent[25] → `kauth_getuid()` → `cr_uid`
- copyin：无
- 一句话：返回 **effective uid**（注意助手名是 `kauth_getuid`，不是 geteuid）

## getgid (#47)
- master 行：`47 AUE_GETGID ... { int getgid(void); }`
- handler：`getgid()` → `kauth_getrgid()` → `cr_rgid`
- 一句话：返回 **real gid**

## getegid (#43)
- master 行：`43 AUE_GETEGID ... { int getegid(void); }`
- handler：`getegid()` → `kauth_getgid()` → `cr_gid`
- 一句话：返回 **effective gid**

## 今日对比（含 Day 1 的 getuid）

| syscall | 助手 | 字段 | 含义 |
|---------|------|------|------|
| getuid | kauth_getruid | cr_ruid | real uid |
| geteuid | kauth_getuid | cr_uid | effective uid |
| getgid | kauth_getrgid | cr_rgid | real gid |
| getegid | kauth_getgid | cr_gid | effective gid |

- 共同点：都走当前线程 `tro_cred`；不读 `proc->p_*` 缓存  
- 最大易混点：函数名里的 `getuid` / `geteuid` 与 kauth 助手命名不完全对称  
