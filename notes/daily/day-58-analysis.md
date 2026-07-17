# 源码分析：Day 58（FD/目录侧属性扫尾）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
f*xattr(fd, ...):
  file_vnode → vn_*xattr → VNOP_*XATTR

fsetattrlist(fd, ...):
  file_vnode → setattrlist_internal

getdirentriesattr(dirfd, ...):
  fp_getfvp → 须 VDIR
  VNOP_READDIRATTR → 更新目录偏移
```

---

## 2. 与路径版对照

| 路径 | FD |
|------|-----|
| get/set/list/removexattr | fget/fset/flist/fremovexattr |
| setattrlist / setattrlistat | fsetattrlist |
| （列目录属性） | getdirentriesattr / getattrlistbulk |

---

## 3. 建议点开

1. `syscalls.master` — 235 / 237 / 241 / 239 / 229 / 222  
2. `vfs_syscalls.c` — `fgetxattr` 等、`getdirentriesattr`  
3. `vfs_attrlist.c` — `fsetattrlist`  
4. 对照 Day 42–43、38、52

验收：能画出 xattr/attrlist/目录批量三张地图；Demo 能跑。
