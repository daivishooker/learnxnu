# Day 20 — kevent64 / kevent_qos

> **正文：** [docs/day-20.md](../../docs/day-20.md)  
> **分析：** [day-20-analysis.md](day-20-analysis.md)

## kevent64 (#369)
- 入口：`kevent64` → `kevent_legacy_internal`（`KEVENT_FLAG_LEGACY64`）
- 一句话：kqueue 事件口的 64 位结构版，多 flags，仍走 legacy 路径

## kevent_qos (#374)
- 入口：`kevent_qos` → `kevent_modern_internal`
- 一句话：现代 kevent；可接 workqueue/QoS，支持额外 data_out

## 今日对比
- 共同点：都是对 kqueue 注册/取事件（和 Day 19 kevent 同一家族）
- 最大差异：legacy 升级 vs 面向 QoS/工作队列的 modern 入口
