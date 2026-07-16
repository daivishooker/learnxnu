# 第十六天（Day 16）正文

学这两个：**`msync` / `madvise`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 15：已经会 `mmap` 建映射。今天学映射建好之后怎么**同步到稳定存储**，以及怎么给内核**访问建议**。

（计划写若无 `madvise` 可读 `mincore`；本树三者都有。今天按表学 **65 / 75**；`mincore` #78 文末顺带一提。）

---

## 今天目标

1. 找到编号 **65 / 75**  
2. 理解 `msync`：把映射区间的脏页按策略同步（对照 `fsync`）  
3. 理解 `madvise`：对映射区间给出访问建议（多为 advisory）  
4. 知道两者都是薄包装，落到 `mach_vm_*`

笔记：[`notes/daily/day-16.md`](../notes/daily/day-16.md)  
分析：[`notes/daily/day-16-analysis.md`](../notes/daily/day-16-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| msync | **65** | 同步（或失效）一段已映射内存 |
| madvise | **75** | 告诉内核这段以后怎么用（建议） |

---

## 1. msync（#65）

[`kern_mman.c`](../xnu/bsd/kern/kern_mman.c)：

```c
msync → msync_nocancel
  校验地址对齐、len≠0
  把 MS_* 转成 VM_SYNC_*
  mach_vm_msync(current_map(), addr, size, sync_flags)
```

常见 flags：

| 标志 | 含义 |
|------|------|
| `MS_SYNC` | 同步等待刷完（默认偏同步） |
| `MS_ASYNC` | 异步发起，不必等完 |
| `MS_INVALIDATE` | 使缓存副本失效（需重新装） |

和 Day 14 `fsync` 对照：

| | `fsync(fd)` | `msync(addr, len, …)` |
|--|-------------|------------------------|
| 对象 | 打开文件 FD | **已 mmap 的地址区间** |
| 典型用途 | 文件写后落盘 | **共享文件映射**写后落盘 |

文件 `MAP_SHARED` 映射被改脏后，常用 `msync` 把这段对应的脏页推回去。

本树：`len == 0` 会直接 `EINVAL`（不像有的系统表示“整段映射”）。

---

## 2. madvise（#75）

```c
madvise(addr, len, behav)
  校验区间
  MADV_* → VM_BEHAVIOR_*
  mach_vm_behavior_set(current_map(), start, size, new_behavior)
```

常见建议：

| behav | 意思 |
|-------|------|
| `MADV_NORMAL` | 默认 |
| `MADV_RANDOM` | 随机访问 |
| `MADV_SEQUENTIAL` | 顺序扫 |
| `MADV_WILLNEED` | 马上要用，可预取 |
| `MADV_DONTNEED` | 暂时不用 |
| `MADV_FREE` 等 | 可丢弃/复用（Darwin 扩展较多） |

要点：源码注释写明 **advisory（建议性）**——内核可以听，不保证立刻怎样；失败/忽略策略因行为而异。

用途直觉：大文件映射顺序读 → `SEQUENTIAL`；用完一大块暂不需要 → `DONTNEED` / `FREE`。

---

## 3. 顺带：mincore（#78）

不问今天必学，但和映射状态很近：

- 查某段地址的页是否在核内（`MINCORE_INCORE`）、是否脏等  
- 用于观察，不是同步、也不是建议  

有兴趣可自己翻 `kern_mman.c` 的 `mincore`。

---

## 今日对比

| | msync | madvise |
|--|-------|---------|
| 强制同步？ | 是（按 flags） | 否，建议 |
| Mach 入口 | `mach_vm_msync` | `mach_vm_behavior_set` |
| 和 fsync | 映射版落盘/失效 | — |

---

## 做完打勾

- [ ] 找到 65 / 75  
- [ ] 能说 msync vs fsync（区间 vs FD）  
- [ ] 能说 madvise 是建议，落到 `mach_vm_behavior_set`  
- [ ] 填好 `notes/daily/day-16.md`

下一步：Day 17 → [`sigaction` / `sigprocmask` / `sigpending`](day-17.md)
