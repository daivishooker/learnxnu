# 源码分析：Day 45（utimes / futimes）

基于 `xnu-12377.121.6`。访问/修改时间。

---

## 1. 心智模型

```text
utimes(path, tptr):
  namei → getutimes → setutimes → vnode_setattr(atime/mtime)

futimes(fd, tptr):
  file_vnode(fd) → 同一 getutimes / setutimes
```

---

## 2. 时间从哪来

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
getutimes:
  tptr == NULL → microtime，两戳相同
  否则 copyin timeval[2] → timespec[2]

setutimes:
  va_access_time / va_modify_time
  nullflag → VA_UTIMES_NULL
  authorize → vnode_setattr
```

---

## 3. 与 fileglob 分流

`futimes` 调 `file_vnode`：FD 必须是 vnode 类型。  
socket 等非 vnode FD 不会走进 `setutimes`。

---

## 4. 建议点开

1. `syscalls.master` — 138 / 139  
2. `vfs_syscalls.c` — `utimes` / `futimes` / `getutimes` / `setutimes`  

验收：能说与 chmod/chown 同属 setattr 族；Demo 能跑。
