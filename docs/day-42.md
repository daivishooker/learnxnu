# 第四十二天（Day 42）正文

学这两个：**`getxattr` / `setxattr`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天是按条件/按 ID 找对象；今天给文件挂「便签」——**扩展属性（xattr）**：名字 → 一段字节，不是文件主内容。

生活类比：

1. `setxattr`：在文件外壳上贴一张便签（名字 + 内容）  
2. `getxattr`：按便签名字把内容读回来  

（Finder 信息、隔离属性 `com.apple.quarantine`、资源叉等，很多都走这条线。）

---

## 今天目标

1. 找到编号 **234 / 236**  
2. 理解 `getxattr`：路径 → `vn_getxattr` → `VNOP_GETXATTR`  
3. 理解 `setxattr`：路径 → `vn_setxattr` → `VNOP_SETXATTR`  
4. 能对比：xattr vs Day 37/38 的 `getattrlist`（属性袋）；与 `stat` 固定字段对照  

笔记：[`notes/daily/day-42.md`](../notes/daily/day-42.md)  
分析：[`notes/daily/day-42-analysis.md`](../notes/daily/day-42-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getxattr | **234** | 按名字读路径对象的扩展属性 |
| setxattr | **236** | 按名字写路径对象的扩展属性 |

（同族：`fgetxattr`/`fsetxattr`、`listxattr`/`removexattr`——明天预告后两者。）

---

## 1. getxattr（#234）——读扩展属性

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
getxattr(path, attrname, value, size, position, options) {
    namei(path) → vp
    copyinstr(attrname)
    可选：构造 UIO 指向用户 value 缓冲
    vn_getxattr → VNOP_GETXATTR（失败可走 default_getxattr）
    返回读到的字节数；value==NULL 时常只问长度
}
```

`vn_getxattr`（[`vfs_xattr.c`](../xnu/bsd/vfs/vfs_xattr.c)）还会做：名字校验、读扩展属性鉴权、MAC 检查。

---

## 2. setxattr（#236）——写扩展属性

```c
setxattr(path, attrname, value, size, position, options) {
    copyinstr(attrname)
    namei(path) → vp
    UIO_WRITE 包用户缓冲
    vn_setxattr → VNOP_SETXATTR
    （成功可发 FSE_XATTR_MODIFIED）
}
```

要点：

- `options`：`XATTR_CREATE`（已存在则失败）、`XATTR_REPLACE`（不存在则失败）、`XATTR_NOFOLLOW` 等  
- 普通 xattr 的 `position` 须为 0；资源叉例外  
- 和 `getattrlist` 不同：xattr 是**任意命名的键值**；attrlist 是内核定义好的属性位图  

---

## 用户层 Demo

```c
#include <stdio.h>
#include <string.h>
#include <sys/xattr.h>
#include <fcntl.h>
#include <unistd.h>

int main(void) {
    const char *path = "/tmp/day42_xattr.txt";
    const char *key = "user.day42.note";
    const char *val = "hello-xattr";
    char buf[64];
    ssize_t n;

    int fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    (void)write(fd, "body\n", 5);
    close(fd);

    /* Demo A：setxattr */
    if (setxattr(path, key, val, strlen(val), 0, 0) != 0) {
        perror("setxattr");
        return 1;
    }

    /* Demo B：getxattr */
    n = getxattr(path, key, buf, sizeof(buf) - 1, 0, 0);
    if (n < 0) {
        perror("getxattr");
        return 1;
    }
    buf[n] = '\0';
    printf("%s = %s\n", key, buf);
    return 0;
}
```

```bash
cc -o day42_demo day42_demo.c && ./day42_demo
```

（需 Darwin；也可用 `xattr -l /tmp/day42_xattr.txt` 对照。）

---

## 做完打勾

- [ ] 找到 234 / 236  
- [ ] 能说 getxattr：namei → vn_getxattr → VNOP_GETXATTR  
- [ ] 能说 setxattr：namei → vn_setxattr → VNOP_SETXATTR  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-42.md`

下一步：Day 43 → [`listxattr` / `removexattr`](day-43.md)（#240 / #238）
