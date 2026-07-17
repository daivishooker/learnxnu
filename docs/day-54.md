# 第五十四天（Day 54）正文

学这两个：**`renameat` / `unlinkat`**  
源码：`xnu/` = **xnu-12377.121.6**

继续 `*at` 家族：相对目录 FD **改名/搬家** 与 **删名字**。

生活类比：

1. `renameat`：从 A 房间某抽屉，改挂到 B 房间另一个名字  
2. `unlinkat`：在某房间里拆掉一块门牌（文件减链接；目录则要 `AT_REMOVEDIR`）

---

## 今天目标

1. 找到编号 **465 / 472**  
2. 理解 `renameat`：双 `nameiat`（from/to）→ `renameat_internal`  
3. 理解 `unlinkat`：`DELETE` 查找 → 删文件名；`AT_REMOVEDIR` 走 rmdir  
4. 能说：`unlink`/`rename` ≈ `*at(AT_FDCWD, …)`  

笔记：[`notes/daily/day-54.md`](../notes/daily/day-54.md)  
分析：[`notes/daily/day-54-analysis.md`](../notes/daily/day-54-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| renameat | **465** | 相对 fromfd/tofd 重命名（可跨目录同卷） |
| unlinkat | **472** | 相对 dirfd 删除名字（或 `AT_REMOVEDIR` 删空目录） |

---

## 1. renameat（#465）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
rename(from, to)
  = renameat_internal(AT_FDCWD, from, AT_FDCWD, to, ...)

renameat(fromfd, from, tofd, to)
  = renameat_internal(fromfd, from, tofd, to, flags=0)

renameat_internal:
  nameiat(DELETE, from, fromfd) → 源父目录 + 源 vnode
  nameiat(RENAME, to, tofd)   → 目标父目录 +（可能已存在的）目标
  鉴权、同挂载等检查
  VNOP_RENAME / 复合 rename 路径
```

要点：

- 两个路径可以各带自己的目录 FD（最灵活）  
- 本质是**目录项改名/搬家**，不是复制文件内容  
- 更强的标志版：`renameatx_np`（#488，`RENAME_EXCL` / `SWAP` 等）  

---

## 2. unlinkat（#472）

```c
unlink(path)
  = unlinkat_internal(AT_FDCWD, path, ...)

unlinkat(dirfd, path, flag):
  if (flag & AT_REMOVEDIR)
    → rmdirat_internal(...)     // 删目录
  else
    → unlinkat_internal(...)    // 删非目录名字（减链接）

unlinkat_internal:
  nameiat(DELETE, path, dirfd)
  鉴权后 VNOP_REMOVE / 复合 remove
```

要点：

- 对普通文件：去掉一个目录项；链接数到 0 且无打开者时回收数据  
- **默认不能当 rmdir**；删目录要显式 `AT_REMOVEDIR`  
- 与 Day 9 `unlink`/`rmdir`、Day 10 `rename` 同语义，多了 dirfd  

`*at` 小结（Day 53–54）：

| 操作 | 调用 |
|------|------|
| 打开 | openat |
| 查元数据 | fstatat* |
| 改名 | renameat |
| 删除 | unlinkat |

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int dirfd;
    int fd;

    dirfd = open("/tmp", O_RDONLY | O_DIRECTORY);
    if (dirfd < 0) { perror("open /tmp"); return 1; }

    unlinkat(dirfd, "day54_a.txt", 0);
    unlinkat(dirfd, "day54_b.txt", 0);

    fd = openat(dirfd, "day54_a.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("openat"); close(dirfd); return 1; }
    (void)write(fd, "x\n", 2);
    close(fd);

    /* Demo A：renameat — 同目录改名 */
    if (renameat(dirfd, "day54_a.txt", dirfd, "day54_b.txt") != 0) {
        perror("renameat");
        close(dirfd);
        return 1;
    }
    printf("renameat ok\n");

    /* Demo B：unlinkat — 删掉新名字 */
    if (unlinkat(dirfd, "day54_b.txt", 0) != 0) {
        perror("unlinkat");
        close(dirfd);
        return 1;
    }
    printf("unlinkat ok\n");

    close(dirfd);
    return 0;
}
```

```bash
cc -o day54_demo day54_demo.c && ./day54_demo
```

---

## 做完打勾

- [ ] 找到 465 / 472  
- [ ] 能说 rename/unlink 汇入 *at_internal  
- [ ] 能说 unlinkat + AT_REMOVEDIR ≈ rmdir  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-54.md`

下一步：Day 55 → `mkdirat` / `faccessat`（#475 / #466）
