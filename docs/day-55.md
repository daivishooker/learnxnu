# 第五十五天（Day 55）正文

学这两个：**`mkdirat` / `faccessat`**  
源码：`xnu/` = **xnu-12377.121.6**

继续 `*at` 家族：相对目录 FD **建目录**，以及相对目录 FD **探权限**（`access` 的 dirfd 版）。

生活类比：

1. `mkdirat`：人已经站在某间房间（dirfd），在里面再隔出一间小房  
2. `faccessat`：站在同一间房间，问「这抽屉我能不能读/写/进？」——默认按**真实身份**问，不是套着有效身份的临时工牌

---

## 今天目标

1. 找到编号 **475 / 466**  
2. 理解 `mkdirat`：`mkdir` / `mkdirat` 都进 `mkdir1at(..., fd)`  
3. 理解 `faccessat`：`access` 也是 `faccessat_internal(AT_FDCWD, …)`  
4. 能说：默认不用 effective uid；要按 euid 查需 `AT_EACCESS`  

笔记：[`notes/daily/day-55.md`](../notes/daily/day-55.md)  
分析：[`notes/daily/day-55-analysis.md`](../notes/daily/day-55-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| mkdirat | **475** | 相对 dirfd 创建目录 |
| faccessat | **466** | 相对 dirfd 探测访问权限（或仅存在性） |

---

## 1. mkdirat（#475）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
mkdir(...) {
    VATTR_SET(&va, va_mode, (mode & ACCESSPERMS) & ~p->p_fd.fd_cmask);
    return mkdir1at(..., path, &va, AT_FDCWD, ...);
}

mkdirat(...) {
    VATTR_SET(&va, va_mode, (mode & ACCESSPERMS) & ~p->p_fd.fd_cmask);
    return mkdir1at(..., path, &va, uap->fd, ...);
}
```

`mkdir1at` 主路径：

```
NDINIT(CREATE, OP_MKDIR, LOCKPARENT | …)
nameiat(..., fd) → 父目录 dvp
若目标已存在 → EEXIST
va_type = VDIR
vn_authorize_mkdir → vn_create（compound mkdir）
```

要点：

- 与 Day 9 `mkdir` **同套逻辑**，只是起点换成 `dirfd`  
- `mode` 仍受进程 **umask**（`fd_cmask`）裁剪  
- 不返回目录 FD；要打开再用 `openat(..., O_DIRECTORY)`  

---

## 2. faccessat（#466）

```c
access(path, amode)
  = faccessat_internal(AT_FDCWD, path, amode, flag=0, ...)

faccessat(fd, path, amode, flag)
  = faccessat_internal(fd, path, amode, flag, ...)
```

`faccessat_internal` 关键点：

1. **默认用 real 凭证**（`kauth_cred_copy_real`）；带 `AT_EACCESS` 才用当前 effective  
2. `nameiat(LOOKUP, OP_ACCESS, …, fd)`；可带 `AT_SYMLINK_NOFOLLOW` / `AT_RESOLVE_BENEATH` / `AT_UNIQUE`  
3. `access1(vp, …)`：把 `R_OK`/`W_OK`/`X_OK` 映射成 `KAUTH_VNODE_*`，再 `vnode_authorize`  
4. `amode == 0`（即 `F_OK`）只验证路径能解析到对象  

要点：

- 这是**探测**，不是打开；成功也不等于随后 `open` 一定成功（TOCTOU）  
- `access` ≈ `faccessat(AT_FDCWD, …, 0)`  

`*at` 小结（Day 53–55）：

| 操作 | 调用 |
|------|------|
| 打开 | openat |
| 查元数据 | fstatat* |
| 改名 | renameat |
| 删除 | unlinkat |
| 建目录 | mkdirat |
| 探权限 | faccessat |

---

## 用户层 Demo

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/stat.h>

int main(void) {
    int dirfd;

    dirfd = open("/tmp", O_RDONLY | O_DIRECTORY);
    if (dirfd < 0) { perror("open /tmp"); return 1; }

    /* 清理上次残留 */
    (void)unlinkat(dirfd, "day55_dir/inner.txt", 0);
    (void)unlinkat(dirfd, "day55_dir", AT_REMOVEDIR);

    /* Demo A：mkdirat — 相对 /tmp 建子目录 */
    if (mkdirat(dirfd, "day55_dir", 0755) != 0) {
        perror("mkdirat");
        close(dirfd);
        return 1;
    }
    printf("mkdirat ok\n");

    /* Demo B：faccessat — 探存在与可写 */
    if (faccessat(dirfd, "day55_dir", F_OK, 0) != 0) {
        perror("faccessat F_OK");
        close(dirfd);
        return 1;
    }
    if (faccessat(dirfd, "day55_dir", W_OK | X_OK, 0) != 0) {
        perror("faccessat W_OK|X_OK");
        close(dirfd);
        return 1;
    }
    printf("faccessat ok\n");

    /* 清理 */
    if (unlinkat(dirfd, "day55_dir", AT_REMOVEDIR) != 0) {
        perror("unlinkat AT_REMOVEDIR");
        close(dirfd);
        return 1;
    }

    close(dirfd);
    return 0;
}
```

```bash
cc -o day55_demo day55_demo.c && ./day55_demo
```

> 说明：Demo 在 Linux 上也可编译跑通（同 POSIX API）。Darwin 上标志与错误码与 XNU 测试更贴近。

---

## 做完打勾

- [ ] 找到 475 / 466  
- [ ] 能说 mkdir / mkdirat 都进 mkdir1at  
- [ ] 能说 access 默认 real；AT_EACCESS 才用 effective  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-55.md`

下一步：Day 56 → `fchmodat` / `fchownat`（#467 / #468）
