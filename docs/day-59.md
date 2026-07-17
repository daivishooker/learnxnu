# 第五十九天（Day 59）正文

学这六个：**`sendfile` / `fdatasync` / `sendto` / `recvfrom` / `getdirentries` / `access_extended`**  
源码：`xnu/` = **xnu-12377.121.6**

杂项打包：文件→套接字零拷贝发送、刷盘、UDP 常用收发、旧版列目录、批量权限探测。

生活类比：

1. `sendfile`：仓库里的货不经你手里，直接装上车（文件 → 已连接流套接字）  
2. `fdatasync`：把账本**数据**落盘；元数据可少等一会（对照完整 `fsync`）  
3. `sendto` / `recvfrom`：寄/收明信片，信封上写地址（UDP 味最浓）  
4. `getdirentries`：旧式翻目录（现代多用 `getdirentries64`）  
5. `access_extended`：一张表一次探多个路径的权限  

---

## 今天目标

1. 找到编号 **337 / 187 / 133 / 29 / 196 / 284**  
2. 理解 `sendfile`：正则文件 FD + 已连接 `SOCK_STREAM` → 内核侧搬运  
3. 理解 `fdatasync` ≈ `fsync_common(..., MNT_DWAIT)`；`fsync` 用 `MNT_WAIT`  
4. 理解 `sendto`/`recvfrom` 汇入 `sendit`/`recvit`（与 Day 24 `sendmsg`/`recvmsg` 同族）  

笔记：[`notes/daily/day-59.md`](../notes/daily/day-59.md)  
分析：[`notes/daily/day-59-analysis.md`](../notes/daily/day-59-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| sendfile | **337** | 把文件内容发到已连接流套接字 |
| fdatasync | **187** | FD 数据完整性刷盘（弱于完整 fsync） |
| sendto | **133** | 向（可选）地址发送数据 |
| recvfrom | **29** | 收数据并可选取回对端地址 |
| getdirentries | **196** | 旧版读目录项（32/兼容布局） |
| access_extended | **284** | 批量 access 探测 |

---

## 1. sendfile（#337）

[`uipc_syscalls.c`](../xnu/bsd/kern/uipc_syscalls.c)：

```c
sendfile(fd, s, offset, nbytes, hdtr, flags) {
    fp_getfvp(fd) → 须可读正则文件
    file_socket(s) → SOCK_STREAM 且 SS_ISCONNECTED
    可选 hdtr：先发/后发用户缓冲（header/trailer）
    内核从文件 offset 起往 socket 送；更新 *nbytes
}
```

要点：用户缓冲可少拷一层（具体是否真「零拷贝」看路径与硬件）；`flags` 在本树实现里须为 0。

---

## 2. fdatasync（#187）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
fsync(fd)      → fsync_common(..., MNT_WAIT)   // 文件完整性：数据+更多元数据
fdatasync(fd)  → fsync_common(..., MNT_DWAIT)  // 数据完整性：内容可恢复即可
  fp_getfvp → VNOP_FSYNC(vp, flags, ...)
```

与 Day 34 `fsync` 同核，**flags 不同**。

---

## 3. sendto（#133） / recvfrom（#29）

```c
sendto(s, buf, len, flags, to, tolen)
  → 拼成简易 msghdr → sendit → pru_sosend

recvfrom(s, buf, len, flags, from, fromlen)
  → recvit → pru_soreceive；可选 copyout 对端地址
```

对照 Day 24：

| 简单 | 完整 msghdr |
|------|-------------|
| sendto / recvfrom | sendmsg / recvmsg |
| 单缓冲 + 可选地址 | 可多段 iov + control |

UDP 无 connect 时几乎总用 `sendto`/`recvfrom`；TCP 连上后也可用，地址常可忽略。

---

## 4. getdirentries（#196）

```c
getdirentries(fd, buf, count, basep)
  = getdirentries_common(..., flags=0)   // 旧布局
getdirentries64(...)
  = getdirentries_common(..., VNODE_READDIR_EXTENDED)
```

Day 37 已学 64 位版；本调用是**旧 ABI**。新代码优先 `getdirentries64`。

---

## 5. access_extended（#284）

```c
access_extended(entries, size, results, uid) {
    copyin 一批 accessx_descriptor + 路径串
    默认用 real 凭证（与 access 相同）
    对每项 namei → access1
    copyout 每项 errno 结果
}
```

`access` / `faccessat` 的**批量版**；单路径日常仍用后两者。

---

## 用户层 Demo

> `sendfile` / `getdirentries` / `access_extended` 偏 BSD/Darwin。Demo：`sendto`/`recvfrom` + `fdatasync`。

```c
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int fd, srv, cli;
    struct sockaddr_in addr, peer;
    socklen_t peerlen = sizeof(peer);
    char buf[64];
    ssize_t n;
    const char *msg = "day59";

    /* Demo A：fdatasync */
    fd = open("/tmp/day59_sync.txt", O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, msg, strlen(msg)) < 0) { perror("write"); return 1; }
    if (fdatasync(fd) != 0) { perror("fdatasync"); return 1; }
    printf("fdatasync ok\n");
    close(fd);
    (void)unlink("/tmp/day59_sync.txt");

    /* Demo B：UDP sendto / recvfrom 环回 */
    srv = socket(AF_INET, SOCK_DGRAM, 0);
    cli = socket(AF_INET, SOCK_DGRAM, 0);
    if (srv < 0 || cli < 0) { perror("socket"); return 1; }

    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;
    if (bind(srv, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        perror("bind");
        return 1;
    }
    peerlen = sizeof(addr);
    if (getsockname(srv, (struct sockaddr *)&addr, &peerlen) != 0) {
        perror("getsockname");
        return 1;
    }

    if (sendto(cli, msg, strlen(msg), 0,
               (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("sendto");
        return 1;
    }
    peerlen = sizeof(peer);
    n = recvfrom(srv, buf, sizeof(buf) - 1, 0,
                 (struct sockaddr *)&peer, &peerlen);
    if (n < 0) { perror("recvfrom"); return 1; }
    buf[n] = '\0';
    printf("sendto/recvfrom ok msg=%s\n", buf);

    close(cli);
    close(srv);
    return 0;
}
```

```bash
cc -o day59_demo day59_demo.c && ./day59_demo
```

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能说 fdatasync vs fsync 的 flags 差  
- [ ] 能说 sendto/recvfrom 与 sendmsg/recvmsg 的关系  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-59.md`

下一步：Day 60 → 凭证变更扫尾（`setuid` / `setgid` / `seteuid` / `setegid` / `setreuid` / `setregid`）
