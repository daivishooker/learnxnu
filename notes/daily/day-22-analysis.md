# 源码分析：Day 22（socket / bind / listen）

基于 `xnu-12377.121.6`。套接字创建与监听前半段。

---

## 1. 心智模型

```text
用户 FD
  → fileproc / fileglob（f_ops = socketops）
       → struct socket
            → 协议域 / PCB（TCP/UDP/本地套接字等）

服务端前半：
  socket → bind → listen →（Day 23）accept
```

---

## 2. socket 主路径

[`uipc_syscalls.c`](../../xnu/bsd/kern/uipc_syscalls.c)：

```
socket_common
  falloc → fd + fileproc
  f_flag = FREAD|FWRITE
  f_ops = socketops
  socreate(domain, type, protocol) → struct socket *
  fp_set_data(fp, so)
  返回 fd
```

`socreate`（`uipc_socket.c`）按 domain/type 接到协议开关（protosw），分配 socket 与协议控制块。今天跟到“造出 so 并挂上 FD”即可。

---

## 3. bind 主路径

```
bind(s, name, namelen)
  file_socket(s) → so（不是 socket → ENOTSOCK）
  getsockaddr / getsockaddr_s → 内核 sockaddr
  sobindlock(so, sa, …)
```

把本地地址交给协议栈（端口占用、权限等在更下层检查）。

---

## 4. listen 主路径

```
listen(s, backlog)
  file_socket(s)
  solisten(so, backlog)
```

标记可接受连接、整理队列长度。之后入站 SYN 等由协议栈处理，完整连接再由 `accept` 取出。

---

## 5. 和 fileglob 模型对接

| 对象 | 数据指针 | ops |
|------|----------|-----|
| 文件 | vnode | vnops |
| 管道 | pipe | pipeops |
| 套接字 | socket | **socketops** |

`read`/`write`/`ioctl`/`kevent` 盯 socket FD，都走这套。

---

## 6. 建议点开的文件

1. `syscalls.master` — 97 / 104 / 106  
2. `uipc_syscalls.c` — `socket_common` / `bind` / `listen`  
3. `uipc_socket.c` — `socreate` / `sobindlock` / `solisten` 函数头  

验收：能画服务端 `socket→bind→listen`；能说 FD 背后是 `struct socket`。
