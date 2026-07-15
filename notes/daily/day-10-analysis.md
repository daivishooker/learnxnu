# 源码分析：Day 10（link / rename）

基于 `xnu-12377.121.6`。硬链接与改名。

---

## 0. 硬链接 vs 符号链接（「浮动链接」）

若你说的 floating = soft/symbolic link：

| | `link` 硬链接 | `symlink` 符号链接 |
|--|---------------|-------------------|
| vnode | 共用已有 vnode | **新建** `VLNK` vnode，内容是路径字符串 |
| 删除一个名字 | 链接数 -1；还有名则文件在 | 删的是链接这个小节点 |
| 源码入口 | `link` → `linkat_internal` → `VNOP_LINK` | `symlink` → `symlinkat_internal`，`va_type=VLNK` |

今天主课是 **`link` + `rename`**；`symlink` 对照看一眼即可。

---

## 1. link：给已有 vnode 再挂一名

```
link (#9)
  → linkat_internal(oldpath, newpath)
       namei LOOKUP oldpath → vp
       if VDIR && 文件系统不支持目录硬链 → EPERM
       namei CREATE newpath → dvp（父目录），新名应不存在
       VNOP_LINK(vp, dvp, ...)
```

要点回顾你前面的问题：

- **不新建数据 vnode**  
- 新父目录是 **newpath 所在目录**；旧父目录仍保留旧名字  
- 所以 vnode 可以有**多个父目录（多个目录项）**

---

## 2. rename：挪目录项

```
rename (#128)
  → renameat_internal(from, to)
       解析 from：源父目录 + 源 vnode
       解析 to：目标父目录 + 目标名
       VNOP_RENAME / compound rename
```

直觉：

- `rename("a.txt", "b.txt")`：同目录改名  
- `rename("a.txt", "subdir/a.txt")`：名字搬到另一目录  
- 通常**同一文件系统**；跨设备常失败或需用户态拷贝（`EXDEV`）

链接计数：单纯改名一般不变；若 `to` 已存在被替换，被替换对象按 unlink 语义处理。

---

## 3. 和 Day 9 串起来

```
mkdir   新建目录 vnode + 目录项
unlink  删一个名字（可能减链接）
link    加一个名字（硬链接，+链接）
rename  移动/改名一个名字
```

---

## 4. 建议点开的文件

1. `syscalls.master` — 9 / 128（可选再看 `symlink`）  
2. `vfs_syscalls.c` — `link` + `linkat_internal` 前半（两次 namei + `VNOP_LINK`）  
3. `vfs_syscalls.c` — `rename` → `renameat_internal` 入口  
4. （对照）`symlinkat_internal` 里 `va_type = VLNK`  

验收：能说明 hard link 不新建 vnode；rename 是搬名字不是复制内容。
