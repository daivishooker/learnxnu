# Day 47 — pathconf / fpathconf

> **正文：** [docs/day-47.md](../../docs/day-47.md)  
> **分析：** [day-47-analysis.md](day-47-analysis.md)

## pathconf (#191)
- 入口：`namei` → `vn_pathconf` →（常）`VNOP_PATHCONF`
- 一句话：按路径查询文件系统/路径相关配置

## fpathconf (#192, sys_fpathconf)
- 入口：`fp_lookup` → 按 DTYPE 分流 → vnode 则 `vn_pathconf`
- 一句话：按 FD 查询；socket/pipe 几乎只答 PIPE_BUF

## 今日对比
- 共同点：都是只读查询，不改对象
- 最大差异：路径 vs FD；FD 版显式类型分流
