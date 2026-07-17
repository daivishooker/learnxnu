# 第四十三天（Day 43）正文

学这两个：**`listxattr` / `removexattr`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天会读写单张便签；今天补上**列出有哪些便签**，以及**撕掉一张**。

生活类比：

1. `listxattr`：把文件外壳上所有便签名字列出来  
2. `removexattr`：按名字撕掉一张便签  

---

## 今天目标

1. 找到编号 **240 / 238**  
2. 理解 `listxattr`：路径 → `vn_listxattr` → `VNOP_LISTXATTR`  
3. 理解 `removexattr`：路径 → `vn_removexattr` → `VNOP_REMOVEXATTR`  
4. 能串起完整 xattr 四件套：set / get / list / remove  

笔记：[`notes/daily/day-43.md`](../notes/daily/day-43.md)  
分析：[`notes/daily/day-43-analysis.md`](../notes/daily/day-43-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| listxattr | **240** | 列出对象上所有扩展属性名 |
| removexattr | **238** | 按名字删除一个扩展属性 |

（FD 版：`flistxattr` #241、`fremovexattr` #239。）

---

## 1. listxattr（#240）——列便签名

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
listxattr(path, namebuf, bufsize, options) {
    namei(path) → vp          // 路径仍经 namei 从用户态取
    可选 UIO → 用户 namebuf
    vn_listxattr → VNOP_LISTXATTR（可 default_listxattr）
    返回写入字节数；namebuf==NULL 时常只问需要多大
}
```

要点：

- 缓冲里是 **NUL 分隔**的名字串：`name1\0name2\0...`  
- 和 `getxattr` 一样走鉴权 `READ_EXTATTRIBUTES`  
- 先 `listxattr(path, NULL, 0, 0)` 拿长度再分配，是常见用法  

---

## 2. removexattr（#238）——删便签

```c
removexattr(path, attrname, options) {
    copyinstr(attrname)       // 属性名显式拷进内核
    namei(path) → vp
    vn_removexattr → VNOP_REMOVEXATTR
    （成功可发 FSE_XATTR_REMOVED）
}
```

要点：

- 受保护名字（某些系统 xattr）可能直接 `EPERM`  
- 不存在 → 常见 `ENOATTR`  
- 与 `setxattr` 对称：写侧贴上，这里撕掉  

四件套对照：

| 操作 | 调用 |
|------|------|
| 写 | setxattr |
| 读 | getxattr |
| 列 | listxattr |
| 删 | removexattr |

---

## 用户层 Demo

```c
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/xattr.h>

int main(void) {
    const char *path = "/tmp/day43_xattr.txt";
    const char *key = "user.day43.note";
    char names[256];
    ssize_t n;
    char *p;

    int fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    close(fd);

    if (setxattr(path, key, "bye", 3, 0, 0) != 0) {
        perror("setxattr");
        return 1;
    }

    /* Demo A：listxattr */
    n = listxattr(path, names, sizeof(names), 0);
    if (n < 0) {
        perror("listxattr");
        return 1;
    }
    printf("xattrs:\n");
    for (p = names; p < names + n; p += strlen(p) + 1)
        printf("  %s\n", p);

    /* Demo B：removexattr */
    if (removexattr(path, key, 0) != 0) {
        perror("removexattr");
        return 1;
    }
    n = listxattr(path, names, sizeof(names), 0);
    printf("after remove, list bytes=%zd\n", n);
    return 0;
}
```

```bash
cc -o day43_demo day43_demo.c && ./day43_demo
```

（需 Darwin。）

---

## 做完打勾

- [ ] 找到 240 / 238  
- [ ] 能说 listxattr：namei → vn_listxattr → 名字列表  
- [ ] 能说 removexattr：copyinstr 名 + namei → vn_removexattr  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-43.md`

下一步：Day 44 → `chmod` / `chown`（#15 / #16）
