# 第四十八天（Day 48）正文

学这两个：**`readlink` / `readlinkat`**  
源码：`xnu/` = **xnu-12377.121.6**

接前面 symlink 讨论：今天专门**读出链接里存的那串目标路径**，不是打开目标文件去读内容。

生活类比：

1. `readlink`：看路牌上写的地址是什么（不跟着走到那栋楼）  
2. `readlinkat`：从某个目录 FD 出发，相对路径去看路牌  

---

## 今天目标

1. 找到编号 **58 / 473**  
2. 理解共用：`readlinkat_internal` → **`NOFOLLOW`** → 必须是 `VLNK` → `VNOP_READLINK`  
3. 能对比：`readlink` vs `open`/`read` 目标文件；vs `ftruncate` 拒绝 symlink  
4. 知道还有 `freadlink`（#551，FD 已是链接本身）  

笔记：[`notes/daily/day-48.md`](../notes/daily/day-48.md)  
分析：[`notes/daily/day-48-analysis.md`](../notes/daily/day-48-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| readlink | **58** | 读路径所指符号链接的目标字符串 |
| readlinkat | **473** | 相对目录 FD 读符号链接目标 |

---

## 共用内部：readlinkat_internal

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
readlinkat_internal(dirfd, path, buf, bufsize) {
    nameiat(dirfd, path, NOFOLLOW) → vp   // 关键：不跟随链接
    if (vp->v_type != VLNK) → EINVAL      // 必须是链接本身
    authorize READ_DATA
    VNOP_READLINK(vp, uio)                // 把目标路径拷进用户 buf
    返回写入字节数（未必加 '\0'）
}
```

```c
readlink(path, buf, count)
  = readlinkat_internal(AT_FDCWD, path, ...)

readlinkat(fd, path, buf, bufsize)
  = readlinkat_internal(fd, path, ...)
```

要点：

- **`NOFOLLOW`**：找到的就是 symlink vnode，不会变成目标文件  
- 读出的是链接里存的**路径字符串**（可能相对、可能绝对）  
- 缓冲**不一定 NUL 结尾**；应用按返回长度使用  
- 对普通文件调 → `EINVAL`（不是 VLNK）  

和前面对照：

| 操作 | 作用在谁 |
|------|----------|
| `readlink(link)` | 链接本身 → 读出路牌文字 |
| `open(link)` 默认跟随 | 目标文件 |
| `ftruncate` 若 FD 是 link | 拒绝（你之前问过） |

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(void) {
    const char *target = "/tmp/day48_target.txt";
    const char *linkpath = "/tmp/day48_link";
    char buf[256];
    ssize_t n;
    int dirfd;

    /* 准备：文件 + 符号链接 */
    int fd = open(target, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open target"); return 1; }
    (void)write(fd, "hello\n", 6);
    close(fd);
    unlink(linkpath);
    if (symlink(target, linkpath) != 0) {
        perror("symlink");
        return 1;
    }

    /* Demo A：readlink */
    n = readlink(linkpath, buf, sizeof(buf) - 1);
    if (n < 0) { perror("readlink"); return 1; }
    buf[n] = '\0';
    printf("readlink => %s\n", buf);

    /* Demo B：readlinkat — 相对 /tmp 目录 FD */
    dirfd = open("/tmp", O_RDONLY);
    if (dirfd < 0) { perror("open /tmp"); return 1; }
    n = readlinkat(dirfd, "day48_link", buf, sizeof(buf) - 1);
    close(dirfd);
    if (n < 0) { perror("readlinkat"); return 1; }
    buf[n] = '\0';
    printf("readlinkat => %s\n", buf);
    return 0;
}
```

```bash
cc -o day48_demo day48_demo.c && ./day48_demo
```

---

## 做完打勾

- [ ] 找到 58 / 473  
- [ ] 能说 NOFOLLOW + VLNK + VNOP_READLINK  
- [ ] 能区分读链接目标字符串 vs 读目标文件内容  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-48.md`

下一步：Day 49 → `symlink` / `symlinkat`（#57 / #474）
