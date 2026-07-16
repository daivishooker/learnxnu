# 第九天（Day 9）正文

学这三个：**`mkdir` / `rmdir` / `unlink`**  
源码：`xnu/` = **xnu-12377.121.6**

今天改的是目录里的**名字（目录项）**：新建目录、删空目录、删文件名。

---

## 今天目标

1. 找到编号 **136 / 137 / 10**  
2. 知道三者都先 **namei** 找到父目录 + 目标名  
3. 分清：`unlink` 删的是**名字/链接**；`rmdir` 专门删**空目录**  
4. 看到 `mode` 会受进程 `fd_cmask`（umask）影响

笔记：[`notes/daily/day-09.md`](../notes/daily/day-09.md)  
分析：[`notes/daily/day-09-analysis.md`](../notes/daily/day-09-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| unlink | **10** | 删除路径上的名字（文件/链接等） |
| mkdir | **136** | 创建目录 |
| rmdir | **137** | 删除空目录 |

---

## 1. mkdir（#136）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
mkdir(...) {
    VATTR_SET(&va, va_mode, (mode & ACCESSPERMS) & ~p->p_fd.fd_cmask);
    return mkdir1at(..., path, &va, AT_FDCWD, ...);
}
```

`mkdir1at` 要点：

```
NDINIT(..., CREATE, OP_MKDIR, LOCKPARENT, path)
nameiat → 父目录 dvp；若目标已存在 → EEXIST
设 va_type = VDIR
→ 授权 + 真正创建（compound VNOP / vn_mkdir 一类）
```

不返回 fd（和 `open(O_CREAT|O_DIRECTORY)` 不同）；只在命名空间里多出一个目录名。

---

## 2. rmdir（#137）

```c
rmdir(...) {
    return rmdirat_internal(..., AT_FDCWD, path, ...);
}
```

路径必须是目录且（通常）为空；内部会走到 `vn_rmdir` / 相关 VNOP。  
目录非空 → 常见 `ENOTEMPTY`。

---

## 3. unlink（#10）

```c
unlink(...) {
    return unlinkat_internal(..., AT_FDCWD, NULLVP, path, ..., 0);
}
```

删除**目录项名字**。对普通文件：链接计数减一，最后一个名字去掉且无引用时数据才真正回收。  
**一般不能**用 `unlink` 删目录（那是 `rmdir`；`unlinkat` 带 `AT_REMOVEDIR` 时可走删目录路径）。

---

## 今日对比

| | mkdir | rmdir | unlink |
|--|-------|-------|--------|
| 创建还是删 | 创建目录 | 删目录 | 删名字 |
| 对象 | 新 VDIR | 空目录 | 多为非目录 |
| 关键查找 | namei CREATE | namei + 父目录锁 | namei + remove |

三者都：**改目录命名空间**，不是改 cwd（Day 8），也不分配长期 fd（除非你另 open）。

---

## 用户层 Demo

目录与文件生命周期：`mkdir` → 建文件 → `unlink` → `rmdir`。

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/stat.h>

int main(void) {
    if (mkdir("/tmp/day09d", 0755) != 0) perror("mkdir");
    int fd = open("/tmp/day09d/a.txt", O_CREAT | O_WRONLY, 0644);
    if (fd >= 0) close(fd);
    if (unlink("/tmp/day09d/a.txt") != 0) perror("unlink");
    if (rmdir("/tmp/day09d") != 0) perror("rmdir");
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 10 / 136 / 137  
- [ ] 能说出 mkdir 的 umask/`fd_cmask`  
- [ ] 能区分 unlink vs rmdir  
- [ ] 填好 `notes/daily/day-09.md`

下一步：Day 10 → `rename` / `link`
