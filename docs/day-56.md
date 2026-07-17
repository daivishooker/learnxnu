# 第五十六天（Day 56）正文

学这两个：**`fchmodat` / `fchownat`**  
源码：`xnu/` = **xnu-12377.121.6**

继续 `*at`：相对目录 FD **改权限位**与**改属主/属组**。Day 44 的 `chmod`/`chown` 其实已经汇入这两条 internal。

生活类比：

1. `fchmodat`：站在某间房间（dirfd），改某个抽屉的门锁规则  
2. `fchownat`：站在同一间房间，改这个抽屉归谁、属哪个组  

---

## 今天目标

1. 找到编号 **467 / 468**  
2. 理解 `fchmodat`：`fchmodat_internal` → `chmodat` → `chmod_vnode` → `vnode_setattr(va_mode)`  
3. 理解 `fchownat`：`fchownat_internal` → `vn_chown_internal` → `vnode_setattr(va_uid/va_gid)`  
4. 能说：`chmod`/`chown`/`lchown` 都是 `*at(AT_FDCWD, …)` 的特化  

笔记：[`notes/daily/day-56.md`](../notes/daily/day-56.md)  
分析：[`notes/daily/day-56-analysis.md`](../notes/daily/day-56-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| fchmodat | **467** | 相对 dirfd 改权限位（mode） |
| fchownat | **468** | 相对 dirfd 改 uid / gid |

---

## 1. fchmodat（#467）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
chmod(path, mode)
  = fchmodat_internal(AT_FDCWD, path, mode, flag=0, ...)

fchmodat(fd, path, mode, flag)
  = fchmodat_internal(fd, path, mode, flag, ...)

fchmodat_internal:
  VATTR_SET(va_mode, mode & ALLPERMS)
  → chmodat → nameiat(LOOKUP, OP_SETATTR, fd)
  → chmod_vnode → vnode_setattr
```

要点：

- 与 Day 44 `chmod` **同一条路**，只是起点换成 `dirfd`  
- 支持 `AT_SYMLINK_NOFOLLOW` / `AT_RESOLVE_BENEATH` / `AT_UNIQUE` 等  
- 已打开的文件用 `fchmod(fd, …)`（走 FD → vnode，不经路径）  

---

## 2. fchownat（#468）

```c
chown(path, uid, gid)
  = fchownat_internal(AT_FDCWD, path, uid, gid, flag=0, ...)

lchown(path, uid, gid)
  = fchownat_internal(AT_FDCWD, path, uid, gid, AT_SYMLINK_NOFOLLOW, ...)

fchownat(fd, path, uid, gid, flag)
  = fchownat_internal(fd, path, uid, gid, flag, ...)

fchownat_internal:
  nameiat(..., fd) → vp
  → vn_chown_internal → vnode_setattr(va_uid / va_gid)
```

要点：

- `lchown` = `fchownat(..., AT_SYMLINK_NOFOLLOW)`，不跟随最后一截 symlink  
- 普通用户通常**不能随意改属主**；改组也有规则  
- `uid`/`gid` 传 `-1` 表示该项不动（与 Day 44 相同）  

对照：

| | 改什么 | 汇入 |
|--|--------|------|
| fchmodat | `va_mode` | `chmodat` → `chmod_vnode` |
| fchownat | `va_uid` / `va_gid` | `vn_chown_internal` |

两者最终都是 **setattr**，不是改文件内容。

`*at` 元数据侧小结：

| 操作 | 调用 |
|------|------|
| 探权限 | faccessat |
| 改 mode | fchmodat |
| 改 owner | fchownat |
| 查 stat | fstatat* |

---

## 用户层 Demo

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    int dirfd;
    int fd;
    struct stat st;

    dirfd = open("/tmp", O_RDONLY | O_DIRECTORY);
    if (dirfd < 0) { perror("open /tmp"); return 1; }

    (void)unlinkat(dirfd, "day56_perm.txt", 0);

    fd = openat(dirfd, "day56_perm.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("openat"); close(dirfd); return 1; }
    close(fd);

    /* Demo A：fchmodat — 改成 0600 */
    if (fchmodat(dirfd, "day56_perm.txt", 0600, 0) != 0) {
        perror("fchmodat");
        close(dirfd);
        return 1;
    }
    if (fstatat(dirfd, "day56_perm.txt", &st, 0) != 0) {
        perror("fstatat");
        close(dirfd);
        return 1;
    }
    printf("fchmodat ok mode=%04o\n", (unsigned)(st.st_mode & 0777));

    /* Demo B：fchownat — 设为自己（通常可成功；改别人要特权） */
    if (fchownat(dirfd, "day56_perm.txt", getuid(), getgid(), 0) != 0) {
        perror("fchownat");
        close(dirfd);
        return 1;
    }
    printf("fchownat ok uid=%d gid=%d\n", (int)getuid(), (int)getgid());

    (void)unlinkat(dirfd, "day56_perm.txt", 0);
    close(dirfd);
    return 0;
}
```

```bash
cc -o day56_demo day56_demo.c && ./day56_demo
```

---

## 做完打勾

- [ ] 找到 467 / 468  
- [ ] 能说 chmod/chown 汇入 f*at_internal(AT_FDCWD)  
- [ ] 能说 lchown ≈ fchownat(..., AT_SYMLINK_NOFOLLOW)  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-56.md`

下一步：Day 57 → `linkat` / `getattrlistat`（#471 / #476）
