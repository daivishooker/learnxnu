# 源码分析：Day 52（getattrlistbulk / fsctl）

基于 `xnu-12377.121.6`。目录批量属性与 FS 控制。

---

## 1. 心智模型

```text
getattrlistbulk(dirfd, attrlist):
  目录 vnode → VNOP_GETATTRLISTBULK → 多条属性袋；可续读

fsctl(path, cmd, data):
  namei → fsctl_internal(switch cmd) → mount/FS 私有逻辑
```

---

## 2. getattrlistbulk

[`vfs_attrlist.c`](../../xnu/bsd/vfs/vfs_attrlist.c)：

```
fp_getfvp；VDIR；FREAD
copyin attrlist；需 ATTR_BULK_REQUIRED
VNOP_GETATTRLISTBULK；ENOTSUP → readdirattr
retval = count；偏移在 fg_vn_data / fg_offset
```

---

## 3. fsctl

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
fsctl: namei → fsctl_internal
ffsctl: file_vnode → 同一 internal
设备 VCHR/VBLK → ENOTTY
```

---

## 4. 建议点开

1. `syscalls.master` — 461 / 242  
2. `vfs_attrlist.c` — `getattrlistbulk`  
3. `vfs_syscalls.c` — `fsctl` / `fsctl_internal`  
4. `sys/attr.h` — `ATTR_BULK_REQUIRED`  

验收：能对比 getattrlist vs bulk；Demo 至少跑通 bulk。
