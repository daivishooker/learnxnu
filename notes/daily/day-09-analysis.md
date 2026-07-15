# 源码分析：Day 9（mkdir / rmdir / unlink）

基于 `xnu-12377.121.6`。主题：目录项的增删。

---

## 1. 今天在改什么？

Day 8 改的是进程「站哪」（`fd_cdir`）。  
今天改的是文件系统里的**名字 → vnode 映射**：

```
父目录 dvp
   ├─ "foo"  → 某个 vnode
   └─ "bar"  → …
```

`mkdir` 加一项；`unlink`/`rmdir` 去掉一项。

---

## 2. mkdir

```
mkdir (#136)
  → 计算 mode &= ~fd_cmask   // umask
  → mkdir1at(AT_FDCWD, path, va)
       NDINIT(CREATE, OP_MKDIR, LOCKPARENT)
       nameiat
       已存在 → EEXIST
       va_type = VDIR
       创建目录节点并链进父目录
```

要点：

1. **CREATE + LOCKPARENT**：创建类操作要锁住父目录。  
2. `WILLBEDIR` / compound mkdir：告诉 namei「将要变成目录」。  
3. 权限/真正落盘在 VFS 授权 + `VNOP_MKDIR`（或 compound）路径；今天跟到「父目录 + 创建」即可。

---

## 3. unlink

```
unlink (#10)
  → unlinkat_internal(AT_FDCWD, path, flags=0)
       namei 找到父目录 dvp + 目标 vp
       授权删除
       VNOP_REMOVE / 等价路径去掉目录项
```

语义提醒：

- 删的是**名字**；硬链接数 >1 时文件内容还在。  
- 已 open 的 fd 往往仍可用，直到最后一个引用关掉（与 Day 4/6 的引用计数直觉一致）。  
- `unlinkat` 若带 `AT_REMOVEDIR`，会转去 `rmdirat_internal`——说明「删目录」和「删普通名」在内部是分叉的。

---

## 4. rmdir

```
rmdir (#137)
  → rmdirat_internal(AT_FDCWD, path)
       确认是目录、通常要求空
       vn_rmdir(dvp, &vp, ...)
```

与 `unlink` 对比：专门处理目录语义（`.` / `..`、非空检查等）。用户态应 `rmdir` 删目录，而不是随便 `unlink`。

---

## 5. 三条链一张图

```
path ──namei──► 父目录 dvp (+ 可选目标 vp)
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     mkdir       unlink       rmdir
   创建子目录     去掉名字     去掉空目录名
```

---

## 6. 建议点开的文件

1. `syscalls.master` — 10 / 136 / 137  
2. `vfs_syscalls.c` — `mkdir` + `mkdir1at` 开头（`fd_cmask`、`EEXIST`）  
3. `vfs_syscalls.c` — `unlink` → `unlinkat_internal` 声明/入口  
4. `vfs_syscalls.c` — `rmdir` → `rmdirat_internal`  

验收：能说明「mkdir 加目录项；unlink 删名字；rmdir 删空目录」，且都相对 cwd/`AT_FDCWD` 解析路径。
