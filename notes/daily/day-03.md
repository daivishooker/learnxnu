# Day 03 — issetugid / getdtablesize

> **正文：** [docs/day-03.md](../../docs/day-03.md)  
> **分析：** [day-03-analysis.md](day-03-analysis.md)

## issetugid (#327)
- handler：`kern_prot.c` → `issetugid` → `proc_issetugid`
- 读：`p->p_flag & P_SUGID`
- 返回：0 未污染 / 1 已污染
- 一句话：查询自上次 exec 以来是否因 SUID/SGID 或改过 uid/gid 而被标记

## getdtablesize (#89)
- handler：`kern_descrip.c` → `sys_getdtablesize`
- 读：`proc_limitgetcur_nofile(p)`（`RLIMIT_NOFILE`）
- 一句话：返回本进程 FD 表允许的最大大小，不是当前打开数量

## 今日对比
- 共同点：无参数、只读查询、`return 0`
- 差异：安全历史标志 vs 资源限制数字
