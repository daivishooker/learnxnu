# 源码分析：Day 15（mmap / munmap / mprotect）

基于 `xnu-12377.121.6`。BSD 内存映射与 Mach VM。

---

## 1. 心智模型

```text
用户地址空间（vm_map）
   │ mmap
   ├─ MAP_ANON ──────────────► 匿名 vm 对象（无文件）
   │
   └─ 带 fd 的文件映射
         fd → vnode → UBC(ubc_getobject) → memory_object_control
                              │
                              └─ mach_vm_map_kernel 挂进 vm_map

之后访问 va：缺页 → vnode_pager / 匿名 pager → 物理页
（文件路径与 Day 14 的 page cache / UBC 同一座桥）
```

---

## 2. mmap 主路径

[`kern_mman.c`](../../xnu/bsd/kern/kern_mman.c)：

```
mmap
  current_map()
  mmap_sanitize（对齐、长度、prot、flags）
  分支：
    MAP_ANON:
      mach_vm_map_kernel(..., 无 pager/control, prot, inherit)
    否则:
      fp_lookup(fd) → vnode
      ubc_getobject(vp) → control   // UBC 桥
      mach_vm_map_kernel(..., control, file_pos, prot, inherit)
  返回映射基址 *retval
```

**flags 教学重点：**

| 标志 | 含义 |
|------|------|
| `MAP_ANON` | 匿名内存，fd 常忽略 |
| `MAP_SHARED` | 改写可与他人/文件共享可见 |
| `MAP_PRIVATE` | 私有；写时常 COW |
| `MAP_FIXED` | 尽量用指定地址（危险，慎用） |

**prot：** `PROT_READ` / `WRITE` / `EXEC` → VM 保护位。本树里写/执行常会顺带隐含读（硬件限制相关注释）。

---

## 3. munmap / mprotect

```
munmap
  munmap_sanitize
  mach_vm_deallocate_kernel(map, addr, size)

mprotect
  mprotect_sanitize
  mach_vm_protect(map, addr, size, …, prot)
```

都是薄 BSD 包装：参数整理后交给 Mach VM。

---

## 4. 和 UBC / fsync 的关系

| 操作 | 关系 |
|------|------|
| `mmap` 文件 | 经 UBC 把文件缓存对象映进地址空间 |
| 访问映射 | 缺页时装页（page cache 那套） |
| `MAP_SHARED` 写入 | 脏页可回到文件缓存 |
| `fsync` | 不经 mmap 也能刷；映射脏页同样最终要回写机制处理 |
| `munmap` | 去掉映射，不等于立刻丢掉全部缓存页 |

Day 16 的 `msync` 会更直接谈「映射区间与同步」。

---

## 5. 建议点开的文件

1. `syscalls.master` — 197 / 73 / 74  
2. `kern_mman.c` — `mmap` 里 `MAP_ANON` vs `ubc_getobject` 分支  
3. `kern_mman.c` — `munmap` / `mprotect` 末尾的 `mach_vm_*`  
4. （可选）`bsd/vm/vnode_pager.c` — 文件页从哪来  

验收：能画「mmap 文件 = vnode → UBC → vm_map」；能区分 ANON / SHARED / PRIVATE。
