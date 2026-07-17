# 第五十三天（Day 53）正文

学这两个：**`openat` / `fstatat64`**  
源码：`xnu/` = **xnu-12377.121.6**

今天看 `*at` 家族的核心：相对**目录 FD** 做打开与取元数据，避免「拼绝对路径」的竞态。

生活类比：

1. `openat`：人已经站在某间房间（dirfd），再开房间里的某个抽屉  
2. `fstatat64`：站在同一间房间，去摸某个抽屉的标签（大小、权限等）

---

## 今天目标

1. 找到编号 **463 / 470**  
2. 理解 `openat`：`openat_internal` → `nameiat(dirfd)` → 与 `open` 同套打开逻辑  
3. 理解 `fstatat64`：`nameiat` → `vn_stat`（64 位 `stat64`）  
4. 能说：`open(path)` ≈ `openat(AT_FDCWD, path)`  

笔记：[`notes/daily/day-53.md`](../notes/daily/day-53.md)  
分析：[`notes/daily/day-53-analysis.md`](../notes/daily/day-53-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| openat | **463** | 相对目录 FD 打开路径 |
| fstatat64 | **470** | 相对目录 FD 取 `stat64` 元数据 |

（还有 `fstatat` #469 旧布局；`open` 内部走同一 `openat_internal`。）

---

## 1. openat（#463）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
open(path, flags, mode)
  = openat_internal(..., AT_FDCWD, ...)

openat(dirfd, path, flags, mode)
  = openat_internal(..., dirfd, ...)

openat_internal:
  准备 va_mode（受 umask）
  NDINIT LOOKUP OP_OPEN
  open1at(..., fd)          // nameiat 从 dirfd 起解析 path
```

要点：

- `dirfd` 常为已 `open` 的目录；`AT_FDCWD` = 相对进程当前目录  
- 路径若以 `/` 开头，行为仍是绝对路径（与 POSIX `*at` 一致）  
- 解决：`chdir` 竞态、多线程 cwd、沙箱里「钉死一个目录再操作」  

---

## 2. fstatat64（#470）

```c
fstatat64(dirfd, path, sb, flag) {
    fstatat_internal(..., isstat64=1, fd=dirfd, flag)
      nameiat(dirfd, path)   // 或 AT_FDONLY 时直接用 fd 的 vnode
      FOLLOW / NOFOLLOW 由 AT_SYMLINK_NOFOLLOW 等决定
      vn_stat → copyout stat64
}
```

要点：

- 与 Day 7 `stat64`/`lstat64` 同族：这里多了 **起始目录 FD**  
- `AT_SYMLINK_NOFOLLOW` ≈ `lstat`（不跟随最后一级符号链接）  
- 查的是 vnode 元数据（经 `vnode_attr` / `vn_stat`），不是 xattr  

对照：

| | 起点 | 动作 |
|--|------|------|
| open | cwd / 绝对路径 | 打开 |
| openat | dirfd | 打开 |
| stat64 | 路径 | 取元数据 |
| fstatat64 | dirfd + 路径 | 取元数据 |

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    int dirfd, fd;
    struct stat st;

    dirfd = open("/tmp", O_RDONLY | O_DIRECTORY);
    if (dirfd < 0) { perror("open /tmp"); return 1; }

    /* Demo A：openat — 在 /tmp 下创建/打开文件 */
    fd = openat(dirfd, "day53_at.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("openat"); close(dirfd); return 1; }
    (void)write(fd, "hi\n", 3);
    close(fd);

    /* Demo B：fstatat — 相对同一 dirfd 取元数据 */
    if (fstatat(dirfd, "day53_at.txt", &st, 0) != 0) {
        perror("fstatat");
        close(dirfd);
        return 1;
    }
    printf("fstatat size=%lld mode=%o\n",
           (long long)st.st_size, st.st_mode & 0777);

    close(dirfd);
    return 0;
}
```

```bash
cc -o day53_demo day53_demo.c && ./day53_demo
```

（用户层常用 `fstatat`；内核 64 位路径对应 `fstatat64`。Darwin 上 `struct stat` 已是 64 位布局。）

---

## 做完打勾

- [ ] 找到 463 / 470  
- [ ] 能说 open ≈ openat(AT_FDCWD)  
- [ ] 能说 fstatat*：nameiat + vn_stat  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-53.md`

下一步：Day 54 → [`renameat` / `unlinkat`](day-54.md)（#465 / #472）
