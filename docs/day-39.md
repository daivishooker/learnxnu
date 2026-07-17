# 第三十九天（Day 39）正文

学这两个：**`exchangedata` / `copyfile`**  
源码：`xnu/` = **xnu-12377.121.6**

今天看 Darwin VFS 里两种「整文件级」操作：原子交换内容，以及内核侧拷贝。

生活类比：

1. `exchangedata`：两份文件的**内容对调**，路径/名字还挂在原处（编辑器「安全保存」常用套路）  
2. `copyfile`：请文件系统**自己拷一份**（可能走克隆/加速路径），不是用户态 `read`/`write` 循环

---

## 今天目标

1. 找到编号 **223 / 227**  
2. 理解 `exchangedata`：两路径 → 同卷、皆普通文件 → `VNOP_EXCHANGE`  
3. 理解 `copyfile`：源 + 目标名 → 鉴权 → `VNOP_COPYFILE`  
4. 能对比：交换内容 vs 复制出新文件；与用户态拷贝循环对照  

笔记：[`notes/daily/day-39.md`](../notes/daily/day-39.md)  
分析：[`notes/daily/day-39-analysis.md`](../notes/daily/day-39-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| exchangedata | **223** | 交换两个普通文件的数据内容 |
| copyfile | **227** | 内核/FS 侧把源拷到目标路径 |

---

## 1. exchangedata（#223）——内容对调

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
exchangedata(path1, path2, options) {
    namei(path1) → fvp
    namei(path2) → svp
    同 vnode → EINVAL
    不同 mount → EXDEV          // 必须同一卷
    非普通文件 → EINVAL
    读写鉴权
    VNOP_EXCHANGE(fvp, svp, ...)
}
```

要点：

- **交换的是数据**（fork/内容），不是改目录项名字  
- 典型用途：写临时文件 → `exchangedata(正式, 临时)` → 原子替换内容  
- 两路径必须在**同一文件系统**；目录不行  

类比：两本书书架位置不变，只把书里的字整本对调。

---

## 2. copyfile（#227）——内核侧拷贝

同文件：

```c
copyfile(from, to, mode, flags) {
    namei(from) → fvp
    namei(CREATE, to) → tdvp / tvp
    目标已存在且无 CPF_OVERWRITE → EEXIST
    目录 → EISDIR
    鉴权：读源、（覆盖则删目标）、父目录可 ADD_FILE
    VNOP_COPYFILE(fvp, tdvp, tvp, ..., mode, flags)
}
```

要点：

- `syscalls.master` 标了 `NO_SYSCALL_STUB`：日常更常见的是 **libc `copyfile(3)`**（用户库，内部可能走 clone/其他路径）  
- 本 syscall 是直接进 VFS 的内核入口；学内核时跟 `VNOP_COPYFILE`  
- 标志如 `CPF_OVERWRITE`（见 `sys/fcntl.h`）  
- 现代 APFS 上「零拷贝式复制」更多看 **`clonefileat`**（Day 40 预告）  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/fcntl.h>
#include <sys/syscall.h>
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
    const char *a = "/tmp/day39_a.txt";
    const char *b = "/tmp/day39_b.txt";
    const char *c = "/tmp/day39_c.txt";

    if (write_all(a, "AAA\n") || write_all(b, "BBB\n")) {
        perror("write_all");
        return 1;
    }

    /* Demo A：exchangedata — 内容对调，路径仍是 a/b */
    if (exchangedata(a, b, 0) != 0) {
        perror("exchangedata");
        return 1;
    }
    printf("after exchangedata:\n");
    show(a);  /* 期望 BBB */
    show(b);  /* 期望 AAA */

    /* Demo B：copyfile syscall — 内核侧拷贝到新路径 */
    unlink(c);
    if (syscall(SYS_copyfile, a, c, 0644, 0) != 0) {
        perror("SYS_copyfile");
        return 1;
    }
    printf("after copyfile:\n");
    show(c);

    return 0;
}
```

```bash
cc -o day39_demo day39_demo.c && ./day39_demo
```

（需 Darwin/macOS；`SYS_copyfile` 无公开 stub 时用 `syscall`。）

---

## 做完打勾

- [ ] 找到 223 / 227  
- [ ] 能说 exchangedata：同卷两普通文件 → VNOP_EXCHANGE  
- [ ] 能说 copyfile：鉴权后 VNOP_COPYFILE；与 libc copyfile(3) 区分  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-39.md`

下一步：Day 40 → `clonefileat` / `fclonefileat`（#462 / #517）
