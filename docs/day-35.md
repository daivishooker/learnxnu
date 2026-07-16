# 第三十五天（Day 35）正文

学这两个：**`statfs64` / `fstatfs64`**  
源码：`xnu/` = **xnu-12377.121.6**

接着刷盘，今天问：**这块文件系统有多大、剩多少、挂在哪**——对 mount 做统计，不是对单个文件做 `stat`。

生活类比：

1. `statfs64(path)`：顺着路径找到「所在柜子」，问柜子容量  
2. `fstatfs64(fd)`：手里已有打开的抽屉，问它属于哪个柜子的容量  

---

## 今天目标

1. 找到编号 **345 / 346**（旧版 `statfs`/`fstatfs` 为 157/158，今天以 64 为主）  
2. 理解两者都落到 `mount`，经 `vfs_update_vfsstat` → `vfs_get_statfs64` → copyout  
3. 对比：路径 lookup vs FD → vnode → `v_mount`  
4. 能说：查的是**文件系统**，不是 inode 元数据  

笔记：[`notes/daily/day-35.md`](../notes/daily/day-35.md)  
分析：[`notes/daily/day-35-analysis.md`](../notes/daily/day-35-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| statfs64 | **345** | 按路径查文件系统统计 |
| fstatfs64 | **346** | 按 FD 查文件系统统计 |

`statfs64` 结果里常见：块大小、总块数、空闲块、挂载点名、文件系统类型名等（`struct statfs64`）。

---

## 1. statfs64（#345）——路径 → mount

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
statfs64(path, buf) {
    namei(LOOKUP) → vp
    mp = vp->v_mount
    vfs_update_vfsstat(mp, …)   // 向 FS 刷新统计
    vfs_get_statfs64(mp, &sfs)
    copyout → 用户 buf
}
```

和 Day 7 `stat64` 对照：`stat` 填的是**文件**；`statfs` 填的是**所在挂载**。

---

## 2. fstatfs64（#346）——FD → mount

```c
fstatfs64(fd, buf) {
    file_vnode(fd) → vp
    mp = vp->v_mount
    vfs_update_vfsstat → vfs_get_statfs64 → copyout
}
```

不需要再走路径；适合已经 `open` 过的文件/目录。

---

## 3. 今日串起来

```text
路径或 FD → vnode → mount
              ↓
     vfs_update_vfsstat（更新）
              ↓
     statfs64 结构 copyout
```

| 调用 | 怎么找到 mount |
|------|----------------|
| statfs64 | `namei` 路径 |
| fstatfs64 | FD → vnode |

和 Day 34：`sync` 扫**所有** mount；今天是查**某一个** mount 的账单。

---

## 用户层 Demo

`statfs`/`fstatfs` 读文件系统统计（用户层常见封装；内核侧对应 `statfs64`/`fstatfs64`）。

```c
#include <fcntl.h>
#include <stdio.h>
#include <sys/mount.h>
#include <sys/param.h>
#include <unistd.h>

int main(void) {
    struct statfs s;
    if (statfs("/", &s) == 0)
        printf("fstyp=%s blocks=%llu bfree=%llu\n",
               s.f_fstypename,
               (unsigned long long)s.f_blocks,
               (unsigned long long)s.f_bfree);
    int fd = open("/", O_RDONLY);
    if (fd >= 0) {
        fstatfs(fd, &s);
        close(fd);
    }
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 345 / 346  
- [ ] 能说查的是 mount/文件系统  
- [ ] 能对比 path vs fd 找 mount  
- [ ] 能说 update + get + copyout  
- [ ] 填好 `notes/daily/day-35.md`

下一步：Day 36 → [`getfsstat64`](day-36.md)
