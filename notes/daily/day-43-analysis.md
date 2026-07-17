# 源码分析：Day 43（listxattr / removexattr）

基于 `xnu-12377.121.6`。扩展属性列举与删除。

---

## 1. 心智模型

```text
listxattr(path):
  namei → vn_listxattr → VNOP_LISTXATTR → NUL 分隔名列表

removexattr(path, name):
  copyinstr(name) → namei → vn_removexattr → VNOP_REMOVEXATTR
```

---

## 2. 系统调用层

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
listxattr:    namei；可选 UIO 填 namebuf；vn_listxattr
removexattr:  copyinstr 名；namei；vn_removexattr；FSE_XATTR_REMOVED
```

---

## 3. 公共包装

[`vfs_xattr.c`](../../xnu/bsd/vfs/vfs_xattr.c)：

```
vn_listxattr:   authorize READ_EXTATTRIBUTES → VNOP_LISTXATTR
vn_removexattr: authorize WRITE_EXTATTRIBUTES → VNOP_REMOVEXATTR
                ENOTSUP 时可 default_removexattr
```

路径仍由 `namei` 从用户地址空间取入（与昨日讨论一致）。

---

## 4. 建议点开

1. `syscalls.master` — 240 / 238  
2. `vfs_syscalls.c` — `listxattr` / `removexattr`  
3. `vfs_xattr.c` — `vn_listxattr` / `vn_removexattr`  

验收：能串起 set/get/list/remove；Demo 能跑。
