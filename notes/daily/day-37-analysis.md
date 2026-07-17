# 源码分析：Day 37（getdirentries64 / getattrlist）

基于 `xnu-12377.121.6`。目录枚举与 Darwin 属性列表。

---

## 1. 心智模型

```text
getdirentries64(dirfd):
  fd → 目录 vnode → VNOP_READDIR / readdir64 → 用户缓冲里的目录项流

getattrlist(path, attrlist):
  copyin 请求位图 → namei → vnode → 收集属性 → 属性袋 copyout
```

---

## 2. getdirentries64

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
getdirentries_common
  校验目录、可读
  vnode_readdir64(..., VNODE_READDIR_EXTENDED) 或 VNOP_READDIR
  更新 fg_offset；copyout position
```

---

## 3. getattrlist

[`vfs_attrlist.c`](../../xnu/bsd/vfs/vfs_attrlist.c)：

```
copyin struct attrlist
getattrlistat_internal(..., AT_FDCWD)
  查路径、按位图取属性、写入 attributeBuffer
```

细节很多（对齐、packed header）；今天跟到「点菜 → 打包」即可。

---

## 4. 建议点开

1. `syscalls.master` — 344 / 220  
2. `vfs_syscalls.c` — `getdirentries64` / `getdirentries_common`  
3. `vfs_attrlist.c` — `getattrlist`  

验收：能说目录枚举与属性点菜两条链；Demo 能跑。
