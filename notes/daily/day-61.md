# Day 61 — getgroups / setgroups / initgroups / getlogin / setlogin / chroot

> **正文：** [docs/day-61.md](../../docs/day-61.md)  
> **分析：** [day-61-analysis.md](day-61-analysis.md)

## getgroups / setgroups / initgroups（#79/#80/#243）
- 入口：读 `cr_groups`；写侧 `setgroups1` → `kauth_cred_model_setgroups`
- 一句话：补充组列表；改要特权；initgroups 带 gmuid

## getlogin / setlogin（#49/#50）
- 入口：session `s_login`；set 要 `proc_suser`
- 一句话：会话登录名字符串，不是 uid

## chroot（#61）
- 入口：特权 + namei → 设 `fd_rdir`
- 一句话：改进程根目录 vnode

## 今日对比
- 共同点：身份/命名空间相关，多需特权才能改
- 最大差异：凭证补充组 vs 会话字符串 vs VFS 根
