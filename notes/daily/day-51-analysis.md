# 源码分析：Day 51（chflags / fchflags）

基于 `xnu-12377.121.6`。BSD 文件标志。

---

## 1. 心智模型

```text
chflags(path, flags) / fchflags(fd, flags):
  得到 vnode → chflags1
    VATTR_SET(va_flags)
    authorize（可 NOIMMUTABLE）
    vnode_setattr
    APPEND → v_ext_flag VE_APPENDONLY
```

---

## 2. 实现

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
chflags0 / chflags1
chflags:  namei FOLLOW
fchflags: file_vnode
```

标志定义见 `sys/stat.h`：`UF_APPEND`、`UF_IMMUTABLE`、`APPEND` 宏等。

---

## 3. 与 truncate 的关系

`ftruncate` 调 `vnode_isappendonly`；`chflags` 设 `APPEND` 时置 `VE_APPENDONLY`。  
这就是 Day 46「拒绝 append-only」的来源之一。

---

## 4. 建议点开

1. `syscalls.master` — 34 / 35  
2. `vfs_syscalls.c` — `chflags` / `fchflags` / `chflags0`  
3. `sys/stat.h` — `UF_*` / `SF_*`  

验收：能说标志 vs mode；Demo 能复现 truncate 失败。
