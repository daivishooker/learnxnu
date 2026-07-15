# 第七天（Day 7）正文

学这三个：**`stat64` / `fstat64` / `lstat64`**  
源码：`xnu/` = **xnu-12377.121.6**

第 1 周收尾：拿文件**元数据**（大小、模式、inode…），并分清三条入口——**路径跟随链接 / 路径不跟随 / 已有 fd**。

---

## 今天目标

1. 找到编号 **338 / 339 / 340**  
2. 知道三者最终都落到 `vn_stat*`，差别只在「怎么找到 vnode」  
3. 能说清 `stat64` vs `lstat64`（是否跟随最后一级符号链接）  
4. 能说清 `fstat64` 为何不解析路径

笔记：[`notes/daily/day-07.md`](../notes/daily/day-07.md)  
分析：[`notes/daily/day-07-analysis.md`](../notes/daily/day-07-analysis.md)

---

## 总表

| 名字 | # | 输入 | 跟随 symlink？ |
|------|---|------|----------------|
| stat64 | **338** | 路径 | 是（FOLLOW） |
| fstat64 | **339** | fd | 不适用（已有对象） |
| lstat64 | **340** | 路径 | 否（`AT_SYMLINK_NOFOLLOW`） |

---

## 1. stat64（#338）

[`vfs_syscalls.c`](../xnu/bsd/vfs/vfs_syscalls.c)：

```c
stat64(...) {
    return fstatat_internal(..., path, ub, ..., isstat64=1, ..., AT_FDCWD, flag=0);
}
```

`flag=0` → namei 用 **FOLLOW** → 若路径末尾是符号链接，stat 的是**目标**。

---

## 2. lstat64（#340）

```c
lstat64(...) {
    return fstatat_internal(..., path, ub, ..., isstat64=1, ..., AT_FDCWD,
                            AT_SYMLINK_NOFOLLOW);
}
```

同一条内部函数，只多了 **NOFOLLOW**：返回的是**链接自身**的元数据（`S_IFLNK` 等）。

---

## 3. fstat64（#339）

[`kern_descrip.c`](../xnu/bsd/kern/kern_descrip.c)：

```c
sys_fstat64(...) {
    return fstat(p, fd, ub, 0, 0, isstat64=1);
}
```

`fstat`：

1. `fp_lookup` 取 `fileproc`  
2. 按类型分支：`DTYPE_VNODE` → `vn_stat` / `vn_stat_noauth`；socket/pipe/… 各有 `*_stat`  
3. `copyout` 用户 `struct stat64`

**不走 namei**，所以没有「跟不跟随链接」问题——你持有的 fd 已经指向打开时的对象。

---

## 今日对比

| | 找 vnode | 用户缓冲 |
|--|----------|----------|
| stat64 | 路径 + FOLLOW | `stat64` |
| lstat64 | 路径 + NOFOLLOW | `stat64` |
| fstat64 | fd → fileproc | `stat64` |

共同点：都不分配新 FD；成功时数据在用户 `ub` 里，syscall 返回值是 0/errno。

---

## 第 1 周验收（今天顺带过一遍）

- [ ] 能讲 `open → read → close`  
- [ ] 知道 `getpid` 极简 vs `open` 有路径/FD  
- [ ] 知道 dup 共享 `fileglob`/`fg_offset`  
- [ ] 今天：stat 三兄弟的差别说得清

下一步：第 2 周 Day 8 → `chdir` / `fchdir` /getcwd 相关

---

## 做完打勾

- [ ] 找到 338 / 339 / 340  
- [ ] 看过 `stat64`/`lstat64` 都进 `fstatat_internal`  
- [ ] 看过 `sys_fstat64` → `fstat`  
- [ ] 填好 `notes/daily/day-07.md`
