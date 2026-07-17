# 第四十六天（Day 46）正文

学这两个：**`truncate` / `ftruncate`**  
源码：`xnu/` = **xnu-12377.121.6**

今天改的是文件**逻辑长度**（`va_data_size`）：变短丢掉尾部，变长常为零填充空洞。仍经 `vnode_setattr`。

生活类比：

1. `truncate`：按路径把纸卷剪到指定长度（或拉长留白）  
2. `ftruncate`：对已打开的文件做同一件事（且能看出 `fileglob` 分流）

---

## 今天目标

1. 找到编号 **200 / 201**  
2. 理解共用：`truncate_internal` → `vnode_setattr(va_data_size)`  
3. 看清 `ftruncate` 里 `FILEGLOB_DTYPE` 分流（vnode / posix shm / 其它）  
4. 能说还会检查 `RLIMIT_FSIZE`  

笔记：[`notes/daily/day-46.md`](../notes/daily/day-46.md)  
分析：[`notes/daily/day-46-analysis.md`](../notes/daily/day-46-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| truncate | **200** | 按路径把文件截断/扩展到 length |
| ftruncate | **201** | 按 FD 做同样的事 |

---

## 1. 共用：truncate_internal

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
truncate_validate_common(length) {
    length < 0 → EINVAL
    length > RLIMIT_FSIZE → SIGXFSZ + EFBIG
}

truncate_internal(vp, length, ..., need_auth) {
    VATTR_SET(va_data_size, length)
    若 need_auth：authorize
    vnode_setattr(vp, &va)     // 真正改大小
}
```

---

## 2. truncate（#200）——路径版

```c
truncate(path, length) {
    validate
    namei(path) → vp
    truncate_internal(..., need_auth=true)
}
```

---

## 3. ftruncate（#201）——FD 版（分流很清晰）

```c
ftruncate(fd, length) {
    validate
    fp_lookup(fd) → fp
    switch (FILEGLOB_DTYPE(fp->fp_glob)) {
      DTYPE_PSXSHM → pshm_truncate(...)   // 共享内存另一条路
      DTYPE_VNODE  → 继续
      default      → EINVAL               // socket 等不行
    }
    需要 FWRITE；符号链接 / append-only 拒绝
    truncate_internal(..., need_auth=false)  // open 时已鉴权过写
}
```

要点（接前面讨论）：

- **分流点就在 `fileglob` 的 dtype**  
- 路径版总是 vnode；FD 版先问「你是什么类型」  
- 截断到更小：尾部数据逻辑上丢弃；扩展：常见稀疏/零填充（FS 实现细节）  
- 与 `write` 不同：不经 UIO 写数据，是直接改 **size 属性**  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

static off_t filesize(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) return -1;
    return st.st_size;
}

int main(void) {
    const char *path = "/tmp/day46_trunc.txt";
    int fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    (void)write(fd, "0123456789", 10);
    close(fd);
    printf("initial size=%lld\n", (long long)filesize(path));

    /* Demo A：truncate — 路径截到 4 */
    if (truncate(path, 4) != 0) {
        perror("truncate");
        return 1;
    }
    printf("after truncate(4)=%lld\n", (long long)filesize(path));

    /* Demo B：ftruncate — FD 扩到 8 */
    fd = open(path, O_RDWR);
    if (fd < 0) { perror("open"); return 1; }
    if (ftruncate(fd, 8) != 0) {
        perror("ftruncate");
        close(fd);
        return 1;
    }
    close(fd);
    printf("after ftruncate(8)=%lld\n", (long long)filesize(path));
    return 0;
}
```

```bash
cc -o day46_demo day46_demo.c && ./day46_demo
```

---

## 做完打勾

- [ ] 找到 200 / 201  
- [ ] 能说 truncate_internal → setattr(va_data_size)  
- [ ] 能说 ftruncate 的 FILEGLOB_DTYPE 分流  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-46.md`

下一步：Day 47 → [`pathconf` / `fpathconf`](day-47.md)（#191 / #192）
