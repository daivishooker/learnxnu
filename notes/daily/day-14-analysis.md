# 源码分析：Day 14（pipe / fcntl / fsync）

基于 `xnu-12377.121.6`。管道、FD 控制、刷盘。

---

## 1. 心智模型

```text
pipe：
  [读端 FD] ←── buffer ──→ [写端 FD]
       │                      │
    fileproc + pipeops     fileproc + pipeops

fcntl(fd, cmd, arg)：
  查 fileproc → 按 cmd 改标志 / 复制槽 / 锁 vnode …

fsync(fd)：
  FD → vnode → VNOP_FSYNC（文件系统真正刷）
```

---

## 2. pipe 主路径

[`sys_pipe.c`](../../xnu/bsd/kern/sys_pipe.c)：

```
pipe
  pipepair_alloc → rpipe / wpipe，互为 pipe_peer
  falloc 读端：f_flag=FREAD，f_ops=pipeops，data=rpipe
  falloc 写端：f_flag=FWRITE，f_ops=pipeops，data=wpipe
  释放进 FD 表；retval[0]/[1] = 两个编号
```

之后父子进程若都继承这一对 FD，关掉不用的一端，就能单向通信。  
`posix_spawn` 的 `file_actions` 也可以在子进程启动前摆好管道两端。

和 Day 5：`read`/`write` 对管道 FD 最终进 `pipeops` 的读写实现，而不是 `VNOP_READ`。

---

## 3. fcntl 主路径

[`kern_descrip.c`](../../xnu/bsd/kern/kern_descrip.c)：

```
sys_fcntl（可取消）
  → sys_fcntl_nocancel
       fp_lookup(fd)
       switch (cmd):
         F_DUPFD / F_DUPFD_CLOEXEC → fdalloc + finishdup
         F_GETFD / F_SETFD         → FP_CLOEXEC
         F_GETFL / F_SETFL         → f_flag ↔ O_* 标志
         F_SETLK / F_GETLK / …     → 文件锁（碰 vnode）
         …
```

教学上先抓住三类：

1. **复制 FD**（对照 Day 6 `dup`）  
2. **每描述符标志**（`CLOEXEC`）  
3. **打开标志**（`O_NONBLOCK` 等）

其余命令知道「都在这个大 switch 里」即可，不必一天啃完。

---

## 4. fsync 主路径

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
fsync
  → fsync_common(p, uap, MNT_WAIT)
       fp_getfvp → vnode（非 vnode → 最终常变 EINVAL）
       VNOP_FSYNC(vp, flags, ctx)
```

| 调用 | flags 含义（本树注释） |
|------|------------------------|
| `fsync` | `MNT_WAIT`：文件完整性（数据 + atime/mtime 等元数据） |
| `fdatasync` | `MNT_DWAIT`：数据完整性（能读回内容即可） |

真正刷盘细节在各文件系统的 `VNOP_FSYNC`。

---

## 5. 和第 2 周的关系

- 进程：`fork` / `spawn` / `exec` / `wait` / `kill`  
- 文件：`open`…`close`，今天补上 **管道通信**、**FD 微调**、**落盘保证**

第 2 周验收可回顾：能画 `fork→execve→wait4` vs `posix_spawn`；并能说 pipe 两端如何配合 spawn 的 file_actions。

---

## 6. 建议点开的文件

1. `syscalls.master` — 42 / 92 / 95  
2. `sys_pipe.c` — `pipe`、`pipeops`  
3. `kern_descrip.c` — `sys_fcntl_nocancel` 里 `F_DUPFD` / `F_GETFL` / `F_SETFD`  
4. `vfs_syscalls.c` — `fsync` / `fsync_common`  

验收：能口述「pipe 两 FD；fcntl 按 cmd；fsync 到 VNOP」。
