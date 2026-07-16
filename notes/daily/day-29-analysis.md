# 源码分析：Day 29（getsockname / getpeername / setsockopt）

基于 `xnu-12377.121.6`。套接字地址查询与选项写入。

---

## 1. 心智模型

```text
PCB 里有：本地地址、（已连接时）对端地址

getsockname：FD → so → pru_sockaddr → 用户缓冲
getpeername：FD → so → 检查已连接 → pru_peeraddr → 用户缓冲
setsockopt： FD → so → sosetoptlock 改 so / 协议状态
```

接 Day 22–23：地址是 socket 的「号码」；这里是**读出来给人看**，以及**改听筒旋钮**。

---

## 2. getsockname / getpeername

[`uipc_syscalls.c`](../../xnu/bsd/kern/uipc_syscalls.c)：

```
getsockname: pru_sockaddr
getpeername: 未 SS_ISCONNECTED(/CONFIRMING) → ENOTCONN
             双向已 shutdown 一类 → EINVAL
             pru_peeraddr
两者：copyout 地址 + 回写 *alen 实际长度
```

---

## 3. setsockopt

```
SOPT_SET + level/name/val
sosetoptlock
  过滤器 sflt_setsockopt
  非 SOL_SOCKET → pr_ctloutput
  SOL_SOCKET → 通用处理（可先 pru_socheckopt）
```

与 Day 24 `sogetoptlock` 镜像。选项表很大，跟到分发即可。

---

## 4. 建议点开

1. `syscalls.master` — 32 / 31 / 105  
2. `uipc_syscalls.c` — 三个 handler  
3. `uipc_socket.c` — `sosetoptlock` 头  

验收：能说本端/对端怎么查；能说 set/get sockopt 成对。
