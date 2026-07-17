# 源码分析：Day 38（setattrlist / fgetattrlist）

基于 `xnu-12377.121.6`。属性列表的写侧与 FD 读侧。

---

## 1. 心智模型

```text
setattrlist(path, attrlist, values):
  namei → vnode
  copyin 位图 + 校验 SETMASK
  copyin 属性值 → vnode_attr → vnode_setattr

fgetattrlist(fd, attrlist):
  fd → vnode（跳过 namei）
  copyin 位图 → getattrlist_internal → 属性袋 copyout
```

---

## 2. setattrlist

[`vfs_attrlist.c`](../../xnu/bsd/vfs/vfs_attrlist.c)：

```
setattrlist
  NDINIT LOOKUP OP_SETATTR → namei
  setattrlist_internal
    copyin attrlist；bitmapcount / SETMASK
    copyin attributeBuffer
    解析可写字段 → VATTR_* → vnode_setattr
```

不可设的位（如多数 `dirattr`）直接 `EINVAL`。

---

## 3. fgetattrlist

同文件：

```
fp_get_ftype(DTYPE_VNODE) → vnode_getwithref
copyin attrlist
getattrlist_internal(...)   // getattrlist / getattrlistat 也进这里
```

与 Day 37 `getattrlist` 的差别只在定位 vnode 的方式。

---

## 4. 建议点开

1. `syscalls.master` — 221 / 228  
2. `vfs_attrlist.c` — `setattrlist` / `setattrlist_internal`  
3. `vfs_attrlist.c` — `fgetattrlist` → `getattrlist_internal`  
4. `sys/attr.h` — `ATTR_CMN_SETMASK` 等可写掩码  

验收：能说读路径 / 写路径 / FD 读三条链；Demo 能跑。
