# 第十四天（Day 14）正文

学这三个：**`pipe` / `fcntl` / `fsync`**  
源码：`xnu/` = **xnu-12377.121.6**

第 2 周收尾：进程生命周期告一段落，回到 **FD / 文件** 侧——管道两端、`fcntl` 控制、刷盘。

---

## 今天目标

1. 找到编号 **42 / 92 / 95**  
2. 理解 `pipe`：一次造出读端 + 写端两个 FD  
3. 理解 `fcntl`：对已有 FD 做控制（dup、CLOEXEC、状态、锁…）  
4. 理解 `fsync`：把打开文件的脏数据刷到稳定存储

笔记：[`notes/daily/day-14.md`](../notes/daily/day-14.md)  
分析：[`notes/daily/day-14-analysis.md`](../notes/daily/day-14-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| pipe | **42** | 创建匿名管道，返回一对 FD |
| fcntl（`sys_fcntl`） | **92** | 对 FD 发控制命令 |
| fsync | **95** | 同步文件内容（及元数据）到盘 |

---

## 1. pipe（#42）

[`sys_pipe.c`](../xnu/bsd/kern/sys_pipe.c)：

```c
pipe(...) {
    pipepair_alloc(&rpipe, &wpipe)   // 一对 pipe 端点，互为 peer
    falloc → 读端 FD：FREAD  + pipeops
    falloc → 写端 FD：FWRITE + pipeops
    retval[0] = 读 FD
    retval[1] = 写 FD
}
```

要点：

- **半双工**：一端读、一端写（经典 Unix 管道）  
- 两个 FD 都挂 `pipeops`，后面 `read`/`write`（Day 5）走同一套 `fileops`  
- 常和 `fork`/`posix_spawn` + `file_actions` 一起用：父写子读，或反过来  

---

## 2. fcntl（#92）

master 里名字是 **`sys_fcntl`**（避免和用户态/宏冲突）。

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c)：

```c
sys_fcntl → sys_fcntl_nocancel
  fp_lookup(fd)
  switch (cmd) {
    F_DUPFD / F_DUPFD_CLOEXEC  // 类似 dup，可指定最小 FD
    F_GETFD / F_SETFD          // 每 FD 标志，常见 CLOEXEC
    F_GETFL / F_SETFL          // 打开标志：O_NONBLOCK、O_APPEND…
    F_SETLK / F_GETLK / …      // 文件锁
    … 还有很多 Darwin 扩展
  }
```

要点：

- **一个 syscall，很多命令**：今天只记几类常用的即可  
- 和 Day 6 的 `dup`/`dup2` 对照：`F_DUPFD` 也是复制 `fileproc` 槽  
- `CLOEXEC`：exec 时自动关 FD（spawn 的 `file_actions` / `CLOEXEC_DEFAULT` 也相关）

别深挖每个 `F_*`；验收能说出「按 cmd 分发到 FD 操作」。

---

## 3. fsync（#95）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
fsync → fsync_common(..., MNT_WAIT)
  fp_getfvp(fd) → vnode
  VNOP_FSYNC(vp, flags, ctx)   // 落到具体文件系统
```

要点：

- 只对 **vnode 类 FD**（普通文件等）有意义；管道等会失败  
- `MNT_WAIT`：文件完整性（数据 + 相关元数据）  
- 旁路：`fdatasync` 用 `MNT_DWAIT`，偏数据完整性（今天知道有区别即可）

---

## 今日对比

| | pipe | fcntl | fsync |
|--|------|-------|-------|
| 造新 FD？ | 是（一对） | 有时（如 DUPFD） | 否 |
| 主对象 | `struct pipe` + 两端 `fileproc` | 已有 `fileproc` | vnode |
| 和 VFS | 通常不经路径 namei | 部分 cmd 碰 vnode | `VNOP_FSYNC` |

---

## 做完打勾

- [ ] 找到 42 / 92 / 95  
- [ ] 能说 pipe 返回读/写两个 FD  
- [ ] 能说 fcntl 按 cmd 分发（至少 DUPFD / GETFL / SETFD）  
- [ ] 能说 fsync → VNOP_FSYNC  
- [ ] 填好 `notes/daily/day-14.md`

下一步：Day 15 → `mmap` / `munmap` / `mprotect`（第 3 周：内存）
