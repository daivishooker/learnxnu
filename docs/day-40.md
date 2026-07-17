# 第四十天（Day 40）正文

学这两个：**`clonefileat` / `fclonefileat`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天 `copyfile` 是「请 FS 拷一份」；今天是现代 Darwin 更常用的 **clone**：同卷上做出写时复制式副本（APFS 等支持时几乎不立刻占双份空间）。

生活类比：

1. `clonefileat`：按路径「克隆」出新名字——像快捷影印，改一边前两边共享纸张  
2. `fclonefileat`：手里已有打开的源 FD，再克隆到目标路径——省掉再查源路径

---

## 今天目标

1. 找到编号 **462 / 517**  
2. 理解两者都进 `clonefile_internal` → `VNOP_CLONEFILE`  
3. 记住约束：同 mount、目标不得已存在；可为文件/目录/符号链接  
4. 能对比：`copyfile` vs `clonefile*`；路径源 vs FD 源  

笔记：[`notes/daily/day-40.md`](../notes/daily/day-40.md)  
分析：[`notes/daily/day-40-analysis.md`](../notes/daily/day-40-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| clonefileat | **462** | 相对目录 FD：源路径 → 目标路径克隆 |
| fclonefileat | **517** | 源已是 FD → 目标路径克隆 |

（还有用户库包装 `clonefile(3)` = 常以 `AT_FDCWD` 调 `clonefileat`。）

---

## 1. clonefileat（#462）——路径源克隆

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
clonefileat(src_dirfd, src, dst_dirfd, dst, flags) {
    校验 flags（CLONE_NOFOLLOW / NOOWNERCOPY / ACL …）
    nameiat(src_dirfd, src) → fvp
    clonefile_internal(fvp, data_read_authorised=FALSE, dst_dirfd, dst, flags)
}
```

`clonefile_internal` 要点：

```c
目标 nameiat(CREATE) → tdvp；tvp 已存在 → EEXIST
vnode_mount(tdvp) != vnode_mount(fvp) → EXDEV   // 必须同卷
鉴权：目标父目录可 ADD；源可读
准备 vnode_attr（mode/flags/可选 ACL、owner）
VNOP_CLONEFILE(fvp, tdvp, &tvp, ...)
```

---

## 2. fclonefileat（#517）——FD 源克隆

```c
fclonefileat(src_fd, dst_dirfd, dst, flags) {
    fp_getfvp(src_fd) → fvp；需 FREAD
    clonefile_internal(fvp, data_read_authorised=TRUE, ...)
}
```

要点：

- 与 `clonefileat` **汇合到同一内部函数**  
- `data_read_authorised=TRUE`：已有可读 FD，鉴权时可少查一层「读数据」  
- 源类型：普通文件、目录、符号链接（named stream 不行）  

对照昨天：

| | 语义 | 典型实现 |
|--|------|----------|
| copyfile | 拷贝 | `VNOP_COPYFILE` |
| clonefile* | 克隆（常 CoW） | `VNOP_CLONEFILE` |

不同卷 → 两边都是 `EXDEV`；clone 不做跨卷「退回成慢拷贝」（那是上层库的事）。

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/clonefile.h>
#include <unistd.h>

static int write_all(const char *path, const char *s) {
    int fd = open(path, O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd < 0) return -1;
    ssize_t n = write(fd, s, strlen(s));
    close(fd);
    return n < 0 ? -1 : 0;
}

static void show(const char *path) {
    char buf[64];
    int fd = open(path, O_RDONLY);
    if (fd < 0) { perror(path); return; }
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n < 0) { perror("read"); return; }
    buf[n] = '\0';
    printf("%s => %s", path, buf);
}

int main(void) {
    const char *src = "/tmp/day40_src.txt";
    const char *dst1 = "/tmp/day40_clone1.txt";
    const char *dst2 = "/tmp/day40_clone2.txt";

    unlink(dst1);
    unlink(dst2);
    if (write_all(src, "clone-me\n") != 0) {
        perror("write_all");
        return 1;
    }

    /* Demo A：clonefileat（AT_FDCWD = 相对当前目录的路径） */
    if (clonefileat(AT_FDCWD, src, AT_FDCWD, dst1, 0) != 0) {
        perror("clonefileat");
        return 1;
    }
    printf("after clonefileat:\n");
    show(dst1);

    /* Demo B：fclonefileat — 已打开源 FD */
    int sfd = open(src, O_RDONLY);
    if (sfd < 0) { perror("open src"); return 1; }
    if (fclonefileat(sfd, AT_FDCWD, dst2, 0) != 0) {
        perror("fclonefileat");
        close(sfd);
        return 1;
    }
    close(sfd);
    printf("after fclonefileat:\n");
    show(dst2);

    return 0;
}
```

```bash
cc -o day40_demo day40_demo.c && ./day40_demo
```

（需 Darwin；目标卷须支持 clone，通常为 APFS。失败常见 `ENOTSUP` / `EXDEV`。）

---

## 做完打勾

- [ ] 找到 462 / 517  
- [ ] 能说两者进 `clonefile_internal` → `VNOP_CLONEFILE`  
- [ ] 能说同卷、目标不存在；与 copyfile 对比  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-40.md`

下一步：Day 41 → [`searchfs` / `fsgetpath`](day-41.md)（#225 / #427）
