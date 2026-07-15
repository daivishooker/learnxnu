# 第八天（Day 8）正文

学这两个（再加一个「假系统调用」说明）：**`chdir` / `fchdir`**，以及 **`getcwd` 为什么不在 `syscalls.master` 里**。

源码：`xnu/` = **xnu-12377.121.6**  
第 2 周开始：目录与路径命名空间。

---

## 今天目标

1. 找到编号 **12 / 13**  
2. 知道进程 cwd 存在 **`p->p_fd.fd_cdir`**（一个目录 vnode）  
3. 分清：路径改 cwd vs 已打开目录 fd 改 cwd  
4. 搞清：**Darwin/XNU 没有独立的 `getcwd` BSD syscall**；用户态另想办法拿路径字符串

笔记：[`notes/daily/day-08.md`](../notes/daily/day-08.md)  
分析：[`notes/daily/day-08-analysis.md`](../notes/daily/day-08-analysis.md)

---

## 总表

| 名字 | # | 输入 |
|------|---|------|
| chdir | **12** | 路径 `sys_chdir(path)` |
| fchdir | **13** | 目录 fd `sys_fchdir(fd)` |
| getcwd | — | **不是**本树 `syscalls.master` 里的独立项 |

另有 `__pthread_chdir`(#348) / `__pthread_fchdir`(#349)：改**单线程** cwd（可选了解）。

---

## 1. chdir（#12）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
sys_chdir → common_chdir(..., per_thread=0)
  → NDINIT(..., OP_CHDIR, FOLLOW, path)
  → chdir_internal → change_dir (namei 等到目录 vnode)
  → p->p_fd.fd_cdir = 新目录 vnode
  → 释放旧的 fd_cdir
```

要求：路径必须是目录（否则 `ENOTDIR` 等）。

---

## 2. fchdir（#13）

```c
sys_fchdir → fchdir(..., fd, per_thread=false)
  → file_vnode(fd) 得到 vnode
  → 必须 v_type == VDIR
  → vnode_authorize(... SEARCH ...)
  → 处理挂载点上的 root 穿越
  → p->p_fd.fd_cdir = vp
```

和 Day 4 `open` 类似：一个靠路径，一个靠已有 fd；最终改的是**同一个 cwd 槽**。

---

## 3. getcwd：用户态 API，不是这张 syscall 表上的主角

在本仓库的 `syscalls.master` 里**搜不到**独立的 `getcwd`/`__getcwd` 编号。

Darwin 上常见做法（概念）：

- 内核只牢牢记着 cwd 的 **vnode**（`fd_cdir`），不保证随时存一份完整路径字符串  
- 用户态 `getcwd()` 往往通过 **`fcntl(fd, F_GETPATH, buf)`** 一类机制，向内核要某个 fd/目录对应的路径（`F_GETPATH` 定义在 `sys/fcntl.h`，处理在 `kern_descrip.c` 的 fcntl 分支）

所以今天重点是：**改 cwd 用 chdir/fchdir；读路径字符串是另一条路，别在 master 里死找 getcwd。**

---

## 今日对比

| | chdir | fchdir |
|--|-------|--------|
| 输入 | 路径 | 目录 fd |
| 查找 | namei | fileproc → vnode |
| 结果 | 更新 `fd_cdir` | 同左 |
| 典型错误 | ENOENT / ENOTDIR | EBADF / ENOTDIR |

---

## 做完打勾

- [ ] 找到 12 / 13  
- [ ] 知道 cwd = `fd_cdir` vnode  
- [ ] 明白 getcwd 不是本表独立 syscall  
- [ ] 填好 `notes/daily/day-08.md`

下一步：Day 9 → `mkdir` / `rmdir` / `unlink`
