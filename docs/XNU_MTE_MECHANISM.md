# XNU MTE 机制完整分析

> 基准源码：本仓库 `xnu/` = **xnu-12377.121.6**  
> 范围：ARM **Memory Tagging Extension（MTE）** 在 XNU 中的启用、标签存储、VM 接口、故障路径，以及与 AMFI / SPTM / PAC 的关系  
> 相关：[`XNU_AMFI_MECHANISM.md`](XNU_AMFI_MECHANISM.md) · [`XNU_PPL_MECHANISM.md`](XNU_PPL_MECHANISM.md) · `xnu/doc/arm/apple_speculative_hardening.md`

---

## 0. 先把边界说清楚

| 组件 | 是否在开源 XNU 里 | 角色 |
|------|-------------------|------|
| **MTE ISA 封装** | **是**（`osfmk/arm64/mte.h`、`mte.c`） | `STG`/`LDG`/`IRG`/TCO 等；`vm_memtag_*` 实现 |
| **标签存储管理** | **是**（`vm_mteinfo.c` 等） | DRAM 中 allocation tag 元数据页的生命周期 |
| **VM 用户接口** | **是**（`VM_FLAGS_MTE` 等） | 用户/内核为映射打开 MTE |
| **硬件检查** | **CPU 架构** | 访问时比较 VA 逻辑标签与内存分配标签 |
| **AMFI MTE 策略** | KPI 在 `amfi.h`；策略在 **AMFI.kext** | 进程是否 soft-mode / opt-out / 继承等 |
| **SPTM 约束** | 客户端在 XNU；策略在 **SPTM** | 标签页类型、禁止非法映射带标签内核页 |
| **KASAN-TBI** | **是**（`san/memory/kasan-tbi.c`） | 软件 TBI 标签路径，与 `vm_memtag` 共用抽象 |

板级：`HAS_MTE` 在较新 Apple Silicon（如 H17 头文件）上定义；无 `HAS_MTE` 的配置下整套代码被裁掉。

因此：

> **MTE 是硬件内存安全机制（防 UAF/越界混用），不是沙盒那种「能力白名单」。**  
> XNU 负责开标签、存标签、递故障；**是否对某进程强制/放宽**常与 AMFI/任务安全策略绑定。

---

## 1. 总体架构

```text
┌────────────────────────────────────────────────────────────┐
│ 用户态                                                     │
│  • vm_allocate(..., VM_FLAGS_MTE) / 等价 Mach VM 标志      │
│  • 编译器/分配器：打标签指针（逻辑标签在 VA 高位）         │
│  • 标签不匹配 → 同步/异步异常 → 信号或 guard exception     │
└────────────────────────────┬───────────────────────────────┘
                             │ Mach VM
                             ▼
┌────────────────────────────────────────────────────────────┐
│ XNU VM / pmap                                              │
│  • VM_MEM_MAP_MTE / MAIR_MTE_WRITEBACK / TCR_MTX*          │
│  • mte_generate_and_store_tag / vm_memtag_*                │
│  • vm_mteinfo：标签存储「cells」                           │
│  • sleh.c：EXC_ARM_MTE_TAGCHECK_FAIL 等                    │
└───────────────┬────────────────────────────┬───────────────┘
                │ 策略查询                    │ 页类型/映射
                ▼                             ▼
┌───────────────────────────┐   ┌────────────────────────────┐
│ AMFI has_mte_*            │   │ SPTM（若 CONFIG_SPTM）     │
│ soft_mode / opt_out / …   │   │ 标签页与 KERNEL_RESTRICTED │
└───────────────────────────┘   └────────────────────────────┘
                             ▲
                             │ 硬件
                    ARM MTE：访问时比标签
```

**与 PAC 的分工：**

| | PAC（ARM64e） | MTE |
|--|---------------|-----|
| 保护对象 | **指针**（签名/认证） | **数据颗粒**（分配标签） |
| 失败表现 | `EXC_ARM_PAC_FAIL` 等 | `EXC_ARM_MTE_TAGCHECK_FAIL` / canonical fail |
| VA 顶字节 | TBI / ptrauth | 逻辑标签占用顶半字节一带（与 TBI 共存，见 `TCR_MTX*`） |
| 典型防 | 函数指针/返回地址篡改 | UAF、线性越界读写到错误对象 |

二者互补，不是互相替代。

---

## 2. 硬件与内核概念

### 2.1 标签是什么

- 内存按颗粒（常见 16 字节）带 **allocation tag**（4 bit）。  
- 指针 VA 携带 **logical tag**（顶字节相关比特）。  
- 访问时硬件比较；不匹配 → tag check fault。  
- **Canonical tag**：内核侧常用 `0xF`、用户侧常用 `0x0` 表示「无标签/规范」语义（实现细节见 `vm_memtag`）。

### 2.2 ISA 与控制（`mte.h` / 系统寄存器）

| 概念 | 用途 |
|------|------|
| `STG` / `ST2G` / `DC GVA` / `STGM` / `LDGM` | 存/批量操作标签 |
| 随机标签（IRG/ACLE） | 分配时生成 |
| **TCO**（Tag Check Override） | 临时关闭检查（调试/特殊路径；有 debug 开关可审计） |
| `SCTLR_ELx.ATA/ATA0`、`TCF/TCF0` | 启用检查；默认同步故障模式相关配置 |

