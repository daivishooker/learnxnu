# 第二十八天（Day 28）正文

**查漏补缺日**：不新开一批 syscall，重读本周（第 4 周）最容易混的三块。  
源码：`xnu/` = **xnu-12377.121.6**

今天自选重读：

1. **套接字两套索引 + accept**（Day 22–23）  
2. **消息收发 + 接收队列**（Day 24）  
3. **shutdown vs close**（Day 25）  

（shm / ptrace / sysctl 若仍糊，文末给回顾入口。）

笔记：[`notes/daily/day-28.md`](../notes/daily/day-28.md)  
分析：[`notes/daily/day-28-analysis.md`](../notes/daily/day-28-analysis.md)

---

## 重读 A：FD 找对象 vs 地址找对象

```text
进程侧：  fd  ──文件表──→  socket
网络侧：  地址 ──PCB 表──→  socket
```

| 说法 | 对不对 |
|------|--------|
| bind 后地址绑在 socket（经 PCB）上 | ✅ |
| 地址先变成 fd，再用 fd 找对象 | ❌ |
| accept 把监听 fd「变成」已连接 | ❌（新 so + 新 fd） |
| 没 listen 就不会往你的 so_comp 挂待接连接 | ✅ |

服务端：

```text
socket → bind → listen（SO_ACCEPTCONN，开排队）
       → 对端 connect → 内核造已连接 so → 挂 so_comp
       → accept → 摘 so + falloc 新 fd
监听 fd 继续听；业务用新 fd。
```

客户端：`socket` 已有 fd → `connect` 给**同一个** so 建连（不经 so_comp）。

---

## 重读 B：sendmsg / recvmsg 数据怎么走

```text
本地 socket.so_snd  → 协议栈/网络 → 对端 socket.so_rcv
进程 recvmsg(fd) ← 从本地 so_rcv 取 → copyout 进 iovec
```

| 点 | 记住 |
|----|------|
| `copyin(msghdr)` | 只拷说明书（指针+长度），不拷全部正文 |
| `iovec` | 正文缓冲区列表；收 = copyout 进去 |
| 没人 recv | 数据堆在 `so_rcv`，有上限；TCP 流控，UDP 满了可丢 |
| UDP 可不 connect | 每次 `msg_name` 带目的地址即可 |
| `getsockopt` | 只读选项；改用 `setsockopt` |

---

## 重读 C：shutdown vs close

| | shutdown | close |
|--|----------|-------|
| FD | 还在 | 去掉 |
| 含义 | 关读/写方向（半关闭） | 放下把手 |
| 典型 | `SHUT_WR` = 告诉对方「我发完了」 | 用完收工 |
| 内核 | 改 socket 状态 + `pru_shutdown` | `soo_close` → `soclose` |

```text
可选：shutdown(SHUT_WR) → 继续读到 EOF → close(fd)
```

---

## 今日验收（能口头答出即可）

1. 网络收包为什么不查 FD？  
2. accept 为什么返回新 FD？  
3. recvmsg 的数据原先躺在哪？怎么进你的 buffer？  
4. shutdown 解决什么同步/收尾问题？  

对照原文：

- [Day 22](day-22.md) · [Day 23](day-23.md) · [Day 24](day-24.md) · [Day 25](day-25.md)

可选加练：[Day 26 shm](day-26.md)（只 mmap，无 read/write）· [Day 27 ptrace/sysctl](day-27.md)（门禁）

---

## 做完打勾

- [ ] 能画 FD / 地址两条索引  
- [ ] 能讲 listen → so_comp → accept  
- [ ] 能讲 so_rcv → recvmsg → iovec  
- [ ] 能对比 shutdown / close  
- [ ] 填好 `notes/daily/day-28.md`

第 4 周到此收束。下一步：Day 29 → [`getsockname` / `getpeername` / `setsockopt`](day-29.md)  
完整日程见 [DAILY_SYSCALL_PLAN.md](DAILY_SYSCALL_PLAN.md)。
