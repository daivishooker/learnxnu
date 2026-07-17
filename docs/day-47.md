# 第四十七天（Day 47）正文

学这两个：**`pathconf` / `fpathconf`**  
源码：`xnu/` = **xnu-12377.121.6**

今天不改文件，只**问配置**：对某个路径/FD，「名字最长多少」「链路数上限」等。

生活类比：

1. `pathconf`：指着某条路问「这条路上的规矩是啥」  
2. `fpathconf`：指着已打开的 FD 问同一类问题（内部仍会按类型分流）

---

## 今天目标

1. 找到编号 **191 / 192**（FD 版入口名是 `sys_fpathconf`）  
2. 理解 `pathconf`：`namei` → `vn_pathconf` → 常进 `VNOP_PATHCONF`  
3. 理解 `fpathconf`：`fp_lookup` 后按 `DTYPE_*` 分流  
4. 能举例：`_PC_NAME_MAX`、`_PC_LINK_MAX`、`_PC_PIPE_BUF`  

笔记：[`notes/daily/day-47.md`](../notes/daily/day-47.md)  
分析：[`notes/daily/day-47-analysis.md`](../notes/daily/day-47-analysis.md)

---

## 总表

| 名字 | # | 作用 |
|------|---|------|
| pathconf | **191** | 按路径查询 pathconf 名字对应的限制/能力 |
| fpathconf（`sys_fpathconf`） | **192** | 按 FD 查询同上 |

---

## 1. pathconf（#191）——路径版

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
pathconf(path, name) {
    namei(path) → vp
    vn_pathconf(vp, name, &retval)
      部分名字内核直接答（如部分 POSIX 常量）
      其余 → VNOP_PATHCONF（问文件系统）
}
```

常见 `name`（见 `unistd.h`）：

| 常量 | 大致问什么 |
|------|------------|
| `_PC_NAME_MAX` | 单个文件名最长 |
| `_PC_PATH_MAX` | 路径最长（若支持） |
| `_PC_LINK_MAX` | 硬链接数上限 |
| `_PC_PIPE_BUF` | pipe 原子写大小 |

---

## 2. fpathconf（#192）——FD 版，再次分流

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c) 里叫 **`sys_fpathconf`**：

```c
sys_fpathconf(fd, name) {
    fp_lookup(fd)
    switch (fp->f_type) {
      DTYPE_SOCKET / DTYPE_PIPE:
        仅允许 _PC_PIPE_BUF → 返回 PIPE_BUF
      DTYPE_VNODE:
        vn_pathconf(vp, name, ...)
      default:
        EINVAL
    }
}
```

要点：

- 又是 **fileglob / file type 分流**（和 `ftruncate`、`futimes` 同一心智模型）  
- socket/pipe 几乎只认 `_PC_PIPE_BUF`  
- vnode 才去问文件系统的 `VNOP_PATHCONF`  
- 返回值经 syscall `retval` 回用户；失败则 `-1` + `errno`（libc 包装）  

---

## 用户层 Demo

```c
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    long v;
    int fd;

    /* Demo A：pathconf — 问 /tmp 上文件名最长 */
    v = pathconf("/tmp", _PC_NAME_MAX);
    if (v < 0) perror("pathconf NAME_MAX");
    else printf("/tmp _PC_NAME_MAX = %ld\n", v);

    v = pathconf("/tmp", _PC_LINK_MAX);
    if (v < 0) perror("pathconf LINK_MAX");
    else printf("/tmp _PC_LINK_MAX = %ld\n", v);

    /* Demo B：fpathconf — 对打开的目录 FD */
    fd = open("/tmp", O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    v = fpathconf(fd, _PC_NAME_MAX);
    if (v < 0) perror("fpathconf");
    else printf("fd(/tmp) _PC_NAME_MAX = %ld\n", v);
    close(fd);
    return 0;
}
```

```bash
cc -o day47_demo day47_demo.c && ./day47_demo
```

---

## 做完打勾

- [ ] 找到 191 / 192  
- [ ] 能说 pathconf：namei → vn_pathconf  
- [ ] 能说 fpathconf：按 DTYPE 分流  
- [ ] 跑通 Demo  
- [ ] 填好 `notes/daily/day-47.md`

下一步：Day 48 → [`readlink` / `readlinkat`](day-48.md)（#58 / #473）
