# 源码分析：Day 42（getxattr / setxattr）

基于 `xnu-12377.121.6`。扩展属性读写。

---

## 1. 心智模型

```text
getxattr(path, name):
  namei → vn_getxattr → VNOP_GETXATTR（可 default_getxattr）

setxattr(path, name, value):
  namei → vn_setxattr → VNOP_SETXATTR
```

---

## 2. 系统调用层

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
getxattr:  copyinstr 名；可选 UIO_READ；vn_getxattr
setxattr:  copyinstr 名；UIO_WRITE；vn_setxattr；FSE 通知
```

FD 版：`fgetxattr` / `fsetxattr`（#235 / #237）跳过 path namei。

---

## 3. 公共包装

[`vfs_xattr.c`](../../xnu/bsd/vfs/vfs_xattr.c)：

```
vn_getxattr / vn_setxattr
  校验 vnode / 名字
  authorize READ/WRITE_EXTATTRIBUTES
  VNOP_*XATTR；ENOTSUP 时可走 default_* 路径
```

标志见 `sys/xattr.h`：`XATTR_CREATE`、`XATTR_REPLACE`、`XATTR_NOFOLLOW`。

---

## 4. 建议点开

1. `syscalls.master` — 234 / 236  
2. `vfs_syscalls.c` — `getxattr` / `setxattr`  
3. `vfs_xattr.c` — `vn_getxattr` / `vn_setxattr`  

验收：能说与 getattrlist 的差别；Demo 能跑。
