# 源码分析：Day 16（msync / madvise）

基于 `xnu-12377.121.6`。映射同步与访问建议。

---

## 1. 心智模型

```text
Day 15：mmap 建映射（VA ↔ 内存对象）
Day 16：
  msync   → 这段脏了？按 flags 刷 / 失效
  madvise → 这段我打算怎么用？告诉 VM 调策略
```

接昨天：文件映射经 UBC；`MAP_SHARED` 写入弄脏页后，可用 `msync` 推回文件侧。

---

## 2. msync 主路径

[`kern_mman.c`](../../xnu/bsd/kern/kern_mman.c)：

```
msync（可取消）
  → msync_nocancel
       msync_sanitize：起始对齐；len==0 → EINVAL
       MS_SYNC / MS_ASYNC / MS_INVALIDATE / …
         → VM_SYNC_SYNCHRONOUS / ASYNCHRONOUS / INVALIDATE …
       mach_vm_msync(map, addr, size, sync_flags)
```

错误映射（节选）：`KERN_INVALID_ADDRESS`（有洞）→ `ENOMEM`；`KERN_FAILURE` → `EIO`。

**和 fsync：**

- `fsync(fd)`：整文件打开描述相关脏数据（VFS 路径）  
- `msync(addr,len)`：指定映射窗口；更贴“我改了这段映射”

---

## 3. madvise 主路径

```
madvise
  madvise_sanitize
  switch (behav)：
    MADV_RANDOM / SEQUENTIAL / WILLNEED / DONTNEED / FREE / …
      → VM_BEHAVIOR_*
  mach_vm_behavior_set(map, start, size, new_behavior)
```

教学上先抓：

- `WILLNEED`：可能预取  
- `DONTNEED` / `FREE`：暗示可回收  
- `SEQUENTIAL` / `RANDOM`：影响预读等策略  

源码写明默认按 **conservative / advisory** 理解——别当成硬保证。

---

## 4. 和 Day 14–15 串起来

| 调用 | 角色 |
|------|------|
| `mmap` | 建映射 |
| `mprotect` | 改权限 |
| `msync` | 映射区间同步/失效 |
| `fsync` | FD/文件落盘 |
| `madvise` | 用法建议 |
| `munmap` | 拆映射 |

---

## 5. 建议点开的文件

1. `syscalls.master` — 65 / 75（可选看 78 `mincore`）  
2. `kern_mman.c` — `msync_nocancel` 的 flags → `VM_SYNC_*`  
3. `kern_mman.c` — `madvise` 的 `MADV_*` → `VM_BEHAVIOR_*`  
4. `sys/mman.h` — 标志定义  

验收：能说清「改完共享映射 → msync」和「大段暂不用 → madvise」。
