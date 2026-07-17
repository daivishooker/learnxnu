# 源码分析：Day 59（杂项六件套）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
sendfile(filefd, sockfd, ...):
  正则文件 + 已连接流套接字 → 内核搬运

fdatasync(fd) / fsync(fd):
  fsync_common(MNT_DWAIT / MNT_WAIT) → VNOP_FSYNC

sendto / recvfrom:
  简易 msghdr → sendit / recvit → pru_sosend / pru_soreceive

getdirentries:
  getdirentries_common(旧) ；getdirentries64 带 EXTENDED

access_extended:
  批量路径 → access1（real 凭证）
```

---

## 2. 建议点开

1. `syscalls.master` — 337 / 187 / 133 / 29 / 196 / 284  
2. `uipc_syscalls.c` — `sendfile` / `sendto_nocancel` / `recvfrom_nocancel`  
3. `vfs_syscalls.c` — `fdatasync` / `fsync_common` / `getdirentries` / `access_extended`  
4. 对照 Day 24、34、37、55

验收：能说清归一关系；Demo（fdatasync + UDP）能跑。
