# 源码分析：Day 24（sendmsg / recvmsg / getsockopt）

基于 `xnu-12377.121.6`。套接字消息收发与选项读取。

---

## 1. 心智模型

```text
用户 fd
  → struct socket
       → so_snd / so_rcv（发送/接收缓冲，mbuf 链）
            ↔ 协议栈 ↔ 对端 socket

sendmsg / recvmsg：一次 syscall 可带
  - 数据（iovec → uio）
  - 地址（msg_name）
  - 控制消息（msg_control，如传 FD）
```

仍是：**进程侧 FD 找本地对象**；数据进/出该对象的缓冲。

---

## 2. sendmsg 主路径

[`uipc_syscalls.c`](../../xnu/bsd/kern/uipc_syscalls.c)：

```
sendmsg_nocancel
  copyin msghdr、iovec → uio (UIO_WRITE)
  file_socket → so
  sendit
    可选 copyin 目的 sockaddr
    可选 sockargs → control mbuf
    pru_sosend(so, to, uio, control, flags)
```

`pru_sosend` 多数协议接到 `sosend`（`uipc_socket.c`）：锁 socket、进发送缓冲、唤醒协议输出。今天跟到「进入协议发送入口」即可。

---

## 3. recvmsg 主路径

```
recvmsg_nocancel
  copyin msghdr、iovec → uio (UIO_READ)
  recvit
    fp_get_ftype → so
    pru_soreceive(so, &fromsa, uio, &control, &flags)
    copyout 地址 / control / 更新后的 msghdr
```

`pru_soreceive` 常落到 `soreceive`：从 `so_rcv` 取数据填 uio；缓冲空可 sleep。

---

## 4. getsockopt 主路径

```
getsockopt
  file_socket → so
  sockopt { SOPT_GET, level, name, val, valsize }
  sogetoptlock
    非 SOL_SOCKET → pr_ctloutput
    SOL_SOCKET → 通用选项处理（可先 pru_socheckopt）
  copyout 实际 valsize
```

`setsockopt`（#105）对称走 `sosetoptlock`。选项表很大，Day 24 只认分发骨架。

---

## 5. 和 read/write 的关系

| 路径 | 说明 |
|------|------|
| `write(socket_fd)` | 经 `socketops`，最终也常进协议发送 |
| `sendmsg` | 显式消息接口：地址 + control + 多 iov |
| `read` vs `recvmsg` | 同理 |

学消息路径时抓住：`sendit`/`recvit` → `pru_sosend`/`pru_soreceive`。

---

## 6. 建议点开的文件

1. `syscalls.master` — 28 / 27 / 118（及 105）  
2. `uipc_syscalls.c` — `sendmsg_nocancel` / `sendit` / `recvmsg_nocancel` / `recvit` / `getsockopt`  
3. `uipc_socket.c` — `sosend` / `soreceive` / `sogetoptlock` 函数头  

验收：能说 msghdr 三块；能画 fd→so→sosend/soreceive；知道 getsockopt 是选项分发。
