# 第五十七天（Day 57）正文

学这六个：**`linkat` / `getattrlistat` / `setattrlistat` / `renameatx_np` / `mkfifoat` / `mknodat`**  
源码：`xnu/` = **xnu-12377.121.6**

从今天起节奏改为 **每天 5–10 个**：把同族/`*at` 尾巴一次收完，不再每天只啃两个。

今天主题：**扫尾 `*at` 家族**——硬链接、attrlist 的 dirfd 版、带 flags 的 rename、以及 Day 50 的 dirfd 版特殊节点。

生活类比（都站在「某间房间」dirfd 里操作）：

1. `linkat`：给同一个抽屉再挂一块门牌  
2. `getattrlistat` / `setattrlistat`：按菜单查/改属性（Day 37/38 的 dirfd 版）  
3. `renameatx_np`：搬家时多几个开关（独占、交换……）  
4. `mkfifoat` / `mknodat`：在房间里放水管 / 设备门牌  

---

## 今天目标

1. 找到编号 **471 / 476 / 524 / 488 / 553 / 554**  
2. 能说：旧 cwd API 多半是 `*at(AT_FDCWD, …)`  
3. 能画一张 `*at` 全家简表（53–57）  
4. 跑通 Demo（`linkat` + `mkfifoat`）  

