# 第四十五天（Day 45）正文

学这两个：**`utimes` / `futimes`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天改权限/属主；今天改 **atime / mtime**（访问时间、修改时间）。仍然落到 `vnode_setattr`。

生活类比：

1. `utimes`：按路径改文件外壳上的两枚时间戳  
2. `futimes`：手里已有打开的文件（FD），改同一对时间戳  

---

## 今天目标

1. 找到编号 **138 / 139**  
2. 理解共用：`getutimes` 取时间 → `setutimes` → `vnode_setattr`  
3. 对比路径版 vs FD 版；FD 版经 `file_vnode`（必须是 vnode）  
4. 能说 `tptr == NULL` 表示「都改成当前时间」  

笔记：[`notes/daily/day-45.md`](../notes/daily/day-45.md)  
分析：[`notes/daily/day-45-analysis.md`](../notes/daily/day-45-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| utimes | **138** | 按路径设置 atime / mtime |
| futimes | **139** | 按 FD 设置 atime / mtime |

---

## 1. 共用内核路径

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
getutimes(tptr, ts[2]) {
    tptr == NULL → 取当前时间，atime=mtime=now
    否则 copyin timeval[2] → timespec[2]
}

setutimes(vp, ts, nullflag) {
    VATTR_SET(va_access_time, ts[0])
    VATTR_SET(va_modify_time, ts[1])
    鉴权 → vnode_setattr
}
```

---

## 2. utimes（#138）——路径版

```c
utimes(path, tptr) {
    namei(path) → vp          // 用户路径进内核
    getutimes(tptr, ts)
    setutimes(vp, ts, ...)
}
```

---

## 3. futimes（#139）——FD 版

```c
futimes(fd, tptr) {
    getutimes(tptr, ts)
    file_vnode(fd) → vp       // 要求 FD 背后是 vnode
    setutimes(vp, ts, ...)
}
```

要点（呼应昨日讨论）：

- `file_vnode`：在 `fileglob` 分流里确认是 **DTYPE_VNODE**  
- 对纯 socket FD 调 `futimes`：过不了 vnode 检查  
- 用户缓冲是 `struct timeval tv[2]`：`[0]=atime`，`[1]=mtime`  
- 与 Day 38 `setattrlist(ATTR_CMN_MODTIME)` 同类目标，接口更老、更专用  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>

static void show_mtime(const char *label, const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) { perror("stat"); return; }
    printf("%s mtime=%ld\n", label, (long)st.st_mtime);
}

int main(void) {
    const char *path = "/tmp/day45_time.txt";
    struct timeval tv[2];
    int fd;

    fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    (void)write(fd, "x\n", 2);

    /* Demo A：utimes — 路径；NULL = 当前时间 */
    if (utimes(path, NULL) != 0) {
        perror("utimes");
        close(fd);
        return 1;
    }
    show_mtime("after utimes(NULL)", path);

    /* Demo B：futimes — FD；显式设一对时间 */
    tv[0].tv_sec = 1000000000;  /* atime */
    tv[0].tv_usec = 0;
    tv[1].tv_sec = 1000000000;  /* mtime */
    tv[1].tv_usec = 0;
    if (futimes(fd, tv) != 0) {
        perror("futimes");
        close(fd);
        return 1;
    }
    close(fd);
    show_mtime("after futimes", path);
    return 0;
}
```

```bash
cc -o day45_demo day45_demo.c && ./day45_demo
```

---

## 做完打勾

- [ ] 找到 138 / 139  
- [ ] 能说 getutimes + setutimes → vnode_setattr  
- [ ] 能说 futimes 要 vnode FD（file_vnode）  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-45.md`

下一步：Day 46 → `truncate` / `ftruncate`（#200 / #201）
