# 第五十八天（Day 58）正文

学这六个：**`fgetxattr` / `fsetxattr` / `flistxattr` / `fremovexattr` / `fsetattrlist` / `getdirentriesattr`**  
源码：`xnu/` = **xnu-12377.121.6**

节奏：每天 5–10 个。今天扫尾 **FD 侧属性**：Day 42–43 的 xattr FD 版，加上 `fsetattrlist` 与较老的目录批量属性 `getdirentriesattr`。

生活类比：

1. `f*xattr`：手里已经捏着文件（FD），直接贴/读/列/撕便签——不再重新找门牌  
2. `fsetattrlist`：手里捏着对象，按菜单改属性（Day 38 的 FD 版）  
3. `getdirentriesattr`：进目录一次抄多名+属性（`getattrlistbulk` 的前辈）  

---

## 今天目标

1. 找到编号 **235 / 237 / 241 / 239 / 229 / 222**  
2. 能说：`f*xattr` = `file_vnode(fd)` → 与路径版同一套 `vn_*xattr`  
3. 能说：`fsetattrlist` → `setattrlist_internal`；`getdirentriesattr` → `VNOP_READDIRATTR`  
4. 能对比：`getdirentriesattr` vs Day 52 `getattrlistbulk`  

笔记：[`notes/daily/day-58.md`](../notes/daily/day-58.md)  
分析：[`notes/daily/day-58-analysis.md`](../notes/daily/day-58-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| fgetxattr | **235** | 按 FD 读扩展属性 |
| fsetxattr | **237** | 按 FD 写扩展属性 |
| flistxattr | **241** | 按 FD 列扩展属性名 |
| fremovexattr | **239** | 按 FD 删扩展属性 |
| fsetattrlist | **229** | 按 FD 写 attrlist 属性 |
| getdirentriesattr | **222** | 目录 FD 批量读「名字+属性」 |

---

## 1–4. f*xattr 四件套

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
fgetxattr / fsetxattr / flistxattr / fremovexattr:
  // 路径版不允许的 NOFOLLOW / RESOLVE_BENEATH 在 FD 版直接 EINVAL
  // （已经握着 vnode，没有「再解析路径」）
  file_vnode(fd) → vnode_getwithref(vp)
  copyinstr(attrname)   // list 除外
  → vn_getxattr / vn_setxattr / vn_listxattr / vn_removexattr
```

对照路径版（Day 42–43）：

| 路径 | FD | 内核干活 |
|------|-----|----------|
| getxattr #234 | fgetxattr #235 | `vn_getxattr` |
| setxattr #236 | fsetxattr #237 | `vn_setxattr` |
| listxattr #240 | flistxattr #241 | `vn_listxattr` |
| removexattr #238 | fremovexattr #239 | `vn_removexattr` |

要点：

- FD 版**跳过 namei**，无路径竞态；对象就是打开时那个 vnode  
- `XATTR_NOFOLLOW` 等「解析类」options 在 `f*` 上无意义 → `EINVAL`  
- 完整 xattr 工具箱：路径四件套 + FD 四件套  

---

## 5. fsetattrlist（#229）

[`vfs_attrlist.c`](../xnu/bsd/vfs/vfs_attrlist.c)：

```c
fsetattrlist(fd, alist, buffer, size, options) {
    file_vnode(fd) → vp
    → setattrlist_internal(vp, ...)   // 与 setattrlist / setattrlistat 同核
}
```

对照：`setattrlist`（路径）/ `setattrlistat`（dirfd+路径）/ `fsetattrlist`（已打开 FD）。读侧还有 `fgetattrlist`（Day 38）。

---

## 6. getdirentriesattr（#222）

```c
getdirentriesattr(fd, alist, buffer, buffersize, count, basep, newstate, options) {
    fp_getfvp(fd) → 须为目录且可读
    copyin(attrlist) + copyin(count)
    authorize LIST_DIRECTORY（要更多字段则加 SEARCH）
    VNOP_READDIRATTR(...)
    推进 fg_offset；copyout count / eofflag / newstate
}
```

要点：

- 老接口：列目录时**顺带**按 attrlist 打包属性  
- 现代更常见 **`getattrlistbulk` #461**（Day 52）；两者目标相近，VNOP 不同  
- 必须是目录 FD；用目录偏移做续读  

属性 API 地图（扫尾后）：

| 粒度 | 路径 | dirfd+路径 | FD |
|------|------|------------|-----|
| xattr 单键 | get/set/list/remove | — | f* 四件套（今天） |
| attrlist | getattrlist / setattrlist | *at（Day 57） | fgetattrlist / **fsetattrlist** |
| 目录批量 | — | — | getdirentriesattr / getattrlistbulk |

---

## 用户层 Demo

> `fsetattrlist` / `getdirentriesattr` 偏 Darwin。Demo 覆盖可移植的 `f*xattr` 四件套。

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/xattr.h>
#include <unistd.h>

int main(void) {
    const char *path = "/tmp/day58_xattr.txt";
    const char *key = "user.day58";
    const char *val = "hello";
    char buf[64];
    char names[256];
    ssize_t n;
    int fd;

    (void)unlink(path);
    fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }

    /* set */
    if (fsetxattr(fd, key, val, strlen(val), 0) != 0) {
        perror("fsetxattr");
        close(fd);
        return 1;
    }
    printf("fsetxattr ok\n");

    /* get */
    n = fgetxattr(fd, key, buf, sizeof(buf) - 1);
    if (n < 0) { perror("fgetxattr"); close(fd); return 1; }
    buf[n] = '\0';
    printf("fgetxattr ok value=%s\n", buf);

    /* list */
    n = flistxattr(fd, names, sizeof(names));
    if (n < 0) { perror("flistxattr"); close(fd); return 1; }
    printf("flistxattr ok bytes=%zd\n", n);

    /* remove */
    if (fremovexattr(fd, key) != 0) {
        perror("fremovexattr");
        close(fd);
        return 1;
    }
    printf("fremovexattr ok\n");

    close(fd);
    (void)unlink(path);
    return 0;
}
```

```bash
cc -o day58_demo day58_demo.c && ./day58_demo
```

> Linux 上 `fsetxattr` 原型无 `position`（Darwin 有）；上例用 Linux 常见 5 参形式。Darwin 需加 `position=0` 与 `options`。

---

## 做完打勾

- [ ] 找到六个编号  
- [ ] 能说 f*xattr 跳过 namei、汇入 vn_*xattr  
- [ ] 能说 getdirentriesattr ≈ 老版目录批量属性  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-58.md`

下一步：Day 59 → `sendfile` / `fdatasync` / `sendto` / `recvfrom` / `getdirentries` / `access_extended`
