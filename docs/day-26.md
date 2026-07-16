# 第二十六天（Day 26）正文

学这三个：**`shm_open` / `shm_unlink` / `mmap`（回顾）**  
源码：`xnu/` = **xnu-12377.121.6**

离开网络一周，看 **POSIX 共享内存**：用名字打开一块可共享的内存对象，再用 Day 15 的 `mmap` 映进进程地址空间。

生活类比：

1. `shm_open`：在内核登记室开一个**有名字的白板**，给你一把钥匙（FD）  
2. `ftruncate`（常用后续，今天捎带）：规定白板多大，真正挂上内存  
3. `mmap(MAP_SHARED)`：把白板映到你桌上，别人用同一名字打开也能映到**同一块物理内容**  
4. `shm_unlink`：从登记室**摘掉名字**；还有人握着钥匙/映射时，白板物体可以还在  

---

## 今天目标

1. 找到编号 **266 / 267 / 197**  
2. 理解 `shm_open`：按名字找到/创建 `pshm` 对象，返回 FD（`pshmops`）  
3. 理解 `shm_unlink`：从名字缓存移除，不立刻等同销毁  
4. 回顾 `mmap`：对 `DTYPE_PSXSHM` 走 `pshm_mmap`，须 `MAP_SHARED`  

笔记：[`notes/daily/day-26.md`](../notes/daily/day-26.md)  
分析：[`notes/daily/day-26-analysis.md`](../notes/daily/day-26-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| shm_open | **266** | 打开/创建命名共享内存，返回 FD |
| shm_unlink | **267** | 按名字解除链接 |
| mmap | **197** | 把该 FD 映射进进程 VA（回顾） |

---

## 1. shm_open（#266）——拿到共享内存的 FD

[`posix_shm.c`](../xnu/bsd/kern/posix_shm.c)：

```c
shm_open(name, oflag, mode) {
    pshm_get_name(...)           // copyin 名字
    falloc → 新 FD
    在 pshm 缓存里查找（O_CREAT 可新建 pshm_info）
    fp->f_ops = pshmops
    fp_set_data(fp, pshmnode → pshm_info)
    返回 fd
}
```

要点：

- 像 `open`，但对象是 **POSIX shm**（`DTYPE_PSXSHM`），不是普通 vnode 文件  
- 内核里有一份按**名字**索引的缓存（`pshm_info`）  
- 刚 `shm_open` 时长度常为 0；实际内存多在之后 **`ftruncate`** 里通过 Mach memory entry 分配（`pshm_truncate`）

---

## 2. shm_unlink（#267）——摘掉名字

```c
shm_unlink(name) {
    查找 pshm_info
    权限检查
    pshm_unlink_internal  // 从名字缓存删除，标 PSHM_REMOVED
}
```

和文件 `unlink` 类似：**名字没了**，已打开的 FD / 已建立的映射还可以继续用，直到最后引用放下。

---

## 3. mmap（#197）回顾——映进地址空间

[`kern_mman.c`](../xnu/bsd/kern/kern_mman.c) 里按 FD 类型分叉：

```c
mmap(..., fd, ...) {
    switch (dtype) {
    case DTYPE_PSXSHM:
        return pshm_mmap(...);   // 必须 MAP_SHARED
    case DTYPE_VNODE:
        // Day 15：文件 / UBC 路径
    }
}
```

`pshm_mmap`：把 `pshm_info` 上挂的 memory object 映进当前进程 `vm_map`。  
两个进程对同一名字 `shm_open` + `mmap(MAP_SHARED)` → 看到**同一块共享内容**（改了对方可见）。

和 Day 15 对照：

| | 文件 mmap | POSIX shm mmap |
|--|-----------|----------------|
| FD 来自 | `open` 路径/vnode | `shm_open` / `pshm` |
| 后端 | UBC / vnode | Mach memory object（`pshm_mobjs`） |
| 典型 flags | SHARED/PRIVATE | **必须 SHARED** |

---

## 今日串起来

```text
进程 A: shm_open("/x", O_CREAT|O_RDWR) → ftruncate(size) → mmap(MAP_SHARED)
进程 B: shm_open("/x", O_RDWR)         → mmap(MAP_SHARED)
        两边 VA 不同，背后同一块共享内存
之后:   shm_unlink("/x")  // 名字没了；映射仍可留到 munmap/close
```

| 调用 | 内核关键动作 |
|------|----------------|
| shm_open | 名字缓存 + `falloc` + `pshmops` |
| shm_unlink | 名字缓存移除 |
| mmap(shm fd) | `pshm_mmap` → Mach `vm_map` |

心智模型：  
**名字 → 共享对象；FD → 进程把手；mmap → 进程 VA 接到同一块内存。**  
这和 socket「地址 demux」不同：这里是**共享同一物理/memory object**，不是收发包。

---

## 做完打勾

- [ ] 找到 266 / 267 / 197  
- [ ] 能说 shm_open 返回 FD，背后是 pshm_info  
- [ ] 能说 shm_unlink 摘名字，对象可仍存活  
- [ ] 能说 mmap 对 PSXSHM 走 pshm_mmap，要 MAP_SHARED  
- [ ] 填好 `notes/daily/day-26.md`

下一步：Day 27 → `ptrace` / `sysctl`（回顾安全相关）
