# Day 39 — exchangedata / copyfile

> **正文：** [docs/day-39.md](../../docs/day-39.md)  
> **分析：** [day-39-analysis.md](day-39-analysis.md)

## exchangedata (#223)
- 入口：双 `namei` → 同 mount、皆 VREG → `VNOP_EXCHANGE`
- 一句话：交换两文件数据内容，路径名不变

## copyfile (#227)
- 入口：源 LOOKUP + 目标 CREATE → 鉴权 → `VNOP_COPYFILE`
- 一句话：内核/FS 侧拷贝到新路径（无公开 stub）

## 今日对比
- 共同点：整文件级 VFS 操作，落到 filesystem VNOP
- 最大差异：对调已有两者内容 vs 复制出目标
