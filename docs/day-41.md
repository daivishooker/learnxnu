# 第四十一天（Day 41）正文

学这两个：**`searchfs` / `fsgetpath`**  
源码：`xnu/` = **xnu-12377.121.6**

今天两条「按条件/按 ID 找东西」的 Darwin VFS 路径：目录树里搜，以及用卷 ID + 对象 ID 反查路径。

生活类比：

1. `searchfs`：给文件系统一本检索单（名字、时间等），让它自己翻目录树找匹配项  
2. `fsgetpath`：手里只有「哪块盘 + 哪个文件编号」，请内核拼出完整路径字符串

---

## 今天目标

1. 找到编号 **225 / 427**  
2. 理解 `searchfs`：路径 → vnode → copyin 搜索块 → `VNOP_SEARCHFS`  
3. 理解 `fsgetpath`：`fsid` + `objid` → `vnode_getfromid` → `build_path`  
4. 能对比：条件搜索 vs ID 反查路径；二者都依赖 FS/VFS 能力  

笔记：[`notes/daily/day-41.md`](../notes/daily/day-41.md)  
分析：[`notes/daily/day-41-analysis.md`](../notes/daily/day-41-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| searchfs | **225** | 在路径所在卷上按条件搜索文件系统对象 |
| fsgetpath | **427** | 用 `fsid` + `objid` 取绝对路径 |

（还有 `fsgetpath_ext` #217，多 `options`；今天略。）

---

## 1. searchfs（#225）——卷内条件搜索

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)（需 `CONFIG_SEARCHFS`，否则直接 `ENOTSUP`）：

```c
searchfs(path, searchblock, nummatches, scriptcode, options, state) {
    copyin(fssearchblock)     // 条件、返回 attrlist、缓冲、上限、超时
    copyin(searchparams / returnattrs / searchstate)
    namei(path) → 起始 vnode（常为卷根或目录）
    VNOP_SEARCHFS(...)        // 文件系统自己搜
    copyout 匹配结果与 state  // 可续搜（EAGAIN 等）
}
```

要点：

- 参数里的 `struct fssearchblock` + `struct attrlist searchattrs`：用属性位图描述「搜什么 / 返回什么」  
- `searchstate` 保存进度，可多次调用继续搜  
- **不是**用户态自己 `readdir` 递归；是 FS 的 catalog/索引能力（支持因卷而异）  
- 很多场景上层已改用 Spotlight 等；学内核时跟到 `VNOP_SEARCHFS` 即可  

---

## 2. fsgetpath（#427）——ID → 路径

同文件：

```c
fsgetpath(buf, bufsize, fsid, objid) {
    fsgetpath_extended(..., options=0)
      copyin(fsid)
      fsgetpath_internal:
        vnode_getfromid(fsid.val[0], objid) → vp
        build_path(vp, ...) → 绝对路径
        copyout；返回长度
}
```

要点：

- 输入是 **卷标识 + 对象 ID**（不是路径字符串）  
- 典型用法：先 `stat`/`getattrlist` 拿到 `f_fsid` 与 file id，再反查路径  
- master 注释写 private / File Manager SPI；现代 SDK 有公开 `fsgetpath(3)`（10.13+）  
- 路径构建可能遇竞态 → 内部可 `EAGAIN` 重试  

对照：

| | 你有什么 | 你要什么 |
|--|----------|----------|
| searchfs | 条件 + 起点路径 | 一批匹配对象（属性袋） |
| fsgetpath | fsid + objid | 一条绝对路径 |

---

## 用户层 Demo

```c
#include <stdio.h>
#include <string.h>
#include <sys/attr.h>
#include <sys/fsgetpath.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <unistd.h>

/* Demo A：fsgetpath — 用卷 fsid + inode 反查路径 */
static void demo_fsgetpath(const char *path) {
    struct statfs sfs;
    struct stat st;
    char buf[1024];
    ssize_t n;

    if (statfs(path, &sfs) != 0) { perror("statfs"); return; }
    if (stat(path, &st) != 0) { perror("stat"); return; }

    n = fsgetpath(buf, sizeof(buf), &sfs.f_fsid, (uint64_t)st.st_ino);
    if (n < 0) {
        perror("fsgetpath");
        return;
    }
    printf("fsgetpath(%s) => %.*s\n", path, (int)n, buf);
}

/* Demo B：searchfs — 仅展示入口；许多卷会 ENOTSUP / 需复杂参数 */
static void demo_searchfs_probe(const char *path) {
    struct fssearchblock sb;
    struct attrlist ret, search;
    struct searchstate state;
    uint32_t num = 0;
    char retbuf[256];

    memset(&sb, 0, sizeof(sb));
    memset(&ret, 0, sizeof(ret));
    memset(&search, 0, sizeof(search));
    memset(&state, 0, sizeof(state));

    ret.bitmapcount = ATTR_BIT_MAP_COUNT;
    ret.commonattr = ATTR_CMN_NAME;
    search.bitmapcount = ATTR_BIT_MAP_COUNT;

    sb.returnattrs = &ret;
    sb.returnbuffer = retbuf;
    sb.returnbuffersize = sizeof(retbuf);
    sb.maxmatches = 1;
    sb.searchattrs = search;

    /* 最小探测：不填真实搜索条件，预期失败或 ENOTSUP，用来确认 syscall 存在 */
    if (searchfs(path, &sb, &num, 0, 0, &state) != 0) {
        perror("searchfs (probe; often ENOTSUP/EINVAL)");
        return;
    }
    printf("searchfs matches=%u\n", num);
}

int main(void) {
    demo_fsgetpath("/tmp");
    demo_searchfs_probe("/");
    return 0;
}
```

```bash
cc -o day41_demo day41_demo.c && ./day41_demo
```

（需 Darwin。重点看 `fsgetpath`；`searchfs` 探测失败也算了解入口。）

---

## 做完打勾

- [ ] 找到 225 / 427  
- [ ] 能说 searchfs：copyin 搜索块 → VNOP_SEARCHFS  
- [ ] 能说 fsgetpath：fsid+objid → vnode → build_path  
- [ ] 跑通 Demo（至少 fsgetpath）  
- [ ] 填好 `notes/daily/day-41.md`

下一步：Day 42 → `getxattr` / `setxattr`（扩展属性）
