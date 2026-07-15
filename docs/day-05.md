# 第五天（Day 5）正文

学这三个：**`read` / `write` / `lseek`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 4 得到了 fd；今天用 fd 做数据搬运，并理解**文件偏移**存在哪。

---

## 今天目标

1. 找到编号 **3 / 4 / 199**  
2. 理解 `read`/`write` 如何把用户缓冲区包成 **uio**，再 `fo_read`/`fo_write`  
3. 知道普通读写用的是 `fileglob->fg_offset`；`lseek` 改的就是它  
4. 能区分 `read` 与 `pread`（今天以 `read` 为主，`pread` 只需知道带显式 offset）

笔记：[`notes/daily/day-05.md`](../notes/daily/day-05.md)  
分析：[`notes/daily/day-05-analysis.md`](../notes/daily/day-05-analysis.md)

---

## 总表

| 名字 | # | 原型要点 |
|------|---|----------|
| read | **3** | `(fd, buf, nbyte)` → 字节数 |
| write | **4** | `(fd, buf, nbyte)` → 字节数 |
| lseek | **199** | `(fd, offset, whence)` → 新偏移 |

---

## 1. read（#3）

[`sys_generic.c`](../xnu/bsd/kern/sys_generic.c)：

```c
read(...) {
    __pthread_testcancel(1);
    return read_nocancel(...);
}
read_nocancel(...) {
    return read_internal(p, fd, buf, nbyte, (off_t)-1, 0, retval);
}
```

`read_internal` 关键步骤：

1. 用用户 `buf`/`nbyte` 建一个 **UIO_READ** 的 `uio`  
2. `readv_internal` → `preparefileread`（按 fd 取 `fileproc`，检查 `FREAD`）  
3. `fo_read(fp, uio, …)`（文件类型相关：vnode/socket/pipe…）  
4. `*retval = 已读字节数`（`count - uio_resid`）

最短链：

```
read → read_internal → 构造 uio
     → preparefileread(fd) → fileproc
     → fo_read → *retval = 字节数
```

---

## 2. write（#4）

对称路径：

```
write → write_nocancel → write_internal
      → 构造 UIO_WRITE 的 uio
      → 查 fd / 检查可写
      → fo_write → *retval = 已写字节数
```

和 `read` 一样：用户缓冲区地址在 uio 里描述，由下层决定如何 `copyin`/`copyout`。

---

## 3. lseek（#199）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
lseek(...) {
    fp_getfvp(p, fd, &fp, &vp);   // 非 vnode 类 → 常变 ESPIPE
    // pipe/tty 禁止 seek
    switch (whence) {
      case L_INCR: offset += fp->fp_glob->fg_offset; break; // SEEK_CUR
      case L_XTND: offset += file_size; break;              // SEEK_END
      case L_SET:  break;                                   // SEEK_SET
      ...
    }
    fp->fp_glob->fg_offset = offset;
    *retval = offset;
}
```

要点：

- 偏移存在 **`fileglob.fg_offset`**（多个 fd 若共享同一 `fileglob`，偏移也共享——`dup` 时会碰到）  
- pipe/FIFO/TTY 等不可定位 → `ESPIPE`  
- 成功返回**新的绝对偏移**

---

## 今日对比

| | read/write | lseek |
|--|------------|-------|
| 碰用户缓冲区 | 是（经 uio） | 否 |
| 改 `fg_offset` | 读写推进（由 fo_* 路径维护） | 显式修改 |
| `*retval` | 字节数 | 新偏移 |
| 典型错误 | EBADF / EFAULT | EBADF / ESPIPE / EINVAL |

---

## 做完打勾

- [ ] 找到 3 / 4 / 199  
- [ ] 能说出 uio 在 read/write 里的角色  
- [ ] 知道偏移在 `fg_offset`  
- [ ] 填好 `notes/daily/day-05.md`

下一步：Day 6 → `dup` / `dup2`
