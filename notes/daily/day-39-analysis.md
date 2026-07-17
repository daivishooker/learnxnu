# 源码分析：Day 39（exchangedata / copyfile）

基于 `xnu-12377.121.6`。整文件交换与内核拷贝。

---

## 1. 心智模型

```text
exchangedata(path1, path2):
  两 vnode（同卷、普通文件）→ VNOP_EXCHANGE → 内容对调

copyfile(from, to):
  源 vnode + 目标父目录/名 → VNOP_COPYFILE → 新文件（或覆盖）
```

---

## 2. exchangedata

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
namei path1 / path2
svp == fvp → EINVAL
不同 v_mount → EXDEV
非 vnode_isreg → EINVAL
authorize 读写
VNOP_EXCHANGE(fvp, svp, ...)
（可选 FSE / kauth 通知）
```

---

## 3. copyfile

同文件：

```
flags & ~CPF_MASK → EINVAL
namei(from)；namei(CREATE, to)
已存在且无 CPF_OVERWRITE → EEXIST
目录 → EISDIR
authorize 读源 / 删旧 / ADD_FILE
VNOP_COPYFILE(...)
```

`NO_SYSCALL_STUB`：用户态常用 `copyfile(3)`，勿与本 syscall 混为一谈。

---

## 4. 建议点开

1. `syscalls.master` — 223 / 227  
2. `vfs_syscalls.c` — `exchangedata` / `copyfile`  
3. `kpi_vfs.c` — `VNOP_EXCHANGE`  
4. `sys/fcntl.h` — `CPF_OVERWRITE`  

验收：能说交换 vs 拷贝两条链；Demo 能跑。
