# 源码分析：Day 36（getfsstat64）

基于 `xnu-12377.121.6`。列举各挂载点统计。

---

## 1. 心智模型

```text
getfsstat64(buf[], bufsize, flags)
  → vfs_iterate 每个 mount
       →（可选）vfs_update_vfsstat
       → vfs_get_statfs64 → copyout 下一槽
  → 返回个数
```

---

## 2. 主路径

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c) `getfsstat64` / `getfsstat64_callback`。

`bufsize / sizeof(statfs64)` = 最多能装几个；返回值是实际枚举到的个数（可被 buffer 截断）。

---

## 3. 建议点开

1. `syscalls.master` — 347  
2. `vfs_syscalls.c` — `getfsstat64`  

验收：能说「扫 mount 列表填数组」；能跑通 Demo。
