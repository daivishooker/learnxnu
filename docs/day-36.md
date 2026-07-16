# 第三十六天（Day 36）正文

学这个：**`getfsstat64`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 35 查**某一个** mount；今天一次列出**多个（常常是全部）挂载点**的统计。

生活类比：不是问「这个柜子多大」，而是拿出一张表——「仓库里每个柜子多大、剩多少」。

---

## 今天目标

1. 找到编号 **347**  
2. 理解 `vfs_iterate` 扫 mount 列表，逐个 `copyout` `statfs64`  
3. 理解 `buf == NULL` 时可只返回个数；`MNT_NOWAIT` / `MNT_WAIT` 影响是否刷新缓存  
4. 能对比：`statfs64`（一个）vs `getfsstat64`（一批）  

笔记：[`notes/daily/day-36.md`](../notes/daily/day-36.md)  
分析：[`notes/daily/day-36-analysis.md`](../notes/daily/day-36-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getfsstat64 | **347** | 获取（多个）文件系统统计 |

---

## 1. getfsstat64（#347）主路径

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
getfsstat64(buf, bufsize, flags) {
    maxcount = bufsize / sizeof(statfs64)
    vfs_iterate(..., getfsstat64_callback, &fst)
      // 对每个 mount：
      //   非 NOWAIT 时 vfs_update_vfsstat
      //   vfs_get_statfs64 → copyout 到用户数组
    *retval = 实际个数（或受 maxcount 限制）
}
```

要点：

- **无路径/FD**：直接扫内核挂载列表  
- 用户缓冲是 `struct statfs64[]`  
- `flags`：`MNT_NOWAIT` 可不刷新；`MNT_WAIT` 倾向刷新统计  

和 Day 34 `sync`、Day 35 `statfs64`：都碰 mount；一个刷盘、一个查一个、一个列一串。

---

## 用户层 Demo

列出本机各挂载点的类型与容量（Darwin 上用户接口常是 `getfsstat`）：

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/mount.h>

int main(void) {
    int n = getfsstat(NULL, 0, MNT_NOWAIT);  /* 先问有多少个 */
    if (n < 0) { perror("getfsstat"); return 1; }

    struct statfs *buf = calloc((size_t)n, sizeof(*buf));
    if (!buf) { perror("calloc"); return 1; }

    n = getfsstat(buf, (int)(n * sizeof(*buf)), MNT_NOWAIT);
    if (n < 0) { perror("getfsstat2"); free(buf); return 1; }

    for (int i = 0; i < n; i++) {
        printf("%-12s %-20s blocks=%lld bfree=%lld\n",
               buf[i].f_fstypename,
               buf[i].f_mntonname,
               (long long)buf[i].f_blocks,
               (long long)buf[i].f_bfree);
    }
    free(buf);
    return 0;
}
```

```bash
cc -o getfsstat_demo getfsstat_demo.c && ./getfsstat_demo
```

---

## 做完打勾

- [ ] 找到 347  
- [ ] 能说 vfs_iterate 扫 mount  
- [ ] 能对比 statfs64 vs getfsstat64  
- [ ] 跑通上面 Demo  
- [ ] 填好 `notes/daily/day-36.md`

下一步：Day 37 → `getdirentries64` / `getattrlist`（目录枚举与属性，编号以 master 为准）
