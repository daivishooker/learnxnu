# 源码分析：Day 26（shm_open / shm_unlink / mmap）

基于 `xnu-12377.121.6`。POSIX 共享内存与 mmap 对接。

---

## 1. 心智模型

```text
名字 "/foo"
  → pshm_info（内核缓存，引用计数）
       → pshm_mobjs（Mach memory object 列表，ftruncate 后才有）
            ↑
进程 A: fdA → pshmnode → pshm_info → mmap → VA_A
进程 B: fdB → pshmnode → 同一 pshm_info → mmap → VA_B
```

两边 VA 可以不同；改共享页，对方能看见（`MAP_SHARED`）。

---

## 2. shm_open 主路径

[`posix_shm.c`](../../xnu/bsd/kern/posix_shm.c)：

```
pshm_get_name（copyin 名字）
falloc → fd
PSHM 锁下 pshm_cache_search
  命中：加引用（O_EXCL 冲突则失败）
  未命中：需 O_CREAT，pshm_cache_add
fp->f_ops = pshmops；数据 = pshmnode{pinfo}
返回 fd
```

长度初始多为 0；`pshm_truncate`（经 `ftruncate`）里 `mach_make_memory_entry_64` 挂上真正内存。

---

## 3. shm_unlink 主路径

```
copyin 名字 → 缓存查找
权限 / MAC
pshm_unlink_internal → 名字摘掉（PSHM_REMOVED）
引用归零时 pshm_deref 才释放 memory object
```

---

## 4. mmap 分叉（回顾 Day 15）

[`kern_mman.c`](../../xnu/bsd/kern/kern_mman.c)：

```
mmap
  DTYPE_PSXSHM → pshm_mmap（要求 MAP_SHARED）
  DTYPE_VNODE  → 文件/UBC 路径（Day 15）
```

`pshm_mmap`：从 `pinfo->pshm_mobjs` 取 memory object，映射进 `current_map()`。

---

## 5. 和 socket / 文件对照

| | POSIX shm | 文件 mmap | socket |
|--|-----------|-----------|--------|
| 打开 | shm_open | open | socket |
| 进程把手 | FD | FD | FD |
| 共享方式 | 同一 memory object | UBC 页 | 否（拷贝收发） |
| 摘名 | shm_unlink | unlink | — |

---

## 6. 建议点开的文件

1. `syscalls.master` — 266 / 267 / 197  
2. `posix_shm.c` — `shm_open` / `shm_unlink` / `pshm_truncate` / `pshm_mmap` 头  
3. `kern_mman.c` — `DTYPE_PSXSHM` 分支  

验收：能画「两进程同一名字 → 两 FD → 两 VA → 一块共享内存」；能说 unlink 只摘名。
