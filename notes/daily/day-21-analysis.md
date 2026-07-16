# 源码分析：Day 21（ioctl / sysctl / getrlimit）

基于 `xnu-12377.121.6`。控制面三件套——只跟主路径。

---

## 1. 心智模型

```text
ioctl     → 对“这个打开对象”下命令
sysctl    → 对“内核配置树”读/写
getrlimit → 问“我这个进程限额是多少”
```

计划提醒：ioctl/sysctl **命令空间极大**，今天到分发点即完成。

---

## 2. ioctl 主路径

[`sys_generic.c`](../../xnu/bsd/kern/sys_generic.c)：

```
ioctl(fd, com, data)
  IOCPARM_LEN(com) → 参数长度
  IOC_IN  → copyin；IOC_OUT → 清缓冲备 copyout
  fp_lookup(fd)
  switch 少数通用：FIOCLEX / FIONBIO …
  默认/其余：fo_ioctl(fp, com, datap, ctx)
    → 按 fileops 到 vnode/dev/socket…
```

教学点：`com` 不只是枚举数字，常宏编码了方向与大小。

---

## 3. sysctl 主路径

[`kern_newsysctl.c`](../../xnu/bsd/kern/kern_newsysctl.c)：

```
sysctl(name[], namelen, old, oldlenp, new, newlen)
  copyin name
  sysctl_create_user_req(...)
  userland_sysctl(...)   // 树查找 + handler
  更新 oldlenp 等
```

节点例子（概念）：`kern.*`、`hw.*`、`net.*`…  
写节点常要权限；很多只读。

---

## 4. getrlimit 主路径

[`kern_resource.c`](../../xnu/bsd/kern/kern_resource.c)：

```
getrlimit(which, rlp)
  which ∈ 合法 rlimit 编号
  proc_limitget(current proc, which)
  copyout struct rlimit { rlim_cur, rlim_max }
```

和 fork/`nprocs`、打开文件数等限制同一家族。

---

## 5. 第 3 周串一下

| 天 | 主题 |
|----|------|
| 15–16 | 内存映射与同步 |
| 17–18 | 信号 |
| 19–20 | 多路 IO / kqueue 演进 |
| 21 | 控制与查询杂项 |

---

## 6. 建议点开的文件

1. `syscalls.master` — 54 / 202 / 194  
2. `sys_generic.c` — `ioctl` 开头到 `fo_ioctl`  
3. `kern_newsysctl.c` — `sysctl` → `userland_sysctl`  
4. `kern_resource.c` — `getrlimit`  

验收：能用一句话说清三个调用各自管谁；不要求背命令表。