### 2.3 Boot 配置（`mte_xnu.h`）

开发/调试常用（iBoot/SPTM 也会认 `-disable_mte`）：

| boot-arg | 作用 |
|----------|------|
| `-disable_mte` | 整机关闭 MTE |
| `mte_config=` | 位掩码：内核/用户、default/pure-data 检查开关 |
| `mte_debug=` | 强制所有用户进程、TCO 调试、非规范地址 panic、异步故障 panic 等 |

`mte_config` 位（概念）：

| 位 | 含义 |
|----|------|
| `MTE_ENABLE_KERNEL` | 内核标签检查 |
| `MTE_ENABLE_KERNEL_PURE_DATA` | 内核纯数据也检查 |
| `MTE_ENABLE_USER` | 用户态检查 |
| `MTE_ENABLE_USER_PURE_DATA` | 用户纯数据检查 |

默认（DEV/RELEASE 注释）：内核+用户及 pure-data 均开。运行时用 `mte_kern_enabled()` / `mte_user_enabled()` 等 static if 查询。

---

## 3. XNU 实现地图

| 路径 | 内容 |
|------|------|
| `osfmk/arm64/mte.h` | 标签存取、TCO、随机标签辅助 |
| `osfmk/arm64/mte_xnu.h` | boot-arg、批量标签、soft-mode API |
| `osfmk/arm64/mte.c` | `vm_memtag_*`、`mte_guard_ast` |
| `osfmk/vm/vm_memtag.h` | 统一 memtag API（MTE / KASAN-TBI / 模拟） |
| `osfmk/vm/vm_mteinfo.c` | 标签存储页状态机（体量最大） |
| `osfmk/arm64/vm_mte_compress.c` | 压缩器与标签元数据 |
| `osfmk/arm64/sleh.c` | MTE（与 PAC）异常入口 |
| `osfmk/mach/arm/exception.h` | `EXC_ARM_MTE_*` |
| `osfmk/mach/vm_statistics.h` | **`VM_FLAGS_MTE` (0x2000)** |
| `libkern/libkern/amfi/amfi.h` | `has_mte_soft_mode` 等 |
| `tests/arm_mte*.c`、`tests/vm/vm_*mte*` | 行为测试 |

### 3.1 分配时打标签

概念路径：

```text
带 MTE 的分配 / 映射建立
  → mte_generate_and_store_tag（避开邻居标签与 canonical，随机化）
  → 标签写入 tag storage（与数据页关联）
  → 返回带逻辑标签的指针（或后续由分配器打标签）
```

### 3.2 标签存储（`vm_mteinfo`）

- 物理 DRAM 的一部分用作 tag storage（数量级约 **1/32** 量级，以树内设计为准）。  
- 以「cell」管理；与 SPTM 协作：**未激活/已回收的标签 cell 不得当普通 MTE 数据用错类型**。  
- 换页/压缩路径需保存或重建标签（`vm_mte_compress.c`）。

### 3.3 Soft-mode 与进程策略

| 策略概念 | 效果 |
|----------|------|
| **正常强制** | 标签失败 → 异常/终止类行为 |
| **soft-mode** | 可降级：清用户检查、`TASK_SEC_POLICY_NEVER_CHECK` 一类；故障走 guard/`mte_guard_ast` |
| **opt-out / inheritance / alias** | 由 **AMFI** 根据签名/entitlement 回答（`amfi->has_mte_*`） |
| **force all**（debug） | `mte_debug` 强制所有用户进程启用 |

任务侧通过 `task_has_sec*` / 安全策略位与 AMFI 查询结合，决定子进程是否继承 MTE 行为。

---

## 4. 应用层：用哪些接口「用上」MTE

MTE **不是**独立 BSD syscall，而是 **Mach VM 标志 + 硬件 + 异常**。

### 4.1 主接口：`VM_FLAGS_MTE`

```c
// osfmk/mach/vm_statistics.h
#define VM_FLAGS_MTE  0x00002000
```

出现在用户可传递的 allocate 标志集合中（与 `VM_FLAGS_TPRO` 同属 `VM_FLAGS_HW`）。

典型用法（概念）：

```c
mach_vm_allocate(task, &addr, size, VM_FLAGS_ANYWHERE | VM_FLAGS_MTE);
```

区域信息可出现 `VM_REGION_FLAG_MTE_ENABLED`；WIMG 侧有 `VM_WIMG_MTE`。

### 4.2 谁决定进程默认开不开

| 来源 | 说明 |
|------|------|
| 平台默认 / hardened heap | 系统分配器与进程硬化配置 |
| **AMFI** | `has_mte_soft_mode`、`has_mte_opt_out`、inheritance、data tagging、alias restriction |
| boot-arg | 全局或 debug 强制 |
| 显式 `VM_FLAGS_MTE` | 调用方为该映射请求标签内存 |

