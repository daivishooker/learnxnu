# 源码分析：Day 35（statfs64 / fstatfs64）

基于 `xnu-12377.121.6`。文件系统统计查询。

---

## 1. 心智模型

```text
statfs64(path):  namei → vnode → mount
fstatfs64(fd):   fd → vnode → mount
                     ↓
              vfs_update_vfsstat
              vfs_get_statfs64 → copyout(statfs64)
```

不是 `stat` 那种 inode 属性；是整卷/挂载点信息。

---

## 2. 主路径

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：两条在拿到 `mp` 之后合流。

可对照旧接口 `statfs`/`fstatfs`（#157/#158）与 `getfsstat64`（列举多个）。

---

## 3. 建议点开

1. `syscalls.master` — 345 / 346  
2. `vfs_syscalls.c` — `statfs64` / `fstatfs64`  

验收：能说 path/fd 如何找到 mount；能对比 Day 7 stat。
