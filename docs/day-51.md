# 第五十一天（Day 51）正文

学这两个：**`chflags` / `fchflags`**  
源码：`xnu/` = **xnu-12377.121.6**

接 Day 46 的问题：`ftruncate` 为何拒绝 **append-only**？今天看这些标志是怎么设上去的。

生活类比：

1. `chflags`：给文件贴额外规矩贴纸（只能追加、不可改……）  
2. `fchflags`：对已打开的 FD 贴/改同一套贴纸  

---

## 今天目标

1. 找到编号 **34 / 35**  
2. 理解共用：`chflags1` → `chflags0` → `vnode_setattr(va_flags)`  
3. 认识常见标志：`UF_APPEND` / `UF_IMMUTABLE` 等  
4. 能说设了 `APPEND` 后，vnode 上会记 `VE_APPENDONLY`  

笔记：[`notes/daily/day-51.md`](../notes/daily/day-51.md)  
分析：[`notes/daily/day-51-analysis.md`](../notes/daily/day-51-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| chflags | **34** | 按路径设置 BSD 文件标志 |
| fchflags | **35** | 按 FD 设置同上 |

---

## 共用路径

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
chflags(path, flags) {
    namei(FOLLOW) → vp
    chflags1(vp, flags)
}

fchflags(fd, flags) {
    file_vnode(fd) → vp          // 必须是 vnode FD
    chflags1(vp, flags)
}

chflags1:
    VATTR_SET(va_flags, flags)
    chflags0 → authorize（可带 NOIMMUTABLE 以便清 immutable）
             → vnode_setattr
    若 flags 含 APPEND：vp->v_ext_flag |= VE_APPENDONLY
    否则清掉 VE_APPENDONLY
```

---

## 常见标志（`sys/stat.h`）

| 标志 | 含义 |
|------|------|
| `UF_APPEND` / `SF_APPEND` | 只能追加写；截断/改中间会失败（`APPEND` 宏是二者或） |
| `UF_IMMUTABLE` / `SF_IMMUTABLE` | 不可改（删、改内容等受限） |
| `UF_HIDDEN` 等 | 其它 UI/系统行为标志 |

`UF_*` 一般用户可设（受权限限制）；`SF_*` 多为系统/特权标志。

和 `chmod` 对照：

| | 改什么 |
|--|--------|
| chmod | 权限位 rwx（谁能读/写/执行） |
| chflags | 额外行为约束（只能追加、冻结等） |

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>

int main(void) {
    const char *path = "/tmp/day51_flags.txt";
    int fd;
    struct stat st;

    fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    (void)write(fd, "abc", 3);

    /* Demo A：fchflags — 设 UF_APPEND（只能追加） */
    if (fchflags(fd, UF_APPEND) != 0) {
        perror("fchflags UF_APPEND");
        close(fd);
        return 1;
    }
    if (fstat(fd, &st) == 0) {
        printf("flags after APPEND: 0x%x\n", st.st_flags);
    }

    /* 对 append-only 做 ftruncate → 预期失败（呼应 Day 46） */
    if (ftruncate(fd, 1) != 0) {
        printf("ftruncate on append-only: %s (expected)\n", strerror(errno));
    } else {
        printf("ftruncate unexpectedly succeeded\n");
    }

    /* Demo B：chflags — 清标志（flags=0） */
    close(fd);
    if (chflags(path, 0) != 0) {
        perror("chflags clear");
        return 1;
    }
    printf("chflags(0) cleared\n");
    return 0;
}
```

```bash
cc -o day51_demo day51_demo.c && ./day51_demo
```

（需 Darwin；也可用 shell：`chflags append /tmp/day51_flags.txt`。）

---

## 做完打勾

- [ ] 找到 34 / 35  
- [ ] 能说 chflags → setattr(va_flags)  
- [ ] 能说 APPEND → VE_APPENDONLY，故 ftruncate 拒绝  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-51.md`

下一步：Day 52 → `getattrlistbulk` / `fsctl`（#461 / #242）
