# 第十五天（Day 15）正文

学这三个：**`mmap` / `munmap` / `mprotect`**  
源码：`xnu/` = **xnu-12377.121.6**

进入第 3 周：内存。承接 Day 14 的 UBC 讨论——今天看用户态如何把文件（或匿名内存）**映射进自己的地址空间**。

---

## 今天目标

1. 找到编号 **197 / 73 / 74**  
2. 理解 `mmap`：在进程 `vm_map` 里开一块映射（匿名或文件）  
3. 理解文件映射经 **UBC** 接到 Mach VM  
4. 理解 `munmap` 拆映射、`mprotect` 改保护位

笔记：[`notes/daily/day-15.md`](../notes/daily/day-15.md)  
分析：[`notes/daily/day-15-analysis.md`](../notes/daily/day-15-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| mmap | **197** | 映射内存（匿名或文件）到进程地址空间 |
| munmap | **73** | 取消一段映射 |
| mprotect | **74** | 改一段映射的读/写/执行权限 |

---

## 1. mmap（#197）

[`kern_mman.c`](../xnu/bsd/kern/kern_mman.c)：

```c
mmap(addr, len, prot, flags, fd, pos) {
    user_map = current_map()           // 当前进程的 Mach vm_map
    校验/对齐地址、长度、prot、flags

    if (MAP_ANON) {
        // 匿名：不绑文件
        mach_vm_map_kernel(user_map, …, IPC_PORT_NULL, …)
    } else {
        // 文件：fd → vnode
        control = ubc_getobject(vp, …) // 经 UBC 拿到 VM 控制口
        mach_vm_map_kernel(user_map, …, control, file_pos, …)
    }
    *retval = 映射起始地址
}
```

要点：

- **BSD 系统调用外壳** → 真正干活多在 **Mach VM**（`mach_vm_map_kernel`）  
- **`MAP_ANON`**：匿名页（堆式扩展、私有内存等）  
- **带 fd**：文件映射；`ubc_getobject` 正是昨天说的 **vnode ↔ UBC ↔ VM** 桥  
- **`MAP_SHARED` / `MAP_PRIVATE`**：共享改写 vs 写时复制（COW）  
- 访问映射地址时才真正缺页装入（和 page cache 同一套故事）

和 `read`/`write` 对照：  
`read` 是拷进用户缓冲；`mmap` 是让用户地址**直接指向**（经页表）缓存/匿名页。

---

## 2. munmap（#73）

```c
munmap(addr, len) {
    对齐/校验
    mach_vm_deallocate_kernel(current_map(), addr, size)
}
```

去掉这段虚拟地址上的映射；之后再访问通常会故障。  
文件映射去掉的是**映射关系**；文件和 UBC 里的缓存页不一定立刻消失（别的引用还在）。

---

## 3. mprotect（#74）

```c
mprotect(addr, len, prot) {
    对齐/校验；整理 prot（读/写/执行）
    mach_vm_protect(current_map(), addr, size, …, prot)
}
```

改已有映射的保护位，例如：

- 把某段改成只读  
- 代码区 `RX`、数据区 `RW`（安全上很常见）

硬件上最终体现在页表权限。

---

## 今日对比

| | mmap | munmap | mprotect |
|--|------|--------|----------|
| 建映射？ | 是 | 否（拆） | 否（改权限） |
| 接 Mach VM？ | `mach_vm_map_kernel` | `mach_vm_deallocate_kernel` | `mach_vm_protect` |
| 文件路径？ | 可经 UBC | — | — |

---

## 做完打勾

- [ ] 找到 197 / 73 / 74  
- [ ] 能说 mmap：BSD 入口 → Mach `vm_map`；文件走 UBC  
- [ ] 能说 ANON vs 文件映射；SHARED vs PRIVATE  
- [ ] 能说 munmap / mprotect 各自调哪个 mach_vm_*  
- [ ] 填好 `notes/daily/day-15.md`

下一步：Day 16 → [`msync` / `madvise`](day-16.md)
