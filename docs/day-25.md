# 第二十五天（Day 25）正文

学这两个：**`shutdown` / `close`**（套接字场景回顾）  
源码：`xnu/` = **xnu-12377.121.6**

Day 22–24 把套接字从创建、建连到收发走通了；今天看**怎么收尾**——半关闭 vs 真正拆掉 FD/对象。

生活类比：

1. `shutdown`：电话还握在手里，但宣布「我这边不说了 / 不听了 / 两边都不了」（线路语义）  
2. `close`：挂断并**放下听筒**（进程侧把手没了；引用没了才销毁对象）

---

## 今天目标

1. 找到编号 **134**（`shutdown`）与 **6**（`close`，Day 4 已见）  
2. 理解 `shutdown`：不释放 FD，只关掉读/写/双向方向  
3. 理解 `close`：释放 FD；经 `socketops.fo_close` → `soclose`  
4. 能对比：半关闭 vs 释放把手  

笔记：[`notes/daily/day-25.md`](../notes/daily/day-25.md)  
分析：[`notes/daily/day-25-analysis.md`](../notes/daily/day-25-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| shutdown | **134** | 关闭套接字某一方向的通信 |
| close | **6** | 关闭 FD；最后引用时关掉底层 socket |

`how`（shutdown）：

| 值 | 含义 |
|----|------|
| `SHUT_RD` (0) | 不再收 |
| `SHUT_WR` (1) | 不再发（TCP 常发 FIN） |
| `SHUT_RDWR` (2) | 收发都关 |

---

## 1. shutdown（#134）——半关闭，FD 还在

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c)：

```c
shutdown(s, how) {
    file_socket(s) → so
    soshutdown(so, how)
      需已连接（否则 ENOTCONN）
      SHUT_RD  → sorflush，标记不能再收
      SHUT_WR  → pru_shutdown（协议收尾，如 TCP FIN）
}
```

要点：

- **FD 仍然有效**，`close` 之前还能拿着这个号（视 how：可能还能读或写另一侧）  
- 典型用法：`SHUT_WR` 表示「我发完了」，对端 `read` 会读到 EOF，但你还能继续收对端数据  
- 和「拆掉对象」不是一回事  

---

## 2. close（#6）——放下 FD（套接字回顾）

通用路径（Day 4）：进程文件表去掉这个 FD；`fileglob` 引用减到 0 时调 `fo_close`。

套接字特有：[`sys_socket.c`](../xnu/bsd/kern/sys_socket.c) `socketops`：

```c
soo_close(fg) {
    sp = fg 上的 socket
    fg_set_data(fg, NULL)
    soclose(sp)          // uipc_socket.c
}
```

`soclose` 会协议断开、清队列、最后 `sofree`（引用归零时）。  
若同一 socket 被 `dup` 成多个 FD：每个 `close` 只减引用；**最后一个**才真正拆掉对象。

---

## 3. 对比（今天核心）

| | shutdown | close |
|--|----------|-------|
| FD 表项 | **还在** | **去掉** |
| 还能用这个 fd 号吗 | 可以（方向受限） | 不可以（EBADF） |
| 主要干什么 | 关读/写方向、通知协议 | 释放把手；必要时销毁 socket |
| 典型场景 | 半关闭、优雅发完 | 用完收工 |

```text
常见收尾：
  shutdown(fd, SHUT_WR);   // 可选：告诉对方「我发完了」
  … 继续读直到 EOF …
  close(fd);               // 放下听筒
```

只 `close` 也可以：通常也会驱动协议断开，但**没有**「只关写、继续读」这种细粒度。

---

## 今日串起来（第 4 周网络收尾感）

```text
socket → bind → listen → accept/connect
  → sendmsg/recvmsg
  → [shutdown] → close
```

| 调用 | 内核关键动作 |
|------|----------------|
| shutdown | `soshutdown` → `pru_shutdown` / `sorflush` |
| close（socket） | `soo_close` → `soclose` |

心智模型：  
- **shutdown** = 改 socket 上的通信能力  
- **close** = 进程侧丢掉 FD；对象随引用释放  

---

## 用户层 Demo

`shutdown(SHUT_WR)` 半关闭写端，对端读到 EOF；最后再 `close` 释放 FD。

```c
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int sv[2];
    socketpair(AF_UNIX, SOCK_STREAM, 0, sv);
    write(sv[0], "x", 1);
    shutdown(sv[0], SHUT_WR);
    char buf[8];
    ssize_t n1 = read(sv[1], buf, sizeof(buf));
    ssize_t n2 = read(sv[1], buf, sizeof(buf)); /* EOF → 0 */
    printf("n1=%zd n2=%zd\n", n1, n2);
    close(sv[0]); close(sv[1]);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 134 / 6  
- [ ] 能说 shutdown 半关闭，FD 还在  
- [ ] 能说 close 经 socketops → soclose  
- [ ] 能对比半关闭 vs 释放把手  
- [ ] 填好 `notes/daily/day-25.md`

下一步：Day 26 → [`shm_open` / `shm_unlink` / `mmap`](day-26.md)
