# 源码分析：Day 49（symlink / symlinkat）

基于 `xnu-12377.121.6`。创建符号链接。

---

## 1. 心智模型

```text
symlink(target_str, link_path):
  copyinstr(target_str)
  nameiat(CREATE, link_path) → 父目录
  VNOP_SYMLINK → 新 VLNK，内容为 target_str
```

---

## 2. 内部

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
symlinkat_internal
  copyinstr 目标串
  NDINIT CREATE OP_SYMLINK → nameiat
  已存在 → EEXIST
  va_type = VLNK；authorize ADD_FILE
  VNOP_SYMLINK(dvp, &vp, cnp, &va, path)
```

参数：`symlink(path, link)` 里 `path`=目标串，`link`=新链接路径。

---

## 3. 建议点开

1. `syscalls.master` — 57 / 474  
2. `vfs_syscalls.c` — `symlink` / `symlinkat` / `symlinkat_internal`  
3. 对照 Day 48 `readlink`  

验收：能说创建与读取成对；Demo 能跑。
