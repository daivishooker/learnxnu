# Day 08 — chdir / fchdir（兼 getcwd）

> **正文：** [docs/day-08.md](../../docs/day-08.md)  
> **分析：** [day-08-analysis.md](day-08-analysis.md)

## chdir (#12)
- 入口：`sys_chdir` → `common_chdir` → `chdir_internal` → `change_dir`
- 结果：`p->p_fd.fd_cdir = 新目录 vnode`
- 一句话：用路径切换进程当前工作目录

## fchdir (#13)
- 入口：`sys_fchdir` → `fchdir`
- 结果：同样更新 `fd_cdir`；要求 fd 是目录
- 一句话：用已打开的目录 fd 切换 cwd

## getcwd
- **不是**本树 `syscalls.master` 的独立 syscall
- 用户态常借 `fcntl(F_GETPATH, …)` 等从目录/fd 反查路径字符串
- 一句话：内核记 vnode；路径字符串是另查出来的

## 今日对比
- chdir vs fchdir：路径 vs fd，目标都是换 `fd_cdir`
- 与 Day 4：相对路径/`AT_FDCWD` 依赖这个 cwd vnode
