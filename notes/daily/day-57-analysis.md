# 源码分析：Day 57（*at 家族扫尾）

基于 `xnu-12377.121.6`。六个调用收官常用 `*at`。

---

## 1. 心智模型

```text
*at 共性：nameiat(..., dirfd) 钉起点
  linkat          → 双查找 + LINK
  getattrlistat   → LOOKUP + getattrlist_internal
  setattrlistat   → LOOKUP + setattrlist_internal
  renameatx_np    → renameat_internal + flags
  mkfifoat/mknodat → CREATE + vn_create（类型不同）
```

---

## 2. 汇合关系

```
link          → linkat_internal(AT_FDCWD×2, AT_SYMLINK_FOLLOW)
getattrlist   → getattrlistat_internal(AT_FDCWD)
renameat      → renameat_internal(flags=0)
renameatx_np  → renameat_internal(flags)
mkfifo/mknod  → mkfifo1 / mknodat_internal(AT_FDCWD)
```

---

## 3. 建议点开

1. `syscalls.master` — 471 / 476 / 524 / 488 / 553 / 554  
2. `vfs_syscalls.c` — `linkat_internal` / `renameatx_np` / `mkfifo1` / `mknodat_internal`  
3. `vfs_attrlist.c` — `getattrlistat_internal` / `setattrlistat`  
4. 对照 Day 37–38、50、54

验收：能画 `*at` 简表；Demo（linkat + mkfifoat）能跑。
