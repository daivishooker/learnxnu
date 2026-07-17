# 第六十四天（Day 64）正文

学这五个：**`revoke` / `acct` / `gethostuuid` / `minherit` / `swapon`**  
源码：`xnu/` = **xnu-12377.121.6**

杂项打包：设备访问吊销、进程记账、主机 UUID、映射继承策略、交换分区（本树未支持）。

生活类比：

1. `revoke`：宣布某块设备门牌作废，已开门的也得清场  
2. `acct`：打开/关掉「进程进出流水账」文件  
3. `gethostuuid`：问这台机器的出厂身份牌  
4. `minherit`：规定这段内存给孩子进程时怎么继承  
5. `swapon`：挂上交换分区——**本树直接 `ENOTSUP`**  

---

## 今天目标

1. 找到编号 **56 / 51 / 142 / 250 / 85**  
2. 理解 `revoke`：只对字符/块设备；属主或 root → `VNOP_REVOKE`  
3. 理解 `acct`：root 指定记账文件或 `NULL` 关闭  
4. 理解 `minherit` → `mach_vm_inherit`；`swapon` 本树未实现  

笔记：[`notes/daily/day-64.md`](../notes/daily/day-64.md)  
分析：[`notes/daily/day-64-analysis.md`](../notes/daily/day-64-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| revoke | **56** | 吊销设备 vnode 上的访问 |
| acct | **51** | 开/关进程记账 |
| gethostuuid | **142** | 取平台 UUID |
| minherit | **250** | 设映射区继承属性 |
| swapon | **85** | 启用交换（本树 **ENOTSUP**） |

---

## 1. revoke（#56）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
revoke(path) {
    namei → vp
    须为 VCHR 或 VBLK；块设备若已挂载 → EBUSY
    属主或 suser
    若仍有引用 → VNOP_REVOKE(vp, REVOKEALL, ...)
}
```

要点：踢掉对该设备节点的打开引用（经典场景：伪终端/登录相关）。普通文件不适用（`ENOTSUP`）。

---

## 2. acct（#51）

[`kern_acct.c`](../xnu/bsd/kern/kern_acct.c)：

```c
acct(path) {
    suser 必须
    path != NULL → vn_open 写普通文件，设为 acctp；启动 acctwatch
    path == NULL → 关掉记账
}
```

进程退出时内核可往记账文件写一条记录（历史 UNIX 会计）。现代 macOS 上很少直接用。

---

## 3. gethostuuid（#142）

[`sys_generic.c`](../xnu/bsd/kern/sys_generic.c)：

```c
gethostuuid(uuid_buf, timeout) {
    可选 entitlement / MAC 检查
    copyin timeout → IOBSDGetPlatformUUID(...)
    copyout 16 字节 UUID
}
```

要点：平台级标识，不是进程 UUID；常需 entitlement 或策略放行。

---

## 4. minherit（#250）

[`kern_mman.c`](../xnu/bsd/kern/kern_mman.c)：

```c
minherit(addr, len, inherit) {
    sanitize → mach_vm_inherit(current_map(), addr, size, inherit)
}
```

常见 `inherit`：`MAP_INHERIT_NONE` / `COPY` / `SHARE` / `ZERO` 等——控制 **`fork` 后**这段映射怎么出现在子进程。对照 Day 15 `mmap`。

---

## 5. swapon（#85）

```c
swapon(...) { return ENOTSUP; }
```

本树 BSD 入口未接真实换页设备管理；交换由 VM 子系统其它路径处理。

---

## 用户层 Demo

> `revoke`/`acct`/`gethostuuid`/`swapon` 偏特权或 Darwin。Demo 覆盖可移植的 `minherit`。

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#ifndef MAP_INHERIT_NONE
/* Linux 用 madvise(MADV_DONTFORK) 等；此处仅在有 minherit 时演示 */
#endif

int main(void) {
#if defined(__APPLE__) || defined(__FreeBSD__)
    size_t len = 4096;
    char *p = mmap(NULL, len, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    memset(p, 'A', len);

    if (minherit(p, len, MAP_INHERIT_NONE) != 0) {
        perror("minherit");
        munmap(p, len);
        return 1;
    }
    printf("minherit(MAP_INHERIT_NONE) ok\n");
    munmap(p, len);
#else
    printf("minherit: skip on this OS (Darwin/FreeBSD demo)\n");
#endif

    /* swapon 在 XNU 为 ENOTSUP；此处不调用 */
    printf("day64 ok\n");
    return 0;
}
```

```bash
cc -o day64_demo day64_demo.c && ./day64_demo
```

> Linux 上本 Demo 会 skip `minherit`；在 macOS/FreeBSD 上可验证。

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能说 revoke 只打设备；acct 要 root  
- [ ] 能说 minherit 管 fork 继承；swapon 本树 ENOTSUP  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-64.md`

下一步：Day 65 → `proc_info` / `csops` / `csops_audittoken` / `workq_open` / `workq_kernreturn`
