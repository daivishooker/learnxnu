# 源码分析：Day 23（accept / connect / socketpair）

基于 `xnu-12377.121.6`。连接建立与本地双端。

---

## 1. 心智模型

```text
监听 socket（head，SO_ACCEPTCONN）
  so_comp 队列：已完成握手、等待 accept 的 socket

accept：
  head(fd_listen) ──摘──→ so_connected
                           ↓ falloc
                         new_fd → so_connected

connect：
  client_fd → so ──pru_connect──→ 对端地址写入 PCB，状态→已连接

socketpair：
  so1 ←──soconnect2──→ so2
   ↑                    ↑
  fd0                  fd1
```

进程侧永远 **FD → 对象**；网络侧 **地址 → PCB → socket**。  
`accept` 不是「地址转成 FD」，而是协议栈已造好连接对象，再给进程挂一个新 FD。

---

## 2. accept 主路径

[`uipc_syscalls.c`](../../xnu/bsd/kern/uipc_syscalls.c) `accept_nocancel`：

```
fp_get_ftype(fd, DTYPE_SOCKET) → head
检查 SO_ACCEPTCONN（未 listen → EINVAL / EOPNOTSUPP）
while so_comp 空：msleep(&head->so_timeo, …)
从 head->so_comp 摘 so
falloc → newfd；socketops；fp_set_data(so)
soacceptlock → pru_accept（取对端 sockaddr）
可选 copyout 对端地址
返回 newfd
```

注意：先出队再 `falloc`，避免 `falloc` 阻塞时别人抢走同一连接。

---

## 3. connect 主路径

```
file_socket(fd) → so
getsockaddr / getsockaddr_s → 对端 sa
connectit(so, sa)
  soconnectlock → pru_connect
  阻塞：while SS_ISCONNECTING → msleep
```

`soconnectlock`（`uipc_socket.c`）：监听 socket / defunct 拒绝；面向连接且已连则 `EISCONN`。

---

## 4. socketpair 主路径

```
socreate → so1
socreate → so2
falloc → sv[0] / so1
falloc → sv[1] / so2
soconnect2(so1, so2)          // pru_connect2
SOCK_DGRAM 再 soconnect2(so2, so1)
copyout(sv[2])
```

内核内互连，不经网卡。和 `pipe` 比：两端都是 socket（`socketops`）。

---

## 5. 和 Day 22 对照

| 阶段 | 调用 | 对象变化 |
|------|------|----------|
| 造端点 | socket | 1 个 so + 1 个 fd |
| 本端号 | bind | PCB 本地地址 |
| 开始听 | listen | `SO_ACCEPTCONN`，队列就绪 |
| 接听 | accept | **再** 1 个 so（已在队列）+ **新** fd |
| 拨号 | connect | 同一 so 填对端并建连 |
| 本地对 | socketpair | 2 个 so + 2 个 fd，已互连 |

---

## 6. 建议点开的文件

1. `syscalls.master` — 30 / 98 / 135  
2. `uipc_syscalls.c` — `accept_nocancel` / `connect_nocancel` / `socketpair`  
3. `uipc_socket.c` — `soacceptlock` / `soconnectlock` / `soconnect2`  

验收：能画服务端 `listen→accept` 与客户端 `connect`；能说 accept 出来的是新 FD/新 socket。
