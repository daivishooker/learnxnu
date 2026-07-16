# 源码分析：Day 25（shutdown / close）

基于 `xnu-12377.121.6`。套接字半关闭与 FD 释放。

---

## 1. 心智模型

```text
shutdown(how)：
  fd 仍在文件表
  socket 标记 SS_CANTRCVMORE / SS_CANTSENDMORE 等
  写方向：pru_shutdown（如 TCP 发 FIN）

close：
  文件表去掉 fd
  fileglob 引用 → 0 时 soo_close → soclose
  协议断开、清 so_comp/缓冲等，引用归零 sofree
```

和前几天一致：进程侧永远用 **FD** 找到对象；`shutdown` 改对象能力，`close` 丢掉把手。

---

## 2. shutdown 主路径

[`uipc_syscalls.c`](../../xnu/bsd/kern/uipc_syscalls.c) → [`uipc_socket.c`](../../xnu/bsd/kern/uipc_socket.c)：

```
file_socket → so
soshutdown(so, how)
  how ∈ {SHUT_RD, SHUT_WR, SHUT_RDWR}
  未连接 → ENOTCONN
  soshutdownlock → soshutdownlock_final
    SHUT_RD 侧：sorflush（冲接收侧）
    SHUT_WR 侧：pru_shutdown
```

FD 不释放。半关闭后仍可用同一 fd 做未关掉的那一侧（常见：`SHUT_WR` 后继续读）。

---

## 3. close（socket）主路径

```
close(fd)                    // kern_descrip 等通用路径
  释放文件表槽位
  fileglob 最后引用 → fo_close
    socketops.fo_close = soo_close   // sys_socket.c
      fg_set_data(NULL)
      soclose(so)                    // uipc_socket.c
        soclose_locked：断协议、清队列、减引用/释放
```

`dup` 过的多个 FD 共享同一 `fileglob`/socket：每个 `close` 减引用，最后一个才 `soclose` 真正收场。

监听 socket 的 `soclose` 还会清掉 `so_comp` / `so_incomp` 上未 accept 的连接（`soabort` 等）——跟到「会清理排队连接」即可。

---

## 4. 和 Day 4 / Day 22–24 对接

| 天 | 关系 |
|----|------|
| Day 4 `close` | 通用 FD 释放骨架 |
| Day 22–23 | 创建/建连留下的 socket + FD |
| Day 24 | 收发用的就是这个对象 |
| Day 25 | 半关闭或拆掉把手 |

---

## 5. 建议点开的文件

1. `syscalls.master` — 134 / 6  
2. `uipc_syscalls.c` — `shutdown`  
3. `uipc_socket.c` — `soshutdown` / `soclose` 函数头  
4. `sys_socket.c` — `socketops` / `soo_close`  

验收：能说清「shutdown 不丢 FD；close 丢 FD；最后引用才销毁 socket」。
