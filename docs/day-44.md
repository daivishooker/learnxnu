# 第四十四天（Day 44）正文

学这两个：**`chmod` / `chown`**  
源码：`xnu/` = **xnu-12377.121.6**

从 xattr「便签」回到经典元数据：**权限位**与**属主/属组**。

生活类比：

1. `chmod`：改门锁规则（谁可读/写/执行）  
2. `chown`：改这扇门归谁、属哪个组  

---

## 今天目标

1. 找到编号 **15 / 16**  
2. 理解 `chmod`：路径 → `chmodat` → `chmod_vnode` → `vnode_setattr(va_mode)`  
3. 理解 `chown`：路径 → `vn_chown_internal` → `vnode_setattr(va_uid/va_gid)`  
4. 能对比：改 mode vs 改 owner；二者都落在 `vnode_setattr`  

笔记：[`notes/daily/day-44.md`](../notes/daily/day-44.md)  
分析：[`notes/daily/day-44-analysis.md`](../notes/daily/day-44-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| chmod | **15** | 改路径对象的权限位（mode） |
| chown | **16** | 改路径对象的 uid / gid |

（FD 版：`fchmod` #124、`fchown` #123；还有 `fchmodat` / `fchownat`。）

---

## 1. chmod（#15）——改权限位

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
chmod(path, mode) {
    fchmodat_internal(..., AT_FDCWD)
      VATTR_SET(va_mode, mode & ALLPERMS)
      chmodat → nameiat(path) → vp
        chmod_vnode → authorize → vnode_setattr(vp, &va)
}
```

要点：

- `mode` 会与 `ALLPERMS` 掩一下，只保留权限相关位  
- 路径仍经 `namei`/`nameiat` 从用户地址取入  
- master 标了 `NO_SYSCALL_STUB`：libc 可能走 `fchmodat` 等包装，编号仍是 15  
- 鉴权失败时常把 `EACCES` 转成 `EPERM`  

---

## 2. chown（#16）——改属主/属组

```c
chown(path, uid, gid) {
    fchownat_internal(AT_FDCWD, path, uid, gid, ...)
      nameiat → vp
      vn_chown_internal:
        可选设置 va_uid / va_gid（VNOVAL 表示不改该项）
        vnode_authattr + authorize
        vnode_setattr
}
```

要点：

- 普通用户通常**不能随意改属主**（需特权）；改组也有规则  
- `uid`/`gid` 传 `-1`（`VNOVAL`）表示「这一项不动」  
- 与 `chmod` 共用「忙锁」序列化，减少竞态  
- `lchown` 不跟随符号链接；`chown` 默认跟随  

对照：

| | 改什么 | vnode_attr 字段 |
|--|--------|-----------------|
| chmod | 权限位 | `va_mode` |
| chown | 所有者 | `va_uid` / `va_gid` |

两者最终都是 **setattr**，不是改文件内容。

---

## 用户层 Demo

```c
#include <stdio.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    const char *path = "/tmp/day44_perm.txt";
    struct stat st;

    int fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    close(fd);

    /* Demo A：chmod */
    if (chmod(path, 0600) != 0) {
        perror("chmod");
        return 1;
    }
    if (stat(path, &st) != 0) { perror("stat"); return 1; }
    printf("mode after chmod: %o\n", st.st_mode & 0777);

    /* Demo B：chown — 普通用户常只能「改成自己」或失败；演示调用本身 */
    if (chown(path, getuid(), getgid()) != 0) {
        perror("chown");
        /* 无特权时可能 EPERM，仍算理解到入口 */
    } else {
        printf("chown ok: uid=%d gid=%d\n", getuid(), getgid());
    }
    return 0;
}
```

```bash
cc -o day44_demo day44_demo.c && ./day44_demo
```

---

## 做完打勾

- [ ] 找到 15 / 16  
- [ ] 能说 chmod：namei → setattr(va_mode)  
- [ ] 能说 chown：namei → setattr(uid/gid)  
- [ ] 跑通 Demo（chmod 为重点）  
- [ ] 填好 `notes/daily/day-44.md`

下一步：Day 45 → `utimes` / `futimes`（#138 / #139）
