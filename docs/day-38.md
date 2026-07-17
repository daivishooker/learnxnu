# 第三十八天（Day 38）正文

学这两个：**`setattrlist` / `fgetattrlist`**  
源码：`xnu/` = **xnu-12377.121.6**

昨天用 `getattrlist`「按清单读属性」；今天补上**写**，以及**已打开 FD** 上的读。

生活类比：

1. `setattrlist`：按清单改标签（时间、标志等）——不是改文件内容  
2. `fgetattrlist`：手里已经握着文件（FD），再按清单问属性——省掉再走一遍路径查找

---

## 今天目标

1. 找到编号 **221 / 228**  
2. 理解 `setattrlist`：路径 → vnode → copyin 属性袋 → `vnode_setattr`  
3. 理解 `fgetattrlist`：FD → vnode → 与 `getattrlist` 同套打包逻辑  
4. 能对比：路径版读 / FD 版读 / 路径版写；可设属性受 `ATTR_*_SETMASK` 限制  

笔记：[`notes/daily/day-38.md`](../notes/daily/day-38.md)  
分析：[`notes/daily/day-38-analysis.md`](../notes/daily/day-38-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| setattrlist | **221** | 按 attrlist 写路径对象的属性 |
| fgetattrlist | **228** | 按 attrlist 读 **FD** 对应对象的属性 |

（同族还有 `fsetattrlist` #229、`setattrlistat` #524——今天略。）

---

## 1. setattrlist（#221）——按需写属性

[`vfs_attrlist.c`](../xnu/bsd/vfs/vfs_attrlist.c)：

```c
setattrlist(path, alist, attributeBuffer, bufferSize, options) {
    namei(path) → vnode
    setattrlist_internal:
      copyin(attrlist)          // 要改哪些位
      校验 SETMASK（不可设的位 → EINVAL）
      copyin(attributeBuffer)   // 新值（无 getattr 那种 length 头）
      填 vnode_attr → vnode_setattr / VNOP_SETATTR
}
```

要点：

- 和 `getattrlist` 同一套「点菜」位图，但只允许 **可写子集**（`ATTR_CMN_SETMASK` 等）  
- 目录的 `dirattr` 在表里几乎都不可设（`ATTR_DIR_SETMASK == 0`）  
- 常见可写：`ATTR_CMN_MODTIME` / `CRTIME`、标志、FinderInfo 等  
- **改的是元数据，不是 `write` 文件内容**  

---

## 2. fgetattrlist（#228）——FD 版读属性

同文件：

```c
fgetattrlist(fd, alist, attributeBuffer, bufferSize, options) {
    fp_get_ftype(..., DTYPE_VNODE) → vnode
    copyin(attrlist)
    getattrlist_internal(vp, ...)   // 与路径版 getattrlist 汇合
}
```

要点：

- 语义 ≈ `getattrlist`，差别只在**怎么找到 vnode**：路径 `namei` vs FD  
- 已 `open` 的文件不必再拼路径；也避开路径上的竞态  
- 返回缓冲仍带 `uint32_t length` 头（与 Day 37 读侧相同）  

对照：

| | 找对象 | 读/写 |
|--|--------|------|
| getattrlist | 路径 | 读 |
| fgetattrlist | FD | 读 |
| setattrlist | 路径 | 写 |

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/attr.h>
#include <time.h>
#include <unistd.h>

/* Demo A：fgetattrlist — 已打开 FD 上取数据长度 */
static void show_size_fd(int fd, const char *label) {
    struct attrlist al;
    memset(&al, 0, sizeof(al));
    al.bitmapcount = ATTR_BIT_MAP_COUNT;
    al.fileattr = ATTR_FILE_DATALENGTH;

    struct {
        uint32_t length;
        off_t    data_length;
    } __attribute__((aligned(4), packed)) buf;

    if (fgetattrlist(fd, &al, &buf, sizeof(buf), 0) != 0) {
        perror("fgetattrlist");
        return;
    }
    printf("%s data_length=%lld\n", label, (long long)buf.data_length);
}

/* Demo B：setattrlist — 改修改时间（可写 common 属性） */
static void bump_mtime(const char *path) {
    struct attrlist al;
    struct timespec ts;

    memset(&al, 0, sizeof(al));
    al.bitmapcount = ATTR_BIT_MAP_COUNT;
    al.commonattr = ATTR_CMN_MODTIME;

    clock_gettime(CLOCK_REALTIME, &ts);
    /* setattr 缓冲：无 length 头，按点菜顺序直接放值 */
    if (setattrlist(path, &al, &ts, sizeof(ts), 0) != 0) {
        perror("setattrlist");
        return;
    }
    printf("setattrlist MODTIME ok: %s\n", path);
}

int main(void) {
    const char *path = "/tmp/day38_demo.txt";
    int fd = open(path, O_CREAT | O_RDWR | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    (void)write(fd, "hello\n", 6);

    show_size_fd(fd, path);
    close(fd);

    bump_mtime(path);
    return 0;
}
```

```bash
cc -o day38_demo day38_demo.c && ./day38_demo
```

（需在 Darwin/macOS 上跑；Linux 无此 API。）

---

## 做完打勾

- [ ] 找到 221 / 228  
- [ ] 能说 setattrlist：namei → SETMASK 校验 → setattr  
- [ ] 能说 fgetattrlist：FD → 与 getattrlist 同内部打包  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-38.md`

下一步：Day 39 → [`exchangedata` / `copyfile`](day-39.md)（#223 / #227）