笔记：[`notes/daily/day-57.md`](../notes/daily/day-57.md)  
分析：[`notes/daily/day-57-analysis.md`](../notes/daily/day-57-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| linkat | **471** | 相对 dirfd 建硬链接（双 dirfd） |
| getattrlistat | **476** | 相对 dirfd 的 `getattrlist` |
| setattrlistat | **524** | 相对 dirfd 的 `setattrlist` |
| renameatx_np | **488** | 带 flags 的 `renameat`（EXCL/SWAP 等） |
| mkfifoat | **553** | 相对 dirfd 建 FIFO |
| mknodat | **554** | 相对 dirfd 建字符/块设备（特权） |

---

## 1. linkat（#471）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
link(path, link)
  = linkat_internal(AT_FDCWD, path, AT_FDCWD, link, AT_SYMLINK_FOLLOW, ...)

linkat(fd1, path, fd2, link, flag)
  = linkat_internal(fd1, path, fd2, link, flag, ...)

linkat_internal:
  nameiat(LOOKUP, path, fd1) → 源 vnode vp
  nameiat(CREATE, link, fd2) → 目标父目录
  （目录硬链默认禁；有 MNTK_DIR_HARDLINKS 等例外）
  → VNOP_LINK / 复合 link
```

要点：源与新名可各带 dirfd；默认**不**跟随源路径最后 symlink（POSIX：`AT_SYMLINK_FOLLOW` 才跟随）。`link()` 则带 `AT_SYMLINK_FOLLOW`。

---

## 2. getattrlistat（#476） / setattrlistat（#524）

[`vfs_attrlist.c`](../xnu/bsd/vfs/vfs_attrlist.c)：

```c
getattrlist(...)  = getattrlistat_internal(..., AT_FDCWD)
getattrlistat(...) = getattrlistat_internal(..., fd)
  nameiat(LOOKUP, path, fd) → getattrlist_internal(vp, ...)

setattrlistat(...)   // 同模式：dirfd + 路径 → setattr 位图路径
```

要点：与 Day 37/38 同一套 attrlist「点菜」模型，只是查找从 `dirfd` 起。options 可带 `FSOPT_NOFOLLOW` / `FSOPT_RESOLVE_BENEATH` 等。

---

## 3. renameatx_np（#488）

```c
renameat(...)     = renameat_internal(..., flags=0)
renameatx_np(...) = renameat_internal(..., uap->flags)
```

常见 flags（互斥注意）：

| flag | 含义 |
|------|------|
| `RENAME_EXCL` | 目标已存在则失败（不覆盖） |
| `RENAME_SWAP` | 原子交换两个已存在名字（与 EXCL 互斥） |
| `RENAME_SECLUDE` | 隔离/隐藏类语义（FS 相关） |
| `RENAME_NOFOLLOW_ANY` / `RENAME_RESOLVE_BENEATH` | 解析策略 |

本质仍是 Day 54 的 `renameat_internal`，多了策略开关。

---

## 4. mkfifoat（#553） / mknodat（#554）

```c
mkfifo(...)  = mkfifo1(..., AT_FDCWD)
mkfifoat(...) = mkfifo1(..., fd)

mknod(...)   = mknodat_internal(..., AT_FDCWD)
mknodat(...) = mknodat_internal(..., fd)
  S_IFIFO → 转 mkfifo1
  否则需 suser；S_IFCHR/S_IFBLK → vn_create
```

与 Day 50 同语义，多了 dirfd。`mknodat` 创建设备节点仍要特权。

---

## `*at` 家族简表（Day 53–57）

| 操作 | 调用 | # |
|------|------|---|
| 打开 | openat | 463 |
| 探权限 | faccessat | 466 |
| 改 mode / owner | fchmodat / fchownat | 467 / 468 |
| stat | fstatat64 | 470 |
| 硬链接 | linkat | 471 |
| 删除 | unlinkat | 472 |
| 读/建 symlink | readlinkat / symlinkat | 473 / 474 |
| 建目录 | mkdirat | 475 |
| attrlist | getattrlistat / setattrlistat | 476 / 524 |
| 改名（flags） | renameat / renameatx_np | 465 / 488 |
| FIFO / 设备 | mkfifoat / mknodat | 553 / 554 |

共性：**dirfd 钉起点**；安全相关再叠加 `AT_RESOLVE_BENEATH` / `NOFOLLOW` 等。

---

## 用户层 Demo

> `getattrlistat` / `renameatx_np` / `mknodat` 偏 Darwin 或需特权；Demo 用可移植的 `linkat` + `mkfifoat`。

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

    (void)unlinkat(dirfd, "day57_a.txt", 0);
    (void)unlinkat(dirfd, "day57_b.txt", 0);
    (void)unlinkat(dirfd, "day57_fifo", 0);

    fd = openat(dirfd, "day57_a.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("openat"); close(dirfd); return 1; }
    (void)write(fd, "hi\n", 3);
    close(fd);

    /* Demo A：linkat — 同目录硬链接 */
    if (linkat(dirfd, "day57_a.txt", dirfd, "day57_b.txt", 0) != 0) {
        perror("linkat");
        close(dirfd);
        return 1;
    }
    if (fstatat(dirfd, "day57_b.txt", &st, 0) != 0) {
        perror("fstatat");
        close(dirfd);
        return 1;
    }
    printf("linkat ok nlink=%lu\n", (unsigned long)st.st_nlink);

    /* Demo B：mkfifoat — 相对 /tmp 建 FIFO */
    if (mkfifoat(dirfd, "day57_fifo", 0644) != 0) {
        perror("mkfifoat");
        close(dirfd);
        return 1;
    }
    if (fstatat(dirfd, "day57_fifo", &st, 0) != 0 || !S_ISFIFO(st.st_mode)) {
        perror("fstatat fifo");
        close(dirfd);
        return 1;
    }
    printf("mkfifoat ok\n");

    (void)unlinkat(dirfd, "day57_a.txt", 0);
    (void)unlinkat(dirfd, "day57_b.txt", 0);
    (void)unlinkat(dirfd, "day57_fifo", 0);
    close(dirfd);
    return 0;
}
```

```bash
cc -o day57_demo day57_demo.c && ./day57_demo
```

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能说 link / getattrlist / mkfifo / mknod 如何汇入 *at  
- [ ] 能说 renameatx_np 相对 renameat 多了什么  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-57.md`

下一步：Day 58 → [FD/目录侧属性扫尾](day-58.md)（`f*xattr` / `fsetattrlist` / `getdirentriesattr`）
