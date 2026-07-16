# 第二十一天（Day 21）正文

学这三个：**`ioctl` / `sysctl` / `getrlimit`**  
源码：`xnu/` = **xnu-12377.121.6**

第 3 周收尾：杂项**控制面**。计划要求——**只跟主路径到分发点**，别一天啃完每个 ioctl 命令或每个 sysctl OID。

生活类比：

- `ioctl`：对着某个已打开的设备/FD 喊具体命令  
- `sysctl`：问/改系统里挂着的一棵“配置树”  
- `getrlimit`：查当前进程某类资源上限（能开多少 FD、栈多大…）

---

## 今天目标

1. 找到编号 **54 / 202 / 194**  
2. 理解 `ioctl`：`fd + cmd + 数据` 分发到文件/设备  
3. 理解 `sysctl`：按名字（MIB）读写内核参数  
4. 理解 `getrlimit`：读进程资源限制  

笔记：[`notes/daily/day-21.md`](../notes/daily/day-21.md)  
分析：[`notes/daily/day-21-analysis.md`](../notes/daily/day-21-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| ioctl | **54** | 对 FD 发设备/文件相关控制命令 |
| sysctl | **202** | 读/写内核 sysctl 节点 |
| getrlimit | **194** | 查询进程资源限制 |

---

## 1. ioctl（#54）——对着 FD 下命令

[`sys_generic.c`](../xnu/bsd/kern/sys_generic.c)：

```c
ioctl(fd, com, data) {
    size = IOCPARM_LEN(com)     // 命令编码里带了参数大小/方向
    按 IOC_IN/OUT copyin 或准备缓冲
    fp_lookup(fd)
    少数通用命令直接处理（如 FIOCLEX / FIONBIO）
    更多 → fo_ioctl(fp, com, …)  // 落到 vnode/设备/socket 各自实现
}
```

要点：

- **同一个 syscall，无数命令**：`com` 决定干什么  
- 命令里常编码：要拷多少字节、方向是进还是出  
- 真正干活的是 **这个 FD 背后对象** 的 ioctl 实现  

今天验收：能说「lookup FD → 按 cmd 分发」，不必背 TTY/磁盘每个码。

---

## 2. sysctl（#202）——内核配置树

[`kern_newsysctl.c`](../xnu/bsd/kern/kern_newsysctl.c)：

```c
sysctl(name, namelen, old, oldlenp, new, newlen) {
    copyin name[]          // 一串整数 OID，如 kern.xxx
    组 sysctl_req
    userland_sysctl(...)   // 在 sysctl 树里找到节点，读 old / 写 new
}
```

要点：

- **按路径找节点**（MIB：`name[0], name[1], …`）  
- 可读（`old`）、可写（`new`），很多只读  
- 用户常用 `sysctl kern.hostname` 这类字符串接口，库会转成 OID  

今天验收：能说「名字 → 树查找 → 读/写」，别展开整棵树。

---

## 3. getrlimit（#194）——资源上限查询

[`kern_resource.c`](../xnu/bsd/kern/kern_resource.c)：

```c
getrlimit(which, rlp) {
    if (which 非法) → EINVAL
    lim = proc_limitget(p, which)   // 当前进程的 soft/hard limit
    copyout(&lim, rlp)
}
```

常见 `which`：`RLIMIT_NOFILE`（最多多少 FD）、`RLIMIT_STACK`、`RLIMIT_NPROC`…  
（`setrlimit` 是改；今天只看 get。）

和前面联系：Day 3 `getdtablesize`、fork 时的进程数限制，都和这类 limit 有关。

---

## 今日对比

| | ioctl | sysctl | getrlimit |
|--|-------|--------|-----------|
| 作用对象 | 某个 **FD** | **系统/内核节点** | **当前进程** |
| 接口形状 | fd + 命令码 | OID 路径 | which 枚举 |
| 今天深度 | 跟到分发 | 跟到树查找 | 跟到 copyout |

第 3 周验收可回顾：`mmap` 接 Mach VM；`poll`/`kevent` 对比；今天三个是“控制/查询”旁路。

---

## 做完打勾

- [ ] 找到 54 / 202 / 194  
- [ ] 能说 ioctl：FD + cmd 分发  
- [ ] 能说 sysctl：MIB 树读/写  
- [ ] 能说 getrlimit：读进程 rlimit  
- [ ] 填好 `notes/daily/day-21.md`

下一步：Day 22 → `socket` / `bind` / `listen`（第 4 周：网络）