第三方应用通常**不**直接编程 STG；由系统 libmalloc / 运行时在支持平台上透明使用。研究/测试代码则可显式打标志并观察故障。

### 4.3 故障如何回到应用层

| 路径 | 说明 |
|------|------|
| 同步 tag check fault | `sleh` → `EXC_ARM_MTE_TAGCHECK_FAIL` 等 → 信号/异常端口 |
| Canonical fail | `EXC_ARM_MTE_CANONICAL_FAIL` |
| Soft-mode / async | `GUARD_VM` / `mte_guard_ast`；debug 下可 panic-on-async |
| `vm_guard_is_mte_policy` | 识别 MTE 相关 guard flavor |

### 4.4 接口汇总

| # | 接口 | 层 | 说明 |
|---|------|-----|------|
| 1 | `vm_allocate` / `mach_vm_allocate` + **`VM_FLAGS_MTE`** | Mach VM | **显式请求 MTE 映射** |
| 2 | 区域查询标志 `VM_REGION_FLAG_MTE_ENABLED` | Mach VM | 观察映射是否启用 |
| 3 | 异常 / guard（`EXC_ARM_MTE_*`） | Mach exception | 标签失败交付 |
| 4 | 系统分配器（libmalloc 等） | 用户库 | 平台上透明打标签（闭源/系统库） |
| 5 | AMFI entitlement/策略（间接） | 签名 | 决定 soft-mode / opt-out 等 |
| 6 | boot-arg / sysctl（设备策略） | 启动 | 全局开关；非应用 API |

---

## 5. 一次完整时序：UAF 被 MTE 拦住（概念）

```text
1. 进程在支持 MTE 的平台上运行，堆启用标签
2. malloc → 内核/分配器：数据页 + 随机 allocation tag；指针带 logical tag A
3. free → 标签被清除或改为其它值（或区域复用前改标签）
4. 悬垂指针（仍带 tag A）再写入
5. 硬件比较失败 → tag check fault
6. sleh 投递 EXC_ARM_MTE_* 或 soft-mode guard
7. 进程崩溃或进入平台故障处理 —— 攻击者无法稳定读写已释放对象
```

若映射未带 MTE 或进程 opt-out/soft-mode，则无此硬件门禁（回退到传统内存安全风险模型）。

---

## 6. 与 SPTM / AMFI / 推测执行

| 机制 | 关系 |
|------|------|
| **SPTM** | 标签存储与内核带标签页的映射策略；`XNU_KERNEL_RESTRICTED` 等防止把内核私有（含标签相关）页暴露给用户/IOMMU |
| **AMFI** | 每进程 MTE 策略查询（`KERN_AMFI_SUPPORTS_MTE`） |
| **PAC** | 同属顶字节/指针生态；推测执行文档强调 **MTE 标签也不可泄露** |
| **KASAN-TBI** | 无硬件 MTE 时的软件近亲；共享 `vm_memtag` 抽象 |
| **Sandbox** | 正交：Sandbox 限能力，MTE 限内存安全 bug 利用 |

---

## 7. 开源树里能亲手验证的点

1. 读 `vm_statistics.h` 中 `VM_FLAGS_MTE`。  
2. 读 `mte_xnu.h` 的 `mte_config` / `mte_debug`。  
3. 读 `mte.c` / `vm_memtag.h` 的生成与存储标签 API。  
4. 在 `sleh.c` / `exception.h` 搜 `MTE`。  
5. 读 `amfi.h` 的 `has_mte_*` 回调表。  
6. 跑/读 `tests/arm_mte*.c`（需对应硬件与内部 SDK）。  
7. 对照 `doc/arm/apple_speculative_hardening.md` 与 `doc/allocators/xnu-kernel-restricted.md`。

---

## 8. 小结（可背）

1. **MTE = 硬件标签比较**；XNU 管启用、标签存储、VM 标志与故障递送。  
2. 应用层主开关是 Mach **`VM_FLAGS_MTE`**；日常多由系统分配器透明使用。  
3. **AMFI** 提供 per-process 策略（soft-mode/opt-out 等）；**SPTM** 约束标签页与内核映射。  
4. 与 **PAC** 互补：PAC 护指针，MTE 护对象粒度内存。  
5. 它不替代 Sandbox/AMFI：不回答「能不能访问相机」，而回答「野指针能不能稳利用」。

---

## 9. 参考

### 本树

- `osfmk/arm64/mte.h` / `mte_xnu.h` / `mte.c`  
- `osfmk/vm/vm_memtag.h` / `vm_mteinfo.c`  
- `osfmk/mach/vm_statistics.h` · `osfmk/mach/arm/exception.h`  
- `libkern/libkern/amfi/amfi.h`（MTE 段）  
- `doc/allocators/xnu-kernel-restricted.md`  
- `doc/arm/apple_speculative_hardening.md`  
- `tests/arm_mte*.c`

### 外部

- ARM Architecture Reference：MTE  
- Apple 平台安全说明中的内存标记相关公开材料  

---

*文档生成说明：AMFI 内 MTEPolicy、系统分配器打标签实现、SPTM 对标签页的完整策略属闭源或固件；本文以开源 XNU 挂接点为准。*
