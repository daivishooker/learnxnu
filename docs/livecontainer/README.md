# LiveContainer 学习线

独立看板：弄清 [LiveContainer/LiveContainer](https://github.com/LiveContainer/LiveContainer) 如何「不真正安装」就跑 iOS App。

| 文档 | 内容 |
|------|------|
| [LEARNING_BOARD.md](LEARNING_BOARD.md) | **看板**（Backlog / Doing / Done） |
| [MECHANISM.md](MECHANISM.md) | 机制说明（Mach-O 改造 → dyld → dlopen 客应用） |
| [STARTUP_TRACE.md](STARTUP_TRACE.md) | 函数级冷启动跟读（Pass 1–7） |
| 源码 | [`projects/LiveContainer/`](../../projects/LiveContainer/) |

> 许可：**AGPL-3.0**（见上游 `LICENSE`）。仅作架构学习；第三方闭源改版会接触容器内全部数据，勿随意信任。

**当前快照：** `e370a92d`（3.8.0）。`litehook` 已纳入；`OpenSSL` 预编译库过大，仅留 stub。
