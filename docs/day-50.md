# 第五十天（Day 50）正文

学这两个：**`mknod` / `mkfifo`**  
源码：`xnu/` = **xnu-12377.121.6**

前面会建普通文件、目录、符号链接；今天建两类**特殊 vnode**：设备节点与命名管道。

生活类比：

1. `mknod`：在目录里放一块「设备门牌」（字符/块设备），指向某个设备号  
2. `mkfifo`：在目录里放一根「命名水管」，进程按路径打开后像 pipe 一样读写  

---

## 今天目标

1. 找到编号 **14 / 132**  
2. 理解 `mknod`：特权 + `S_IFCHR`/`S_IFBLK` → `vn_create`；`S_IFIFO` 转去 `mkfifo`  
3. 理解 `mkfifo`：`CREATE` → `va_type=VFIFO` → `vn_create`  
4. 能对比：设备节点 vs FIFO vs 普通文件  

笔记：[`notes/daily/day-50.md`](../notes/daily/day-50.md)  
分析：[`notes/daily/day-50-analysis.md`](../notes/daily/day-50-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| mknod | **14** | 创建特殊文件（主要为字符/块设备；FIFO 会转交） |
| mkfifo | **132** | 创建命名管道（FIFO） |

（还有 `mknodat` #554、`mkfifoat` #553。）

---

## 1. mknod（#14）——特殊文件 / 设备节点

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
mknod(path, mode, dev) {
    VATTR_SET(va_mode, ... & ~umask)
    VATTR_SET(va_rdev, dev)          // 设备号
    mknodat_internal(..., AT_FDCWD)
}

mknodat_internal:
    if ((mode & S_IFMT) == S_IFIFO)
        → mkfifo1(...)               // FIFO 不走设备路径
    suser(...) 必须特权              // 创建设备节点要 root 类权限
    nameiat(CREATE) → 父目录
    S_IFCHR → VCHR；S_IFBLK → VBLK；其它 → EINVAL
    authorize ADD_FILE
    vn_create(...)
}
```

要点：

- 日常 `/dev` 里那些节点，很多就是 `mknod` 思路（现代也可能用 devfs）  
- **无特权**对 `S_IFCHR`/`S_IFBLK` 会失败（`suser`）  
- `mode` 里的文件类型位决定建什么  

---

## 2. mkfifo（#132）——命名管道

```c
mkfifo(path, mode) {
    VATTR_SET(va_mode, ... & ~umask)
    mkfifo1:
      nameiat(CREATE)
      已存在 → EEXIST
      va_type = VFIFO
      vn_authorize_create → vn_create
}
```

要点：

- 结果是路径上的 **FIFO vnode**；两端用 `open` 读/写（阻塞语义类似匿名 `pipe`）  
- 与 Day 14 `pipe` 对照：`pipe` 出一对匿名 FD；`mkfifo` 出**有名字**的管道  
- 一般**不需要**像 `mknod` 设备那样的特权  

对照：

| | 类型 | 典型用途 |
|--|------|----------|
| 普通文件 | VREG | 存数据 |
| mknod 设备 | VCHR / VBLK | 进设备驱动 |
| mkfifo | VFIFO | 按路径的 IPC |
| symlink | VLNK | 存路径字符串 |

---

## 用户层 Demo

```c
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main(void) {
    const char *fifo = "/tmp/day50.fifo";
    struct stat st;

    unlink(fifo);

    /* Demo A：mkfifo — 普通用户可做 */
    if (mkfifo(fifo, 0600) != 0) {
        perror("mkfifo");
        return 1;
    }
    if (stat(fifo, &st) != 0) { perror("stat"); return 1; }
    printf("mkfifo ok: S_ISFIFO=%d mode=%o\n",
           S_ISFIFO(st.st_mode), st.st_mode & 0777);

    /* Demo B：mknod 设备 — 通常需要特权；演示预期失败 */
    unlink("/tmp/day50.nod");
    if (mknod("/tmp/day50.nod", S_IFCHR | 0600, makedev(0, 0)) != 0) {
        printf("mknod device: %s (expected without root)\n", strerror(errno));
    } else {
        printf("mknod device succeeded (running privileged?)\n");
    }

    /* mknod 建 FIFO 会转到 mkfifo 路径 */
    unlink("/tmp/day50.fifo2");
    if (mknod("/tmp/day50.fifo2", S_IFIFO | 0600, 0) != 0) {
        perror("mknod FIFO");
    } else {
        printf("mknod(S_IFIFO) ok (delegates to mkfifo path)\n");
    }
    return 0;
}
```

```bash
cc -o day50_demo day50_demo.c && ./day50_demo
```

---

## 做完打勾

- [ ] 找到 14 / 132  
- [ ] 能说 mknod：特权 + VCHR/VBLK；FIFO 转 mkfifo  
- [ ] 能说 mkfifo：CREATE → VFIFO → vn_create  
- [ ] 跑通 Demo（至少 mkfifo）  
- [ ] 填好 `notes/daily/day-50.md`

下一步：Day 51 → [`chflags` / `fchflags`](day-51.md)（#34 / #35；含 append-only 等标志）
