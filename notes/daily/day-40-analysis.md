# 源码分析：Day 40（clonefileat / fclonefileat）

基于 `xnu-12377.121.6`。整文件/目录克隆（常为写时复制）。

---

## 1. 心智模型

```text
clonefileat(src_dirfd, src, dst_dirfd, dst):
  nameiat 源 → fvp → clonefile_internal → VNOP_CLONEFILE

fclonefileat(src_fd, dst_dirfd, dst):
  fd → fvp（需 FREAD）→ 同一 clonefile_internal
```

---

## 2. clonefile_internal

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
源类型：VREG / VLNK / VDIR（非 mount 根等）
目标 CREATE nameiat；已存在 → EEXIST
不同 mount → EXDEV
authorize 父目录 ADD + 源读
填 vnode_attr；VNOP_CLONEFILE
缺省属性可用 setattr_fallback 补
```

标志见 `sys/clonefile.h`：`CLONE_NOFOLLOW`、`CLONE_NOOWNERCOPY`、`CLONE_ACL` 等。

---

## 3. 两入口差异

| | 定位源 | `data_read_authorised` |
|--|--------|------------------------|
| clonefileat | `nameiat(src_dirfd, src)` | FALSE |
| fclonefileat | `fp_getfvp` + FREAD | TRUE |

---

## 4. 建议点开

1. `syscalls.master` — 462 / 517  
2. `vfs_syscalls.c` — `clonefileat` / `fclonefileat` / `clonefile_internal`  
3. `sys/clonefile.h` — flags  
4. `kpi_vfs.c` / `vnode_if.h` — `VNOP_CLONEFILE`  

验收：能说与 copyfile 的差别；Demo 在 APFS 上能跑。
