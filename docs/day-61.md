# 第六十一天（Day 61）正文

学这六个：**`getgroups` / `setgroups` / `initgroups` / `getlogin` / `setlogin` / `chroot`**  
源码：`xnu/` = **xnu-12377.121.6**

承接 Day 60 的 uid/gid 三角：今天看**补充组列表**、**会话登录名**，以及把进程关进新「根目录」的 `chroot`。

生活类比：

1. `getgroups` / `setgroups` / `initgroups`：你不止一个组徽章，口袋里一串补充组  
2. `getlogin` / `setlogin`：这台终端会话挂的「登录名牌」（不等于 uid）  
3. `chroot`：把进程眼里的「`/`」换成某棵子树，像换了一个笼子根  

---

## 今天目标

1. 找到编号 **79 / 80 / 243 / 49 / 50 / 61**  
2. 理解补充组在 `cr_groups[]`；`setgroups`/`initgroups` 汇入 `setgroups1`  
3. 理解 login 名挂在 **session**（`s_login`），不是凭证 uid  
4. 理解 `chroot`：特权 + 路径 → 设 `fd_rdir`（进程根 vnode）  

笔记：[`notes/daily/day-61.md`](../notes/daily/day-61.md)  
分析：[`notes/daily/day-61-analysis.md`](../notes/daily/day-61-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getgroups | **79** | 读补充组列表 |
| setgroups | **80** | 设补充组（偏兼容；退出 memberd 参与） |
| initgroups | **243** | 设补充组并绑定 gmuid（登录路径常用） |
| getlogin | **49** | 读当前 session 登录名 |
| setlogin | **50** | 设 session 登录名（特权） |
| chroot | **61** | 改变进程根目录（特权） |

---

## 1. getgroups / setgroups / initgroups

[`kern_prot.c`](../xnu/bsd/kern/kern_prot.c)：

```c
getgroups(size, set) {
    cred → cr_groups[0..cr_ngroups)
    size==0 → 只返回个数
    否则 copyout 整表
}

setgroups(size, set)  = setgroups1(..., gmuid=KAUTH_UID_NONE)  // 退出扩展组解析参与
initgroups(size, set, gmuid) = setgroups1(..., gmuid)         // 参与 memberd 一类解析

setgroups1 → proc_suser → kauth_cred_model_setgroups(...)
```

要点：

- 补充组回答「除了 primary egid，还算哪些组的成员」  
- **改组列表要特权**（`proc_suser`）  
- `initgroups` 是 login 类程序的正路：先摆好组 + gmuid，再 `setuid` 丢掉特权  
- `setgroups` 多留给 POSIX 兼容；注释写明多数程序应优先 `initgroups`  

与 Day 60 对照：`setgid`/`setegid` 动的是「主」组身份；这里是**一串额外组**。

---

## 2. getlogin / setlogin

```c
getlogin(buf, len) {
    session → s_login → copyout
}

setlogin(name) {
    proc_suser
    copyinstr → setlogin_internal → session.s_login
}
```

要点：

- 挂在 **session**，同一会话里的进程共享这份名字  
- **不是** uid，也不是 `/etc/passwd` 实时查询；只是内核里存的登录名字符串  
- 改要特权；libc 的 `getlogin()` 有时还会走别的路径，syscall 本体是上面这条  

---

## 3. chroot（#61）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
chroot(path) {
    suser(...)
    namei(LOOKUP) → 目录 vnode
    设 p->p_fd.fd_rdir = 该 vnode   // 之后「/」从这个 vnode 起算
    若已在 chroot 中，常同步改 fd_cdir
}
```

要点：

- 需要特权；路径解析相对**当前**根与 cwd  
- 只改**这个进程**眼里的根，不是整机  
- 已打开的 FD、以及逃逸手法（相对 `..`、传 FD）另当别论——`chroot` 不是完整沙箱  
- 与 Day 8 `chdir`：一个改 cwd，一个改 root  

---

## 用户层 Demo

> `setgroups`/`initgroups`/`setlogin`/`chroot` 通常要特权。Demo 覆盖可读的 `getgroups` + `getlogin`。

```c
#define _GNU_SOURCE
#include <limits.h>
#include <stdio.h>
#include <unistd.h>

#ifndef NGROUPS_MAX
#define NGROUPS_MAX 64
#endif

int main(void) {
    gid_t groups[NGROUPS_MAX];
    int n, cap;
    char name[64];

    n = getgroups(0, NULL);
    if (n < 0) { perror("getgroups size"); return 1; }
    cap = n;
    if (cap > (int)(sizeof(groups) / sizeof(groups[0]))) {
        cap = (int)(sizeof(groups) / sizeof(groups[0]));
    }
    n = getgroups(cap, groups);
    if (n < 0) { perror("getgroups"); return 1; }

    printf("getgroups ok count=%d first=%d\n", n, n > 0 ? (int)groups[0] : -1);

    if (getlogin_r(name, sizeof(name)) != 0) {
        perror("getlogin_r");
        printf("getlogin_r unavailable/empty\n");
    } else {
        printf("getlogin_r ok name=%s\n", name);
    }

    printf("day61 read-side ok\n");
    return 0;
}
```

```bash
cc -o day61_demo day61_demo.c && ./day61_demo
```

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能说 setgroups/initgroups 汇入 setgroups1  
- [ ] 能说 login 名在 session，chroot 改 fd_rdir  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-61.md`

下一步：Day 62 → 进程组/会话（`getpgrp` / `setpgid` / `setsid` / `getpgid` / `getsid` 等）
