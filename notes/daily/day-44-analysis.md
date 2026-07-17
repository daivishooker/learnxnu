# 源码分析：Day 44（chmod / chown）

基于 `xnu-12377.121.6`。权限与属主。

---

## 1. 心智模型

```text
chmod(path, mode):
  nameiat → chmod_vnode → vnode_setattr(va_mode)

chown(path, uid, gid):
  nameiat → vn_chown_internal → vnode_setattr(va_uid/va_gid)
```

---

## 2. chmod

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
chmod → fchmodat_internal(AT_FDCWD)
  VATTR_SET(va_mode, mode & ALLPERMS)
  chmodat → nameiat → chmod_vnode
    vnode_chmod_chown_busy
    vnode_authattr / authorize
    vnode_setattr
```

---

## 3. chown

```
chown → fchownat_internal(AT_FDCWD)
  nameiat → vn_chown_internal
    可选 va_uid / va_gid（VNOVAL = 不改）
    authorize → vnode_setattr
```

`EACCES` 在写侧常转成 `EPERM`。

---

## 4. 建议点开

1. `syscalls.master` — 15 / 16  
2. `vfs_syscalls.c` — `chmod` / `chmod_vnode` / `chown` / `vn_chown_internal`  

验收：能说两者都落 setattr；Demo 至少跑通 chmod。
