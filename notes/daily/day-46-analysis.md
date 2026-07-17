# 源码分析：Day 46（truncate / ftruncate）

基于 `xnu-12377.121.6`。文件长度截断/扩展。

---

## 1. 心智模型

```text
truncate(path, len):
  namei → truncate_internal(need_auth=true) → setattr(va_data_size)

ftruncate(fd, len):
  fp → switch dtype:
    PSXSHM → pshm_truncate
    VNODE  → truncate_internal(need_auth=false)
    other  → EINVAL
```

---

## 2. 内部

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
truncate_validate_common: length>=0；RLIMIT_FSIZE
truncate_internal: VATTR_SET(va_data_size)；vnode_setattr
```

`ftruncate` 要求可写；拒绝 symlink、append-only。

---

## 3. 建议点开

1. `syscalls.master` — 200 / 201  
2. `vfs_syscalls.c` — `truncate` / `ftruncate` / `truncate_internal`  
3. 对照 `FILEGLOB_DTYPE` 分支（巩固 fileglob 分流）  

验收：能说 size 也是 vnode_attr；Demo 能跑。
