# 第二十二天（Day 22）正文

学这三个：**`socket` / `bind` / `listen`**  
源码：`xnu/` = **xnu-12377.121.6**

进入第 4 周：网络。先把套接字生命周期的**前半段**走通——造出来、绑地址、开始听。

生活类比（服务器）：

1. `socket`：装一部电话  
2. `bind`：登记自己的号码（IP:端口）  
3. `listen`：开始坐席听电话（允许排队）  

（明天才是 `accept` 接听、`connect` 拨号。）

---

## 今天目标

1. 找到编号 **97 / 104 / 106**  
2. 理解 `socket`：分配 FD + 内核 `struct socket`，ops 为 `socketops`  
3. 理解 `bind`：把本地地址绑到这个 socket  
4. 理解 `listen`：把 socket 标成监听、设 backlog  

笔记：[`notes/daily/day-22.md`](../notes/daily/day-22.md)  
分析：[`notes/daily/day-22-analysis.md`](../notes/daily/day-22-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| socket | **97** | 创建套接字，返回 FD |
| bind | **104** | 绑定本地地址 |
| listen | **106** | 进入监听状态 |

---

## 1. socket（#97）——造一个能当 FD 用的通信端点

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c)：

```c
socket(domain, type, protocol) {
    falloc → 新 FD / fileproc
    fp->f_ops = &socketops          // 和 pipe/文件一样走 fileglob 模型
    socreate(domain, &so, type, protocol)  // 内核 socket 对象
    fp_set_data(fp, so)
    *retval = fd
}
```

参数直觉：

| 参数 | 例子 |
|------|------|
| domain | `AF_INET` / `AF_INET6` / `AF_UNIX` |
| type | `SOCK_STREAM`（TCP 类）/ `SOCK_DGRAM`（UDP 类） |
| protocol | 常 0=默认；或明确 IPPROTO_TCP 等 |

和 Day 14 对照：又是 **FD → fileglob → 数据指针（这里是 `struct socket`）+ `socketops`**。

---

## 2. bind（#104）——挂上本地地址

```c
bind(s, name, namelen) {
    file_socket(s, &so)             // FD 必须是 socket
    getsockaddr(...)                // copyin 用户 sockaddr
    sobindlock(so, sa, …)           // 协议栈完成绑定
}
```

常见：服务器 `bind(fd, {AF_INET, 端口, INADDR_ANY}, …)`。  
绑成功后，这个 socket 就有了“我在这个地址上等”的身份。

---

## 3. listen（#106）——开始听（仅面向连接）

```c
listen(s, backlog) {
    file_socket(s, &so)
    solisten(so, backlog)
}
```

要点：

- 主要用于 **`SOCK_STREAM`**（TCP）这类面向连接的套接字  
- `backlog`：未完成/待 accept 的连接排队长度提示  
- 之后客户端 `connect`，服务端用明天的 `accept` 取出连接  

UDP（`SOCK_DGRAM`）一般不走 listen/accept 这套。

---

## 今日串起来（服务端前半）

```text
socket() → bind(本地地址) → listen(backlog)
                ↓
         明天：accept() 接连接
```

| 调用 | 内核关键动作 |
|------|----------------|
| socket | `falloc` + `socreate` + `socketops` |
| bind | `sobindlock` |
| listen | `solisten` |

---

## 做完打勾

- [ ] 找到 97 / 104 / 106  
- [ ] 能说 socket 返回 FD，背后是 struct socket  
- [ ] 能说 bind 绑本地地址  
- [ ] 能说 listen 进入监听  
- [ ] 填好 `notes/daily/day-22.md`

下一步：Day 23 → `accept` / `connect` / `socketpair`
