# 源码分析：Day 33（sys_flock）

基于 `xnu-12377.121.6`。文件劝告锁（flock 语义）。

---

## 1. 心智模型

```text
fd → fileproc/fileglob → vnode
         │
         └─ VNOP_ADVLOCK(id=fileglob, op, flock, F_FLOCK [|F_WAIT])
              → 文件系统/内核锁表记录占有与等待
```

整文件：`l_start=0, l_len=0`。

---

## 2. sys_flock 主路径

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c)：

```
fp_getfvp(fd)
LOCK_UN → F_UNLCK
LOCK_EX → F_WRLCK；LOCK_SH → F_RDLCK
VNOP_ADVLOCK(..., F_SETLK, F_FLOCK [| F_WAIT])
成功：FWASLOCKED
```

`LOCK_NB`：不加 `F_WAIT`，冲突立即返回。

---

## 3. 和 open(O_EXLOCK/O_SHLOCK)

`open1` 里也可在打开时直接 `VNOP_ADVLOCK`（同样 `F_FLOCK`）。  
`flock` 是打开后再加/解锁的显式接口。

---

## 4. 建议点开

1. `syscalls.master` — 131  
2. `kern_descrip.c` — `sys_flock`  
3. `vnode_if.h` — `VNOP_ADVLOCK` 注释  

验收：能画 FD→vnode→ADVLOCK；能说劝告与整文件语义。
