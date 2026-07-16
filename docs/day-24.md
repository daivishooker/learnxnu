# 第二十四天（Day 24）正文

学这三个：**`sendmsg` / `recvmsg` / `getsockopt`**  
源码：`xnu/` = **xnu-12377.121.6**

Day 22–23 把连接建好了；今天看**连上之后怎么传数据**，以及怎么查一点 socket 选项。  
（`setsockopt` 与 `getsockopt` 成对，今天以读选项为主，写选项略提。）

生活类比：

1. `sendmsg`：不只塞一封信，还可附带**收件地址条、附件袋**（控制消息）  
2. `recvmsg`：收信时同时拿回**寄件人地址、附件袋**  
3. `getsockopt`：查这张「听筒」的设置（缓冲区大小、是否 reuse 等）

---

## 今天目标

1. 找到编号 **28 / 27 / 118**（`setsockopt` 为 **105**，对照即可）  
2. 理解 `msghdr`：数据 + 可选地址 + 可选 control  
3. 理解发送/接收最终进 `pru_sosend` / `pru_soreceive`（常落到 `sosend` / `soreceive`）  
4. 理解 `getsockopt`：按 level/name 读选项，别深挖每个 cmd  

笔记：[`notes/daily/day-24.md`](../notes/daily/day-24.md)  
分析：[`notes/daily/day-24-analysis.md`](../notes/daily/day-24-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sendmsg | **28** | 按 `msghdr` 发送（可带地址/控制消息） |
| recvmsg | **27** | 按 `msghdr` 接收 |
| getsockopt | **118** | 读取 socket 选项 |

对照：普通 `write`/`read` 只搬缓冲区；`sendmsg`/`recvmsg` 是**消息接口**。

---

## 1. sendmsg（#28）——带信封的发送

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c)：

```c
sendmsg(s, msg, flags) {
    copyin(msghdr) + copyin(iovec[]) → uio
    file_socket(s) → so
    sendit(so, msg, uio, flags)
      可选 getsockaddr(msg_name)     // 对端地址（UDP 常用）
      可选 sockargs(msg_control)     // 附属数据 → mbuf
      pru_sosend(so, to, uio, control, flags)
}
```

`msghdr` 里常见三块：

| 字段 | 干什么 |
|------|--------|
| `msg_iov` | 要发的数据（可多段） |
| `msg_name` | 目的地址（未 connect 的 UDP 等） |
| `msg_control` | 控制消息（如 `SCM_RIGHTS` 传 FD） |

已 `connect` 的 TCP：通常只填 iov，地址可空。

---

## 2. recvmsg（#27）——带信封的接收

```c
recvmsg(s, msg, flags) {
    copyin(msghdr) + iovec → uio
    recvit(s, msg, uio)
      fp → so
      pru_soreceive(so, &fromsa, uio, &control, &flags)
      可选 copyout 对端地址、control
      copyout 更新后的 msghdr
}
```

和 `sendmsg` 对称：数据进你的 buffer；需要时把**从哪来**、**附属控制消息**一并带出。

和 Day 5 `read`/`write` 对照：

| | read/write | recvmsg/sendmsg |
|--|------------|-----------------|
| 入口 | 文件通用路径 | 套接字消息路径 |
| 地址 | 无 | 可带 |
| control | 无 | 可带 |
| 底层 | 对 socket 最终也常进协议收发 | `pru_soreceive` / `pru_sosend` |

---

## 3. getsockopt（#118）——查选项（略读）

```c
getsockopt(s, level, name, val, valsize) {
    file_socket(s) → so
    填 sockopt { SOPT_GET, level, name, … }
    sogetoptlock(so, &sopt)
      SOL_SOCKET → 通用项（linger、rcvbuf…）
      否则 → pr_ctloutput（协议私有项）
    copyout 实际长度
}
```

今天验收：知道是 **FD → socket → 按 level/name 分发读选项** 即可。  
不必背 `SO_REUSEADDR`、`TCP_NODELAY` 每一个实现。

（写选项：`setsockopt` #105 → `sosetoptlock`，对称。）

---

## 今日串起来

```text
已连接（或 UDP 填地址）：
  sendmsg(fd, msghdr) → 本地 socket 发送队列 → 网络 → 对端 socket
  recvmsg(fd, msghdr) ← 本地接收队列 ← …

查设置：
  getsockopt(fd, level, name, …)
```

| 调用 | 内核关键动作 |
|------|----------------|
| sendmsg | `sendit` → `pru_sosend`（常 `sosend`） |
| recvmsg | `recvit` → `pru_soreceive`（常 `soreceive`） |
| getsockopt | `sogetoptlock` |

心智模型：还是 **进程用 FD 找本地 socket**；数据在两边 socket 的收发缓冲之间走。

---

## 用户层 Demo

`sendmsg`/`recvmsg` 走 `msghdr`+`iovec`；`getsockopt` 读回 `SO_TYPE`。

```c
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int sv[2];
    socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
    char data[] = "msg";
    struct iovec iov = { .iov_base = data, .iov_len = 3 };
    struct msghdr mh = {0};
    mh.msg_iov = &iov; mh.msg_iovlen = 1;
    sendmsg(sv[0], &mh, 0);

    char buf[8] = {0};
    struct iovec riov = { .iov_base = buf, .iov_len = sizeof(buf) - 1 };
    struct msghdr rmh = {0};
    rmh.msg_iov = &riov; rmh.msg_iovlen = 1;
    recvmsg(sv[1], &rmh, 0);
    int type = 0; socklen_t len = sizeof(type);
    getsockopt(sv[0], SOL_SOCKET, SO_TYPE, &type, &len);
    printf("recv=%s type=%d\n", buf, type);
    close(sv[0]); close(sv[1]);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 28 / 27 / 118  
- [ ] 能说 msghdr = 数据 + 可选地址 + 可选 control  
- [ ] 能说收发进 pru_sosend / pru_soreceive  
- [ ] 能说 getsockopt 按 level/name 读，不深挖每个选项  
- [ ] 填好 `notes/daily/day-24.md`

下一步：Day 25 → [`shutdown` / `close`](day-25.md)
