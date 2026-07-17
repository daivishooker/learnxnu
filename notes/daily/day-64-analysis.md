# 源码分析：Day 64（杂项五件套）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
revoke → namei 设备 → VNOP_REVOKE
acct   → suser → 设/清 acctp
gethostuuid → IOBSDGetPlatformUUID → copyout
minherit → mach_vm_inherit
swapon → ENOTSUP
```

---

## 2. 建议点开

1. `syscalls.master` — 56 / 51 / 142 / 250 / 85  
2. `vfs_syscalls.c` — `revoke`  
3. `kern_acct.c` — `acct`  
4. `sys_generic.c` — `gethostuuid`  
5. `kern_mman.c` — `minherit`  
6. `vm_unix.c` — `swapon` stub

验收：能各说一句主路径；Demo（minherit 或 skip）能跑。
