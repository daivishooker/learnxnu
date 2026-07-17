# 第三十七天（Day 37）正文

学这两个：**`getdirentries64` / `getattrlist`**  
源码：`xnu/` = **xnu-12377.121.6**

今天看目录里「有哪些名字」，以及 Darwin 特色的「按需取文件属性」。

生活类比：

1. `getdirentries64`：翻目录抽屉，一页一页抄目录项（名字等）  
2. `getattrlist`：按清单问「这个文件我关心的那几项属性」

---

## 今天目标

1. 找到编号 **344 / 220**  
2. 理解 `getdirentries64`：目录 FD → `vnode_readdir64` / `VNOP_READDIR`  
3. 理解 `getattrlist`：路径 + `attrlist` 请求 → 填属性缓冲  
4. 能对比：枚举目录项 vs 取单个对象属性；与 Day 7 `stat` 对照  

笔记：[`notes/daily/day-37.md`](../notes/daily/day-37.md)  
分析：[`notes/daily/day-37-analysis.md`](../notes/daily/day-37-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| getdirentries64 | **344** | 从目录 FD 读一批目录项 |
| getattrlist | **220** | 按 attrlist 取路径对应对象的属性 |

---

## 1. getdirentries64（#344）——读目录项

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
getdirentries64(fd, buf, bufsize, position) {
    getdirentries_common(..., VNODE_READDIR_EXTENDED)
      fp → vnode（必须是目录）
      vnode_readdir64 / VNOP_READDIR → 填用户缓冲
      更新目录偏移；copyout 新 position
    返回读到的字节数
}
```

要点：

- 参数是**已打开的目录 FD**（不是路径）  
- 缓冲里是 `direntry` 一类变长记录（名字 + ino 等）  
- 可多次调用推进；`position` 记住读到哪  
- 用户常用 `readdir(3)`，库底层常走到这类接口  

---

## 2. getattrlist（#220）——按需取属性

[`vfs_attrlist.c`](../xnu/bsd/vfs/vfs_attrlist.c)：

```c
getattrlist(path, alist, attributeBuffer, bufferSize, options) {
    copyin(attrlist)          // 用户声明要哪些属性
    getattrlistat_internal → namei 路径 → vnode
      按请求收集属性（常经 vnode_getattr 等）
      打包进 attributeBuffer → copyout
}
```

要点：

- Darwin / macOS 特色；比 `stat` 更灵活（可选打包多种属性）  
- `struct attrlist` 用位图说明要 COMMON / VOLUME / FILE… 哪些字段  
- 还有 `fgetattrlist`（FD）、`getattrlistbulk`（目录批量）——今天略  

和 Day 7：`stat` 固定结构；`getattrlist` 是「点菜式」属性袋。

---

## 用户层 Demo

```c
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/attr.h>
#include <sys/mount.h>
#include <unistd.h>

/* Demo A：列目录（libc readdir；Darwin 下底层常接 getdirentries*） */
static void list_dir(const char *path) {
    DIR *d = opendir(path);
    if (!d) { perror("opendir"); return; }
    struct dirent *e;
    while ((e = readdir(d)) != NULL)
        printf("  %s\n", e->d_name);
    closedir(d);
}

/* Demo B：getattrlist 取文件大小（ATTR_FILE_ALLOCSIZE 等） */
static void show_size(const char *path) {
    struct attrlist al;
    memset(&al, 0, sizeof(al));
    al.bitmapcount = ATTR_BIT_MAP_COUNT;
    al.fileattr = ATTR_FILE_DATALENGTH;

    struct {
        uint32_t length;
        off_t    data_length;
    } __attribute__((aligned(4), packed)) buf;

    if (getattrlist(path, &al, &buf, sizeof(buf), 0) != 0) {
        perror("getattrlist");
        return;
    }
    printf("%s data_length=%lld\n", path, (long long)buf.data_length);
}

int main(void) {
    printf("entries in /tmp:\n");
    list_dir("/tmp");
    show_size("/tmp");
    return 0;
}
```

```bash
cc -o day37_demo day37_demo.c && ./day37_demo
```

（若只想直接打 `getdirentries64`，可 `#include <sys/syscall.h>` 后对目录 FD 调用；日常用 `readdir` 即可理解语义。）

---

## 做完打勾

- [ ] 找到 344 / 220  
- [ ] 能说 getdirentries64：目录 FD → READDIR  
- [ ] 能说 getattrlist：attrlist 点菜 + 属性袋  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-37.md`

下一步：Day 38 → [`setattrlist` / `fgetattrlist`](day-38.md)——写属性与按 FD 查属性。
