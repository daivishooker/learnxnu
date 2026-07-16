# 第三十四天（Day 34）正文

学这两个：**`sync` / `fsync`（回顾）**  
源码：`xnu/` = **xnu-12377.121.6**

Day 14 已见 `fsync`；今天加上全系统的 **`sync`**，把「刷脏页到稳定存储」两条入口对照清楚。

生活类比：

1. `fsync(fd)`：把**这一本打开的笔记**赶紧誊到保险柜  
2. `sync()`：喊一声「所有柜子能刷的都刷一遍」（遍历挂载点）

---

## 今天目标

1. 找到编号 **36 / 95**  
2. 理解 `sync`：`vfs_iterate` → 各 mount 的 `VFS_SYNC`  
3. 回顾 `fsync`：FD → vnode → `VNOP_FSYNC`（`MNT_WAIT`）  
4. 能对比：全系统 vs 单文件；顺带知道 `fdatasync`（#187）偏数据完整性  

笔记：[`notes/daily/day-34.md`](../notes/daily/day-34.md)  
分析：[`notes/daily/day-34-analysis.md`](../notes/daily/day-34-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sync | **36** | 同步（几乎）所有可写文件系统的脏数据 |
| fsync | **95** | 同步某个打开文件对应的 vnode |

---

## 1. sync（#36）——扫一遍挂载点

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
sync() {
    vfs_iterate(..., sync_callback, NULL)
}

sync_callback(mp) {
    if (!只读) VFS_SYNC(mp, waitfor, …)   // 落到该文件系统
}
```

要点：

- **无 FD**：对整个 VFS 挂载列表动手  
- 每个文件系统自己实现 `VFS_SYNC`（刷缓冲、元数据等）  
- 默认路径里 wait 语义偏 `MNT_NOWAIT`（尽快发起，不在每个 mount 上死等同一套语义）——细节跟到「遍历 + VFS_SYNC」即可  

---

## 2. fsync（#95）——盯住一个 FD（回顾）

```c
fsync(fd) → fsync_common(..., MNT_WAIT) {
    fp_getfvp → vnode
    VNOP_FSYNC(vp, MNT_WAIT, ctx)   // 文件完整性：数据+相关元数据
}
```

对照：

| | fsync | fdatasync (#187) |
|--|-------|------------------|
| 标志 | `MNT_WAIT` | `MNT_DWAIT` |
| 直觉 | 文件内容 + 更多元数据 | 偏「数据能读回来」 |

和 Day 16 `msync`：mmap 区间同步；`fsync` 是打开文件/vnode 路径。

---

## 3. 今日对比

| | sync | fsync |
|--|------|-------|
| 范围 | 多个 mount | 一个 FD → 一个 vnode |
| 入口 | `VFS_SYNC` | `VNOP_FSYNC` |
| 典型用途 | 「系统层面冲一下」 | 「这个文件先落稳」 |

```text
write(fd) → 可能还在页缓存/脏缓冲
fsync(fd) → 尽量让该文件变「稳」
sync()    → 尽量让各文件系统脏数据推进去
```

注意：调用返回不总等于「物理盘已经绝对永不丢」——还取决于硬件写缓存等；内核语义是推进到稳定存储路径。

---

## 做完打勾

- [ ] 找到 36 / 95  
- [ ] 能说 sync：vfs_iterate → VFS_SYNC  
- [ ] 能说 fsync：FD → VNOP_FSYNC  
- [ ] 能对比全系统 vs 单文件  
- [ ] 填好 `notes/daily/day-34.md`

下一步：Day 35 → `statfs64` / `fstatfs64`（文件系统统计）
