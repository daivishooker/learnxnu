# 第六十三天（Day 63）正文

学这五个：**`umask` / `mlock` / `munlock` / `mlockall` / `munlockall`**  
源码：`xnu/` = **xnu-12377.121.6**

两块打包：建文件时的**默认权限掩码**，以及把内存页**钉住不换出**。

生活类比：

1. `umask`：开店默认规矩——新文件自动抠掉哪些权限位（如默认不给 other 写）  
2. `mlock` / `munlock`：把某段内存钉在物理页上，别被换到磁盘  
3. `mlockall` / `munlockall`：想钉住整个地址空间——**本树未实现**（`ENOSYS`）  

---

## 今天目标

1. 找到编号 **60 / 203 / 204 / 324 / 325**  
2. 理解 `umask`：读写 `p->p_fd.fd_cmask`；创建时 `mode & ~cmask`  
3. 理解 `mlock` → `vm_map_wire`；`munlock` → `vm_map_unwire`  
4. 知道本树 `mlockall`/`munlockall` 直接 `ENOSYS`  

笔记：[`notes/daily/day-63.md`](../notes/daily/day-63.md)  
分析：[`notes/daily/day-63-analysis.md`](../notes/daily/day-63-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| umask | **60** | 设/返回进程创建掩码（`fd_cmask`） |
| mlock | **203** | 锁定地址范围（wire） |
| munlock | **204** | 解锁地址范围 |
| mlockall | **324** | 锁定全部（本树 **ENOSYS**） |
| munlockall | **325** | 解锁全部（本树 **ENOSYS**） |

---

## 1. umask（#60）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
umask(newmask) {
    retval = 旧的 fd_cmask
    fd_cmask = newmask & ALLPERMS
}

// 创建时（mkdir/open/mknod 等一再出现）：
va_mode = (mode & ACCESSPERMS) & ~p->p_fd.fd_cmask
```

要点：

- 返回值是**旧** umask；同时设成新值  
- 掩码含义：位为 1 的权限在创建时被**去掉**  
  - 例：`umask(022)` → 请求 `0666` 实际常得 `0644`  
- 进程属性，不是文件属性；`fork` 会继承  

---

## 2. mlock / munlock（#203 / #204）

[`kern_mman.c`](../xnu/bsd/kern/kern_mman.c)：

```c
mlock(addr, len) {
    vm_map_wire_kernel(current_map(), addr, end, ..., TRUE)
    // SUCCESS→0；资源不足→EAGAIN；保护失败→EPERM 等
}

munlock(addr, len) {
    vm_map_unwire(current_map(), addr, end, TRUE)
}
```

要点：

- **wire**：页留在物理内存，避免换页抖动（实时、密码学缓冲等场景）  
- 消耗物理页与锁定额度，失败常见 `EAGAIN`/`ENOMEM`  
- 对照 Day 15 `mmap`：映射出空间；`mlock` 是再钉住  

---

## 3. mlockall / munlockall（#324 / #325）

```c
mlockall(...)   { return ENOSYS; }
munlockall(...) { return ENOSYS; }
```

本树 BSD 包装**未实现**整地址空间锁定。需要时用分段 `mlock`，或走 Mach 侧其它路径（不在今天范围）。

---

## 用户层 Demo

```c
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    mode_t old;
    char *p;
    size_t len = 4096;
    int fd;
    struct stat st;

    /* Demo A：umask */
    old = umask(022);
    printf("umask: old=%04o now set 022\n", (unsigned)old);
    fd = open("/tmp/day63_umask.txt", O_CREAT | O_RDWR | O_TRUNC, 0666);
    if (fd < 0) { perror("open"); return 1; }
    if (fstat(fd, &st) != 0) { perror("fstat"); return 1; }
    printf("umask effect: created mode=%04o (expect ~0644)\n",
           (unsigned)(st.st_mode & 0777));
    close(fd);
    (void)unlink("/tmp/day63_umask.txt");
    (void)umask(old); /* 恢复 */

    /* Demo B：mlock / munlock */
    p = mmap(NULL, len, PROT_READ | PROT_WRITE,
             MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    memset(p, 0x5a, len);
    if (mlock(p, len) != 0) {
        perror("mlock");
        munmap(p, len);
        return 1;
    }
    printf("mlock ok\n");
    if (munlock(p, len) != 0) {
        perror("munlock");
        munmap(p, len);
        return 1;
    }
    printf("munlock ok\n");
    munmap(p, len);

    /* Demo C：本树/平台上 mlockall 可能 ENOSYS */
    if (mlockall(MCL_CURRENT) != 0) {
        printf("mlockall: %s (XNU stub is ENOSYS)\n", strerror(errno));
    } else {
        printf("mlockall ok\n");
        (void)munlockall();
    }

    printf("day63 ok\n");
    return 0;
}
```

```bash
cc -o day63_demo day63_demo.c && ./day63_demo
```

> Demo 需 `#include <fcntl.h>`（上例 `open`）。Linux 上 `mlockall` 可能成功，与 XNU stub 不同。

---

## 做完打勾

- [ ] 找到五个编号  
- [ ] 能说 umask ↔ `fd_cmask` 与 `mode & ~cmask`  
- [ ] 能说 mlock ↔ wire；mlockall 本树 ENOSYS  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-63.md`

下一步：Day 64 → [杂项五件套](day-64.md)（`revoke` / `acct` / `gethostuuid` / `minherit` / `swapon`）
