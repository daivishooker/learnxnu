# 第四天（Day 4）正文

学这三个：**`open` / `close` / `access`**  
源码：`xnu/` = **xnu-12377.121.6**

前三天几乎都是「无参数只读查询」。今天第一次认真碰：**用户路径字符串、vnode、FD 分配/释放**。

---

## 今天目标

1. 找到编号 **5 / 6 / 33**  
2. 能画出 `open`：路径 → 查名 → 授权 → 分配 FD → 返回 fd  
3. 知道 `close` 如何按 fd 找到 `fileproc` 并关掉  
4. 知道 `access` 默认按 **real** 身份检查（不是 effective）

笔记：[`notes/daily/day-04.md`](../notes/daily/day-04.md)  
分析：[`notes/daily/day-04-analysis.md`](../notes/daily/day-04-analysis.md)

---

## 总表

| 名字 | # | master |
|------|---|--------|
| open | **5** | `open(path, flags, mode)` |
| close | **6** | `sys_close(fd)` |
| access | **33** | `access(path, flags)` |

---

## 1. open（#5）

入口 [`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
open(...) {
    __pthread_testcancel(1);
    return open_nocancel(...);
}
open_nocancel(...) {
    return openat_internal(..., AT_FDCWD, ...);
}
```

核心落在 `open1()`（同文件）：

1. **`falloc_withinit`** — 先在进程 FD 表里占一个槽（受 Day 3 的 nofile 限制）  
2. **`vn_open_auth`** — 内部会 `namei` 解析路径得到 `vnode`，并做权限/打开  
3. 把 vnode 挂到 `fileproc`，`*retval = fd`  
4. 失败则 `fp_free` 退回已占 FD

最短链：

```
open → open_nocancel → openat_internal → open1
     → falloc（占 FD）
     → vn_open_auth（路径→vnode+授权）
     → *retval = fd
```

用户 `path` 会经 namei/`copyinstr` 进内核 —— **今天起有真实的跨边界字符串拷贝**。

---

## 2. close（#6）

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c)：

```c
sys_close(p, uap, ...) {
    __pthread_testcancel(1);
    return close_nocancel(p, current_cached_proc_cred(p), uap->fd);
}
close_nocancel(...) {
    proc_fdlock(p);
    fp = fp_get_noref_locked(p, fd);  // 坏 fd → EBADF
    ...
    return fp_close_and_unlock(p, p_cred, fd, fp, 0);
}
```

要点：

- 参数是 **int fd**，不再解析路径  
- 锁住 FD 表，取出 `fileproc`，再关闭（含 guard 检查）  
- 成功时通常不往 `*retval` 塞有意义数据，靠 `return 0` / errno

---

## 3. access（#33）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
access(...) {
    return faccessat_internal(..., AT_FDCWD, path, flags, 0, ...);
}
```

`faccessat_internal` 关键点：

1. **默认用 real 凭证**做检查（`kauth_cred_copy_real`），除非带 `AT_EACCESS`  
2. `nameiat` 解析路径  
3. `access1(vnode, …)` 做实际权限探测  
4. **不分配 FD** —— 只回答「能不能」

这和 Day 2 的 real vs effective 直接相关。

---

## 今日对比

| | open | close | access |
|--|------|-------|--------|
| 输入 | 路径+flags+mode | fd | 路径+amode |
| 核心对象 | vnode + fileproc | fileproc | vnode |
| 是否占 FD | 是 | 释放 FD | 否 |
| 典型错误 | ENOENT/EACCES/EMFILE | EBADF | ENOENT/EACCES |

---

## 做完打勾

- [ ] 找到 5 / 6 / 33  
- [ ] 能口述 open1 里「先 falloc 再 vn_open_auth」  
- [ ] 知道 access 默认查 real 身份  
- [ ] 填好 `notes/daily/day-04.md`

下一步：Day 5 → `read` / `write` / `lseek`
