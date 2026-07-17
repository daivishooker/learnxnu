# 源码分析：Day 55（mkdirat / faccessat）

基于 `xnu-12377.121.6`。`*at` 建目录与权限探测。

---

## 1. 心智模型

```text
mkdirat(dirfd, path, mode):
  mode &= ACCESSPERMS; mode &= ~umask
  mkdir1at → nameiat(CREATE, dirfd) → vn_create(VDIR)

faccessat(dirfd, path, amode, flag):
  默认 kauth_cred_copy_real（除非 AT_EACCESS）
  nameiat(LOOKUP, dirfd) → access1 → vnode_authorize
```

---

## 2. 汇合关系

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
mkdir    → mkdir1at(AT_FDCWD)
mkdirat  → mkdir1at(fd)
access   → faccessat_internal(AT_FDCWD, flag=0)
faccessat → faccessat_internal(fd, flag)
```

---

## 3. faccessat 标志（本树）

合法组合（非法 → `EINVAL`）：

| flag | 作用 |
|------|------|
| `AT_EACCESS` | 用 effective 凭证，而非 real |
| `AT_SYMLINK_NOFOLLOW` | 最后一截不跟随 symlink |
| `AT_SYMLINK_NOFOLLOW_ANY` | 全程不跟随（`NAMEI_NOFOLLOW_ANY`） |
| `AT_RESOLVE_BENEATH` | 解析不得逃出 dirfd 树 |
| `AT_UNIQUE` | 唯一性约束（见测试 `unique.c`） |

---

## 4. 建议点开

1. `syscalls.master` — 475 / 466  
2. `vfs_syscalls.c` — `mkdir1at` / `faccessat_internal` / `access1`  
3. 对照 Day 4 `access`、Day 9 `mkdir`、Day 53 `openat`

验收：能说清 mkdirat 与 faccessat 各自汇入哪条 internal；Demo 能跑。
