# Day 54 — renameat / unlinkat

> **正文：** [docs/day-54.md](../../docs/day-54.md)  
> **分析：** [day-54-analysis.md](day-54-analysis.md)

## renameat (#465)
- 入口：`renameat_internal`；双 `nameiat(fromfd/tofd)`
- 一句话：相对目录 FD 重命名/搬家目录项

## unlinkat (#472)
- 入口：默认 `unlinkat_internal`；`AT_REMOVEDIR` → rmdir
- 一句话：相对目录 FD 删除名字

## 今日对比
- 共同点：都是命名空间操作；cwd 版汇入同一 internal
- 最大差异：改名搬家 vs 删除（减链接/删目录）
