# 源码分析：Day 20（kevent64 / kevent_qos）

基于 `xnu-12377.121.6`。Darwin 事件口演进。

---

## 1. 心智模型

```text
Day 19：kqueue + knote + kevent（取信/登记）

Day 20：同一邮箱，换更强的“信件格式”和投递系统
  kevent      旧信封
  kevent64    大信封 + flags（仍走 legacy 分拣）
  kevent_qos  新分拣线（modern），可接 workqueue / QoS
```

---

## 2. 调用汇合

[`kern_event.c`](../../xnu/bsd/kern/kern_event.c)：

```
kevent
  → kevent_legacy_internal(..., KEVENT_FLAG_LEGACY32)

kevent64
  → kevent_legacy_internal(..., KEVENT_FLAG_LEGACY64 | 用户flags)

两者最终：
  kevent_get_kqfile / kevent_get_kqwq
  → kevent_internal(..., legacy=true)


kevent_qos
  →（WORKQ？）kevent_get_kqwq : kevent_get_kqfile
  → kevent_modern_internal(...)
  → kevent_internal(..., legacy=false)
```

验收点：**底层仍是 kqueue；syscall 包装和事件 ABI 在变。**

---

## 3. kevent64 要点

- 用户结构：`struct kevent64_s`  
- 形参多了 `flags`（经 `KEVENT_FLAG_USER` 掩码后并入）  
- copyin/copyout 走 `kevent_legacy_copyin/out` 的 LEGACY64 分支  
- 超时仍是 `timespec`（legacy_internal 里算 deadline）  

相对 Day 19 的 `kevent`：学会“为什么要 64 版”——ident/data 等字段宽度、扩展 flags。

---

## 4. kevent_qos 要点

- 用户结构：`struct kevent_qos_s`  
- 额外：`data_out` / `data_available`（事件附带数据通道）  
- `KEVENT_FLAG_WORKQ`：操作进程 workqueue 侧 kqueue，而不是普通 kq fd  
- 现代用户态（libdispatch）靠这套把“事件就绪”和“用什么 QoS 的线程来跑”接起来  

今天深度：跟到 **modern vs legacy 分叉** 即可；workloop/parking 等细节可留专题。

---

## 5. 和 select/poll 对照（第 3 周多路 IO 收束）

| API | 兴趣集在哪 | Darwin 现状 |
|-----|------------|-------------|
| select/poll | 每次调用带齐 | 可用；poll 本树甚至转 kqueue |
| kevent/64 | kqueue | 通用程序常用 |
| kevent_qos | kqueue + 运行时集成 | 系统框架/GCD 重 |

---

## 6. 建议点开的文件

1. `syscalls.master` — 363 / 369 / 374  
2. `kern_event.c` — `kevent` / `kevent64` / `kevent_qos` 三个入口  
3. 同文件 `kevent_legacy_internal` vs `kevent_modern_internal` 调用  

验收：能画「三代 syscall → 两类 internal → 同一个 kqueue 模型」。
