# 源码分析：Day 41（searchfs / fsgetpath）

基于 `xnu-12377.121.6`。卷内搜索与按 ID 取路径。

---

## 1. 心智模型

```text
searchfs(path, fssearchblock, state):
  copyin 条件/返回格式/状态 → 起点 vnode → VNOP_SEARCHFS → copyout 匹配

fsgetpath(buf, fsid, objid):
  vnode_getfromid → build_path → copyout 路径字符串
```

---

## 2. searchfs

[`vfs_syscalls.c`](../../xnu/bsd/vfs/vfs_syscalls.c)：

```
#if CONFIG_SEARCHFS
  copyin searchblock / params / attrlist / state
  namei(path) → vp（union mount 可下钻层）
  VNOP_SEARCHFS(...)
  copyout nummatches / state / 结果缓冲
#else
  ENOTSUP
#endif
```

结构见 `sys/attr.h`：`fssearchblock`、`searchstate`。

---

## 3. fsgetpath

同文件：

```
fsgetpath → fsgetpath_extended(options=0)
  copyin fsid
  fsgetpath_internal(fsid.val[0], objid)
    vnode_getfromid
    build_path（可 EAGAIN 重试）
  copyout；retval = 长度
```

`fsgetpath_ext` 可带 `FSOPT_NOFIRMLINKPATH` 等。

---

## 4. 建议点开

1. `syscalls.master` — 225 / 427  
2. `vfs_syscalls.c` — `searchfs` / `fsgetpath_internal`  
3. `sys/attr.h` — `fssearchblock`  
4. `sys/fsgetpath.h` — 用户声明  

验收：能说两条链；Demo 至少跑通 `fsgetpath`。
