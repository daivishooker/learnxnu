# 第四十九天（Day 49）正文

学这两个：**`symlink` / `symlinkat`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天用 `readlink` 读路牌；今天**立路牌**——创建符号链接（`VLNK`）。

生活类比：

1. `symlink`：在某个路径挂一块路牌，上面写着目标地址字符串  
2. `symlinkat`：相对某个目录 FD 挂这块路牌  

---

## 今天目标

1. 找到编号 **57 / 474**  
2. 理解共用：`symlinkat_internal` → `copyinstr(目标串)` → `CREATE` 找父目录 → `VNOP_SYMLINK`  
3. 分清参数顺序：**先目标字符串，再链接路径**  
4. 能对比：创建链接 vs `readlink` 读链接；目标文件**不必已存在**  

笔记：[`notes/daily/day-49.md`](../notes/daily/day-49.md)  
分析：[`notes/daily/day-49-analysis.md`](../notes/daily/day-49-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| symlink | **57** | 创建符号链接：`symlink(目标, 链接名)` |
| symlinkat | **474** | 相对 dirfd 创建：`symlinkat(目标, dirfd, 链接名)` |

---

## 共用内部：symlinkat_internal

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
symlinkat_internal(path_data /*目标串*/, fd, link /*新名字*/) {
    copyinstr(path_data) → path          // 路牌上要写的字
    nameiat(CREATE, link, fd) → dvp      // 链接要出现在哪个目录
    若已存在 → EEXIST
    VATTR：类型 VLNK，mode 受 umask
    authorize 父目录 ADD_FILE
    VNOP_SYMLINK(dvp, ..., path)         // 真正创建链接 vnode
}
```

```c
symlink(path, link)     = symlinkat_internal(path, AT_FDCWD, link)
symlinkat(path1, fd, path2) = symlinkat_internal(path1, fd, path2)
```

要点：

- **目标串只是字符串**：内核不要求目标文件此刻存在（可以挂悬空链接）  
- 创建的是新的 **`VLNK` vnode**，不是硬链接（硬链共享 inode；软链另存路径）  
- 链接名已存在 → `EEXIST`  
- 与 Day 48 成对：`symlink` 写入，`readlink` 读出  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    const char *target = "/tmp/day49_may_not_exist_yet";
    const char *link1 = "/tmp/day49_link1";
    const char *link2_name = "day49_link2";
    char buf[256];
    ssize_t n;
    int dirfd;

    unlink(link1);
    unlink("/tmp/day49_link2");

    /* Demo A：symlink — 目标甚至可以还不存在 */
    if (symlink(target, link1) != 0) {
        perror("symlink");
        return 1;
    }
    n = readlink(link1, buf, sizeof(buf) - 1);
    if (n < 0) { perror("readlink"); return 1; }
    buf[n] = '\0';
    printf("symlink => %s\n", buf);

    /* Demo B：symlinkat — 相对 /tmp */
    dirfd = open("/tmp", O_RDONLY);
    if (dirfd < 0) { perror("open"); return 1; }
    if (symlinkat(target, dirfd, link2_name) != 0) {
        perror("symlinkat");
        close(dirfd);
        return 1;
    }
    close(dirfd);
    n = readlink("/tmp/day49_link2", buf, sizeof(buf) - 1);
    if (n < 0) { perror("readlink2"); return 1; }
    buf[n] = '\0';
    printf("symlinkat => %s\n", buf);
    return 0;
}
```

```bash
cc -o day49_demo day49_demo.c && ./day49_demo
```

---

## 做完打勾

- [ ] 找到 57 / 474  
- [ ] 能说 copyinstr 目标串 + CREATE + VNOP_SYMLINK  
- [ ] 能说目标不必存在；与硬链接区别  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-49.md`

下一步：Day 50 → `mknod` / `mkfifo`（#14 / #132）
