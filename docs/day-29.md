# 第二十九天（Day 29）正文

学这三个：**`getsockname` / `getpeername` / `setsockopt`**  
源码：`xnu/` = **xnu-12377.121.6**

第 4 周日程已走完。进入**第 5 周**：补全套接字「查地址 / 改选项」，和你刚问过的 `getsockopt` 成对。

生活类比：

1. `getsockname`：查**自己这张证上的本端号码**  
2. `getpeername`：查**对面那张证的号码**（得先连上）  
3. `setsockopt`：**改**听筒设置（缓冲、reuse、linger…）；`getsockopt` 是查

---

## 今天目标

1. 找到编号 **32 / 31 / 105**  
2. 理解本端 / 对端地址从 PCB 经 `pru_sockaddr` / `pru_peeraddr` 取出  
3. 理解 `setsockopt`：`SOPT_SET` → `sosetoptlock`（与 get 对称）  
4. 能说：查地址 ≠ 改选项；get/set sockopt 成对  

笔记：[`notes/daily/day-29.md`](../notes/daily/day-29.md)  
分析：[`notes/daily/day-29-analysis.md`](../notes/daily/day-29-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getsockname | **32** | 取本端 sockaddr |
| getpeername | **31** | 取对端 sockaddr（需已连接） |
| setsockopt | **105** | 设置 socket 选项 |

---

## 1. getsockname（#32）——我的本端地址

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c)：

```c
getsockname(fd, asa, alen) {
    file_socket → so
    copyin(*alen)
    pru_sockaddr(so, &sa)     // 协议从 PCB 取出本地地址
    copyout(sa) + 回写实际长度
}
```

`bind` 之后（或内核自动选端口后）就能查到「本端 IP:端口」。  
接昨天模型：**地址在 socket/PCB 上；FD 只是把手。**

---

## 2. getpeername（#31）——对面的地址

```c
getpeername(fd, asa, alen) {
    file_socket → so
    未连接 → ENOTCONN
    已双向 shutdown 一类 → 可能 EINVAL
    pru_peeraddr(so, &sa)     // 对端地址
    copyout
}
```

典型：`accept` / `connect` 成功后查「对面是谁」。  
UDP 未 connect 时常没有稳定对端 → 会失败。

---

## 3. setsockopt（#105）——改选项（略读分发）

```c
setsockopt(s, level, name, val, valsize) {
    file_socket → so
    sockopt { SOPT_SET, level, name, … }
    sosetoptlock(so, &sopt)
      SOL_SOCKET → 通用项（如 SO_REUSEADDR、SO_RCVBUF…）
      否则 → pr_ctloutput（如 IPPROTO_TCP）
}
```

和 Day 24 `getsockopt`（#118）对称：一个 `SOPT_GET`，一个 `SOPT_SET`。  
今天验收：到分发点即可，不背每个选项。

常见例子（用户层）：`SO_REUSEADDR`、`SO_RCVBUF`、`TCP_NODELAY`。

---

## 今日串起来

```text
bind / connect / accept 之后：
  getsockname(fd) → 本端
  getpeername(fd) → 对端（已连接）

调优：
  setsockopt(fd, level, name, …)
  getsockopt(fd, level, name, …)   // Day 24
```

| 调用 | 内核关键动作 |
|------|----------------|
| getsockname | `pru_sockaddr` + copyout |
| getpeername | `pru_peeraddr` + copyout |
| setsockopt | `sosetoptlock` / `pr_ctloutput` |

---

## 做完打勾

- [ ] 找到 32 / 31 / 105  
- [ ] 能说 getsockname = 本端，getpeername = 对端  
- [ ] 能说 getpeername 要已连接  
- [ ] 能说 setsockopt 与 getsockopt 成对  
- [ ] 填好 `notes/daily/day-29.md`

下一步：Day 30 → `getrusage` / `gettimeofday`（资源统计与时间）
