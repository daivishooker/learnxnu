# 源码分析：Day 61（补充组 / login / chroot）

基于 `xnu-12377.121.6`。

---

## 1. 心智模型

```text
getgroups → cr_groups[]
setgroups / initgroups → setgroups1 → setgroups_internal（特权）

getlogin / setlogin → session.s_login

chroot → suser + namei → p_fd.fd_rdir
```

---

## 2. initgroups vs setgroups

| | gmuid | 意图 |
|--|-------|------|
| initgroups | 调用方传入 | 参与扩展组解析（登录正路） |
| setgroups | `KAUTH_UID_NONE` | POSIX 兼容；退出 memberd 参与 |

---

## 3. 建议点开

1. `syscalls.master` — 79 / 80 / 243 / 49 / 50 / 61  
2. `kern_prot.c` — `getgroups` / `setgroups1` / `getlogin` / `setlogin`  
3. `vfs_syscalls.c` — `chroot`  
4. 对照 Day 60、Day 8

验收：能区分补充组、login 名、chroot 根；Demo 能跑。
