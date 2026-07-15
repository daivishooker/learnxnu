# Day 04 — open / close / access

> **正文：** [docs/day-04.md](../../docs/day-04.md)  
> **分析：** [day-04-analysis.md](day-04-analysis.md)

## open (#5)
- 入口：`vfs_syscalls.c` → `open` → `open_nocancel` → `openat_internal` → `open1`
- 关键步骤：`falloc_withinit` 占 FD → `vn_open_auth` 路径/授权/打开 → `*retval = fd`
- 一句话：路径变成 vnode，再挂到新的 fileproc/fd 上

## close (#6)
- 入口：`kern_descrip.c` → `sys_close` → `close_nocancel`
- 关键步骤：按 fd 取 `fileproc` → `fp_close_and_unlock`
- 一句话：不解析路径，只拆 FD 表项

## access (#33)
- 入口：`access` → `faccessat_internal`
- 关键步骤：默认 `kauth_cred_copy_real` → `nameiat` → `access1`
- 一句话：只检查权限，不分配 FD；默认按 real 身份

## 今日对比
- open vs access：都查路径；open 要 FD，access 不要  
- open vs close：创建句柄 vs 销毁句柄  
- 与 Day 2/3：权限看凭证；FD 数量受 nofile 限制  
