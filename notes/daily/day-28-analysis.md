# 源码分析：Day 28（第 4 周查漏补缺）

基于 `xnu-12377.121.6`。不新开主路径，串联本周易混点与源码锚点。

---

## 1. 总图

```text
创建：socket / bind / listen
建连：accept（服务端新 fd） / connect（客户端原 fd） / socketpair
收发：sendmsg / recvmsg → pru_sosend / pru_soreceive → so_snd / so_rcv
收尾：shutdown（方向） / close（soo_close → soclose）
旁路：shm（共享物理页）· ptrace/sysctl（强门禁控制面）
```

---

## 2. 锚点文件（重读时点开）

| 主题 | 文件 | 看什么 |
|------|------|--------|
| socket/bind/listen | `uipc_syscalls.c` / `uipc_socket.c` | `socreate` / `sobindlock` / `solisten` |
| accept/connect | 同上 | `accept_nocancel` 的 `so_comp`；`soconnectlock` |
| send/recv | 同上 | `sendit` / `recvit`；`sosend` / `soreceive` |
| shutdown/close | `uipc_socket.c` / `sys_socket.c` | `soshutdown`；`soo_close` |
| shm | `posix_shm.c` / `kern_mman.c` | `pshmops` 无读写；`pshm_mmap` |
| ptrace/sysctl | `mach_process.c` / `kern_newsysctl.c` | `cantrace`；`userland_sysctl` |

---

## 3. 易错清单（对照自问）

1. 地址会不会先转成 FD？——不会。  
2. 每个 socket 的 `so_comp` 都当排队口吗？——字段都有，只有 listen 头当真用。  
3. 客户端 connect 返回新 FD 吗？——不，还是原 FD。  
4. copyin(msghdr) 是否拷走全部数据？——否，先说明书。  
5. getsockopt 能改选项吗？——不能，用 setsockopt。  
6. shutdown 丢 FD 吗？——不丢。  

---

## 4. 验收

能不看笔记画出：服务端四步、客户端三步、收发包与 so_rcv、半关闭与 close。  
能说清：两套索引、accept 新对象、消息 copy 边界。
