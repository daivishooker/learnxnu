# 第十天（Day 10）正文

学这两个：**`link` / `rename`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 9：继续改命名空间——**加硬链接**、**改名/搬家**。

先分清两种「链接」（你问的 hard vs soft/「浮动」）：

| | 硬链接 hard link | 符号链接 soft / symbolic link |
|--|------------------|------------------------------|
| 系统调用 | **`link`**（今天） | **`symlink`**（顺带知道） |
| 有没有自己的 vnode | **没有**，共用目标 vnode | **有**，自己是 `VLNK` 类型 vnode |
| 存什么 | 目录项再挂一个名字 | 存一段目标路径字符串 |
| 跨文件系统 | 通常不行 | 可以 |

---

## 今天目标

1. 找到编号 **9 / 128**  
2. 看清 `link`：两次 namei → `VNOP_LINK`（不加新数据 vnode）  
3. 看清 `rename`：from/to 两条路径，目录项搬家（可能跨目录）  
4. 能口述硬链接 vs 符号链接

笔记：[`notes/daily/day-10.md`](../notes/daily/day-10.md)  
分析：[`notes/daily/day-10-analysis.md`](../notes/daily/day-10-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| link | **9** | `link(已有路径, 新路径)` 建硬链接 |
| rename | **128** | `rename(from, to)` 改名或移到另一目录名下 |

---

## 1. link（#9）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
link(...) {
    return linkat_internal(..., AT_FDCWD, path, AT_FDCWD, link, AT_SYMLINK_FOLLOW, ...);
}
```

`linkat_internal` 骨架：

```
1) namei(LOOKUP) 已有 path → vnode vp（被链接对象）
2) 目录一般 EPERM（除非文件系统声明支持目录硬链）
3) namei(CREATE) 新名字 link → 父目录 dvp，目标不存在
4) VNOP_LINK(vp, dvp, ...)  → 父目录多一条名字指向 vp
5) 链接计数 +1（在文件系统层体现）
```

**不新建数据 vnode**——这就是硬链接。

---

## 2. rename（#128）

```c
rename(...) {
    return renameat_internal(..., AT_FDCWD, from, AT_FDCWD, to, ...);
}
```

概念：

```
from 路径的目录项  →  挪到 to 这个名字下
（同一 vnode；通常仍是同一个文件系统）
```

可能是同目录改名，也可能是跨目录移动名字。目标已存在时有替换/失败等规则（POSIX + Darwin 扩展 flag 在 `renameatx_np`）。

今天先抓住：**改的是目录项位置/名字，不是拷贝文件内容。**

---

## 今日对比

| | link | rename |
|--|------|--------|
| 结果 | 多一个名字 | 名字从 A 换成 B（旧名通常消失） |
| 链接数 | 一般 +1 | 通常不变（只是改名） |
| 典型限制 | 同文件系统；目录受限 | 同挂载等 |

---

## 用户层 Demo

`link` 增加硬链接名；`rename` 原子改名（同文件系统内）。

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int fd = open("/tmp/day10-a", O_CREAT | O_WRONLY | O_TRUNC, 0644);
    if (fd >= 0) { write(fd, "x", 1); close(fd); }
    if (link("/tmp/day10-a", "/tmp/day10-b") != 0) perror("link");
    if (rename("/tmp/day10-b", "/tmp/day10-c") != 0) perror("rename");
    unlink("/tmp/day10-a");
    unlink("/tmp/day10-c");
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 9 / 128  
- [ ] 能画「两 namei + VNOP_LINK」  
- [ ] 能区分 link vs symlink  
- [ ] 填好 `notes/daily/day-10.md`

下一步：Day 11 → `fork` / `vfork` / `wait4`
