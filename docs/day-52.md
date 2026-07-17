# 第五十二天（Day 52）正文

学这两个：**`getattrlistbulk` / `fsctl`**  
源码：`xnu/` = **xnu-12377.121.6**

一个是「目录里批量点菜取属性」（比反复 `getattrlist` 更省）；一个是「对文件系统发专用控制命令」（像面向 FS 的 ioctl）。

生活类比：

1. `getattrlistbulk`：进一间目录，按清单一次抄出多件物品的标签  
2. `fsctl`：对整卷/某个 FS 对象喊一句专有口令（快照、标志 CAS 等）

---

## 今天目标

1. 找到编号 **461 / 242**  
2. 理解 `getattrlistbulk`：目录 FD → `VNOP_GETATTRLISTBULK`（或默认 `readdirattr`）  
3. 理解 `fsctl`：路径 → `fsctl_internal`（按 `cmd` 分发）  
4. 能对比：单对象 `getattrlist` vs 目录批量；`fsctl` vs 普通 `ioctl`  

笔记：[`notes/daily/day-52.md`](../notes/daily/day-52.md)  
分析：[`notes/daily/day-52-analysis.md`](../notes/daily/day-52-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getattrlistbulk | **461** | 对目录 FD 批量取条目属性 |
| fsctl | **242** | 按路径对 FS/对象发控制命令 |

（FD 版控制：`ffsctl` #245。）

---

## 1. getattrlistbulk（#461）——目录批量属性

[`vfs_attrlist.c`](../xnu/bsd/vfs/vfs_attrlist.c)：

```c
getattrlistbulk(dirfd, alist, attributeBuffer, bufferSize, options) {
    fp_getfvp(dirfd) → dvp；需 FREAD
    必须是 VDIR（可选项切到 snapshot 目录）
    copyin(attrlist)
    必须含 ATTR_BULK_REQUIRED（NAME + RETURNED_ATTRS）
    authorize LIST_DIRECTORY（可能还要 SEARCH）
    VNOP_GETATTRLISTBULK(...)     // FS 原生批量
      若 ENOTSUP → readdirattr 默认实现
    更新目录偏移；retval = 本批条目数
}
```

要点：

- 输入是**已打开的目录 FD**（不是路径）  
- 一次返回多条「属性袋」，适合列目录并带元数据（比 `readdir` + 每个再 `getattrlist` 更整）  
- 偏移记在 `fileglob` / `fd_vn_data`，可多次调用直到 EOF  
- 与 Day 37 `getattrlist`：单个对象 vs 目录批量  

---

## 2. fsctl（#242）——文件系统控制

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
fsctl(path, cmd, data, options) {
    namei(path) → vp
    （设备 vnode → ENOTTY）
    fsctl_internal:
      按 IOC 方向 copyin/copyout data
      switch (cmd) 处理各种 FSIOC_* / 特殊命令
      许多最终问 mount / vnode / FS 私有逻辑
}
```

要点：

- 形态像 **ioctl**，但面向 **VFS/文件系统**（不是字符设备驱动那套为主）  
- `cmd` 决定语义：BSD flags CAS、firmlink、磁盘调节器、FS 私有扩展……  
- 对 `VCHR`/`VBLK` 直接 `ENOTTY`（设备请走 `ioctl`）  
- `ffsctl`：已有 FD，跳过 `namei`  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/attr.h>
#include <sys/mount.h>
#include <unistd.h>
#include <errno.h>

/* Demo A：getattrlistbulk — 列 /tmp 里一批名字 */
static void demo_bulk(void) {
    struct attrlist al;
    char buf[64 * 1024];
    int dirfd, n;

    memset(&al, 0, sizeof(al));
    al.bitmapcount = ATTR_BIT_MAP_COUNT;
    /* ATTR_BULK_REQUIRED = NAME | RETURNED_ATTRS；再要 OBJTYPE 利于原生实现 */
    al.commonattr = ATTR_CMN_NAME | ATTR_CMN_RETURNED_ATTRS | ATTR_CMN_OBJTYPE;

    dirfd = open("/tmp", O_RDONLY);
    if (dirfd < 0) { perror("open /tmp"); return; }

    n = getattrlistbulk(dirfd, &al, buf, sizeof(buf), 0);
    if (n < 0) {
        perror("getattrlistbulk");
        close(dirfd);
        return;
    }
    printf("getattrlistbulk returned %d entries (packed attrs in buffer)\n", n);

    /* 缓冲布局较绕：每条以 length 头开始；这里只验证调用成功 */
    close(dirfd);
}

/* Demo B：fsctl — 对普通路径发未知/无效 cmd，观察入口 */
static void demo_fsctl(void) {
    /* cmd=0 通常无效；用于确认 syscall 存在，不依赖特定 FSIOC */
    if (fsctl("/tmp", 0, NULL, 0) != 0) {
        printf("fsctl probe: %s (expected failure for cmd=0)\n", strerror(errno));
    }
}

int main(void) {
    demo_bulk();
    demo_fsctl();
    return 0;
}
```

```bash
cc -o day52_demo day52_demo.c && ./day52_demo
```

（需 Darwin。重点看 `getattrlistbulk`；`fsctl` 的具体 `FSIOC_*` 随场景选用。）

---

## 做完打勾

- [ ] 找到 461 / 242  
- [ ] 能说 getattrlistbulk：目录 FD → VNOP_GETATTRLISTBULK  
- [ ] 能说 fsctl：namei → fsctl_internal 按 cmd 分发  
- [ ] 跑通 Demo（至少 bulk）  
- [ ] 填好 `notes/daily/day-52.md`

下一步：Day 53 → `openat` / `fstatat64`（#463 / #470）
