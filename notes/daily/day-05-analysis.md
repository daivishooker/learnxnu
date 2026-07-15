# 源码分析：Day 5（read / write / lseek）

基于 `xnu-12377.121.6`。承接 Day 4 的 `fileproc`/fd。

---

## 1. 今天的核心对象

```
fd ──► fileproc ──► fileglob
                      ├─ fg_ops / fo_read, fo_write
                      ├─ fg_offset     ← 当前文件偏移
                      ├─ fg_cred
                      └─ 数据指针（常为 vnode*）
```

`read`/`write` 不解析路径；只认 fd。数据通过 **uio** 描述「从哪读/写到用户哪段内存」。

---

## 2. read 主路径

[`sys_generic.c`](../../xnu/bsd/kern/sys_generic.c)：

```
read
  → read_nocancel
  → read_internal(fd, buf, nbyte, offset=-1, flags=0)
       建 uio：UIO_READ，一个 iov = (buf, nbyte)
  → readv_internal
       preparefileread：fp_lookup + 检查 FREAD
       context.vc_ucred = fp->fp_glob->fg_cred   // 用打开时的凭证
       fp_readv → fo_read(fp, uio, ...)
       *retval = 请求长度 - 剩余 resid
```

要点：

1. **`retval` 类型是字节数**（`user_ssize_t`），不是「成功才塞 pid」那种小整数身份调用。  
2. 普通 `read` 传 `offset = (off_t)-1` 且无 `FOF_OFFSET` → 使用/更新文件当前偏移。  
3. `pread` 则带显式 offset + `FOF_OFFSET`，不改（或不按同一规则改）当前偏移——今天扫一眼即可。  
4. `fo_read` 是多态入口：vnode 文件走 VFS/`VNOP_READ`，socket/pipe 走各自实现。

部分读：若已读一些后遇到 `EINTR`/`EWOULDBLOCK`，可能把 error 清 0，仍返回已读字节（`fp_readv` 里那段 switch）。

---

## 3. write 主路径（对称）

```
write → write_internal → 建 UIO_WRITE 的 uio → fo_write → *retval = 字节数
```

同样经 fd → `fileproc`；检查可写标志。用户缓冲区在写路径上是 **copyin** 方向。

---

## 4. lseek：只动偏移，不动数据

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c) 的 `lseek`：

1. `fp_getfvp`：fd 必须对应 vnode；否则常 `ESPIPE`/`ENOTSUP` 映射  
2. FIFO、TTY 明确禁止 seek → `ESPIPE`  
3. 按 `whence` 算新 offset，写入 **`fp->fp_glob->fg_offset`**  
4. `*retval = 新偏移`

| whence（源码名） | 含义 |
|------------------|------|
| `L_SET` | SEEK_SET：绝对 |
| `L_INCR` | SEEK_CUR：相对当前 `fg_offset` |
| `L_XTND` | SEEK_END：相对文件大小 |

**和 read/write 的关系：** 普通顺序读写依赖同一个 `fg_offset`。`dup` 共享 `fileglob` 时，一个 fd 上 `lseek` 会影响另一个（Day 6 会强调）。

---

## 5. uio 是什么（够用版）

`uio` = 一次 I/O 的描述符：

- 方向：`UIO_READ` / `UIO_WRITE`  
- 地址空间：用户 32/64  
- iovec 列表：每段用户地址 + 长度  
- `resid`：还剩多少没完成  

`read_internal` 用栈上 buffer 快速建「单段」uio，避免为简单 read 额外分配。

---

## 6. 和前几天串起来

| 天 | 对象 |
|----|------|
| Day 3 | nofile 限制 FD 数量 |
| Day 4 | open 创建 fileproc；close 拆掉 |
| Day 5 | 用 fileproc 做 uio I/O；lseek 改 fg_offset |

```
open → fd
        │
        ├─ read/write ──uio──► fo_read/fo_write ──► vnode/socket/...
        │
        └─ lseek ──► fg_offset
```

---

## 7. 建议点开的文件

1. `syscalls.master` — 3 / 4 / 199  
2. `sys_generic.c` — `read` / `read_internal` / `preparefileread` / `fp_readv`  
3. `sys_generic.c` — `write` / `write_nocancel`  
4. `vfs_syscalls.c` — `lseek` 的 switch(whence)  

不必今天钻进具体文件系统的 `VNOP_READ`。
