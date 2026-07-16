# 第二十三天（Day 23）正文

学这三个：**`accept` / `connect` / `socketpair`**  
源码：`xnu/` = **xnu-12377.121.6**

接着 Day 22：前半段造好听筒，今天把**连接接上**——服务端接听、客户端拨号，再加一个本地双端对。

生活类比：

1. `accept`：坐席从排队里**接起一通新电话**（新听筒）  
2. `connect`：客户**拨号**到对方号码  
3. `socketpair`：直接做一对**已经串好的对讲机**（常见本地 `AF_UNIX`）

---

## 今天目标

1. 找到编号 **30 / 98 / 135**  
2. 理解 `accept`：监听 socket **不变**；返回**新 FD** 指向已连接 socket  
3. 理解 `connect`：给已有 socket 填**对端地址**并建立连接  
4. 理解 `socketpair`：一次造两个已互连的 socket + 两个 FD  

笔记：[`notes/daily/day-23.md`](../notes/daily/day-23.md)  
分析：[`notes/daily/day-23-analysis.md`](../notes/daily/day-23-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| accept | **30** | 从监听队列取出一条连接，返回新 FD |
| connect | **98** | 主动连到远端地址 |
| socketpair | **135** | 创建一对已互连的套接字 |

---

## 1. accept（#30）——接听，拿到新听筒

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c) → `accept_nocancel`：

```c
accept(监听fd, name, namelen) {
    fp_get_ftype(..., DTYPE_SOCKET) → head   // 必须是 listen 过的
    等 so_comp 队列非空（可 sleep）
    so = 从 head->so_comp 摘下一条已完成连接
    falloc → newfd
    fp->f_ops = socketops; fp_set_data(fp, so)
    soaccept → 可选 copyout 对端地址
    返回 newfd
}
```

要点：

| 点 | 说明 |
|----|------|
| 监听 FD | 继续听；**不要**拿它去 `read`/`write` 业务数据 |
| 返回值 | **新 FD** → **新的** `struct socket`（已连上） |
| 队列 | 协议栈完成握手后挂进 `so_comp`；`accept` 只是取出并挂 FD |

和昨天串起来：

```text
socket → bind → listen → accept → 业务用新 fd
                         ↑
                   监听 fd 还在排队口
```

---

## 2. connect（#98）——拨号

```c
connect(s, name, namelen) {
    file_socket(s, &so)
    getsockaddr(...)          // copyin 对端地址
    connectit → soconnectlock → pru_connect
    // 阻塞式：可 sleep 直到连上或失败
}
```

要点：

- 用的是**客户端自己的 FD**（Day 22 的 `socket`，常不 `listen`）  
- 对端地址写进 PCB；网络侧之后按四元组 demux 到这个 socket  
- 非阻塞：可能马上返回 `EINPROGRESS`，稍后再用 `select`/`kevent` 等可写  

对比：

| | bind | connect |
|--|------|---------|
| 填哪一端 | **本地**地址 | **对端**地址（并驱动建连） |
| 典型角色 | 服务器登记号码 | 客户端拨号 |

（服务器 `accept` 出来的 socket，对端地址已由协议栈填好。）

---

## 3. socketpair（#135）——一对已串好的本地端

```c
socketpair(domain, type, protocol, int sv[2]) {
    socreate → so1
    socreate → so2
    falloc → sv[0] 挂 so1
    falloc → sv[1] 挂 so2
    soconnect2(so1, so2)       // 内核内互连
    // DGRAM 再 soconnect2(so2, so1)
    copyout(sv, …)
}
```

直觉：像 **pipe**，但是两个都是 **socket FD**（可走 socket 选项、`sendmsg` 传 FD 等）。  
常见：`AF_UNIX` + `SOCK_STREAM`。

---

## 今日串起来

```text
服务端：socket → bind → listen → accept(新fd) → read/write(新fd)
客户端：socket → [可选 bind] → connect(对端) → read/write

本地双端：socketpair → sv[0] / sv[1] 已互连
```

| 调用 | 内核关键动作 |
|------|----------------|
| accept | 从 `so_comp` 取 so + `falloc` 新 FD |
| connect | `soconnectlock` / `pru_connect` |
| socketpair | 两个 `socreate` + `soconnect2` |

心智模型（接昨天）：

- **进程侧**：始终用 **FD** 找对象  
- **网络侧**：用 **地址** demux 到 socket  
- `accept` 多出来的是**另一个对象 + 另一个 FD**，不是把监听 FD「变成」已连接

---

## 用户层 Demo

`socketpair` 最快练 `accept`/`connect` 语义的近亲；也可用 listen+connect+accept 三件套。

```c
#include <stdio.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int sv[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0) {
        perror("socketpair"); return 1;
    }
    write(sv[0], "hi", 2);
    char buf[8] = {0};
    read(sv[1], buf, sizeof(buf) - 1);
    printf("got=%s\n", buf);
    close(sv[0]); close(sv[1]);
    return 0;
}
```

---

## 做完打勾

- [ ] 找到 30 / 98 / 135  
- [ ] 能说 accept 返回新 FD，监听 FD 仍在听  
- [ ] 能说 connect 填对端并建连  
- [ ] 能说 socketpair 一次给两个已互连 FD  
- [ ] 填好 `notes/daily/day-23.md`

下一步：Day 24 → [`sendmsg` / `recvmsg` / `getsockopt`](day-24.md)
