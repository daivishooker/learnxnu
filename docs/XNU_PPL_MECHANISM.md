# XNU PPL / SPTM / TXM 机制完整分析

> 基准源码：本仓库 `xnu/` = **xnu-12377.121.6**  
> 范围：**Page Protection Layer（经典 PPL）**、继任者 **SPTM（Secure Page Table Monitor）**、协同的 **TXM（Trusted Execution Monitor）**，以及开源 XNU 侧如何接入  
> 相关：[`XNU_AMFI_MECHANISM.md`](XNU_AMFI_MECHANISM.md) · [`XNU_MTE_MECHANISM.md`](XNU_MTE_MECHANISM.md) · `xnu/doc/allocators/xnu-kernel-restricted.md`

---

## 0. 先把边界说清楚

| 组件 | 是否在开源 XNU 里 | 角色 |
|------|-------------------|------|
| **经典 PPL pmap 客户端** | **是**（`osfmk/arm/pmap/`、`arm64/locore.s` 等） | 把页表/签名关键数据放进受 APRR/xPRR 保护的域；经 trampoline 进入 |
| **PMAP_CS（PPL 内代码签名监视）** | **部分**（`pmap_cs.c`、`bsd/kern/code_signing/ppl.c`） | 在 PPL 环境中强制代码签名相关不变量 |
| **SPTM 固件 / libsptm** | **否**（仅有 XNU 客户端与头文件引用） | 更高特权组件：拥有页表变更与物理页**类型系统** |
| **TXM 固件** | **否**（`code_signing/txm.c` + 闭源 API 头） | 与 SPTM 协同的代码签名/信任监视器 |
| **无监视器后端** | **是**（`code_signing/xnu.c`） | 部分配置下 CSM 退化为纯 XNU |

树内选择逻辑（`bsd/sys/code_signing_internal.h`）：

```text
CONFIG_SPTM          → CODE_SIGNING_MONITOR_PREFIX = txm
PMAP_CS_PPL_MONITOR  → CODE_SIGNING_MONITOR_PREFIX = ppl
否则                 → xnu（无独立监视器）
```

较新 SoC（如 H14+ 板级头）要求 `CONFIG_SPTM`，并注明 **PPL 已弃用**。较旧芯片在未开 SPTM 时仍可走 `XNU_MONITOR` / 经典 PPL。

因此：

> **PPL 是「内核内、用权限寄存器隔出来的监视器」；**  
> **SPTM 把页表权威移出 XNU；TXM 是签名侧的配套监视器。**  
> 用户态**没有**直接的 `ppl()` / `sptm()` syscall——只通过普通 VM / 代码签名路径间接触发。

---

## 1. 总体架构（三代演进）

```text
┌─────────────────────────────────────────────────────────────┐
│ 用户态：vm_allocate / mmap / exec / csops / dyld            │
│         （无直接 PPL/SPTM API）                              │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ XNU：Mach VM + BSD 代码签名管线 + AMFI KPI                  │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ 无监视器     │   │ 经典 PPL        │   │ SPTM 时代        │
│ code_signing │   │ XNU_MONITOR     │   │ CONFIG_SPTM      │
│ /xnu.c       │   │ + PMAP_CS       │   │ + TXM            │
│              │   │ aprr_ppl_enter  │   │ sptm_* / txm_*   │
└──────────────┘   └────────┬────────┘   └────────┬─────────┘
                            │                     │
                            ▼                     ▼
                   ┌────────────────┐   ┌────────────────────┐
                   │ PPL 域（同核   │   │ SPTM（闭源固件）   │
                   │ EL1 子环境）   │   │ 物理页类型 + 页表 │
                   │ 页表/CS 数据   │   │ TXM：签名隔离      │
                   └────────────────┘   └────────────────────┘
```

| 模式 | 配置线索 | 监视器在哪 | 代码签名 CSM 前缀 |
|------|----------|------------|-------------------|
| 经典 PPL | `XNU_MONITOR`，且非 `CONFIG_SPTM` | XNU 内 PPL 段 + APRR | `ppl_` |
| SPTM+TXM | `CONFIG_SPTM` | 外部 SPTM + TXM | `txm_` |
| 无监视器 | 两者皆无 | — | `xnu_` |

---

## 2. 经典 PPL：如何把页表从「普通内核」手里拿走

### 2.1 要防什么

若攻击者已获得任意内核写：

- 可改页表，把内核私有页映射给用户或 IOMMU；  
- 可篡改代码签名相关元数据，绕过「只跑已授权代码」。

PPL 的目标：即使普通 EL1 内核文本被破坏，**也不能随意改受保护的页表与 PMAP_CS 数据结构**——必须经狭窄入口。

### 2.2 实现骨架（开源可见）

| 机制 | 说明 |
|------|------|
| **专用段** | `__PPLTEXT` / `__PPLDATA` / `__PPLDATA_CONST` / `__PPLTRAMP`；`MARK_AS_PMAP_TEXT` 等 |
| **APRR / xPRR** | 锁定后，普通内核与 PPL 对同一物理页看到不同「权限索引」（如 `XPRR_PPL_RW_PERM` vs 内核侧不可写） |
| **入口桩** | `PMAP_SUPPORT_PROTOTYPES` 生成包装：设索引 → `aprr_ppl_enter` → trampoline |
| **分发表** | `ppl_handler_table[PMAP_COUNT]` → 各 `*_internal`（位于 `__PPLTEXT`） |
| **每 CPU 栈 / 状态机** | `locore.s` 中 PPL 进出与 `PPL_STATE_*` |
| **锁定** | `pmap_lockdown_ppl()` / `pmap_static_allocations_done()` 完成 bootstrap 后收紧权限 |

概念调用：

```text
普通内核：pmap_foo(...)
  → pmap_foo_ppl 桩
  → aprr_ppl_enter (index)
  → ppl_dispatch → handler_table[index]
  → pmap_foo_internal（PPL 权限下改页表 / CS 结构）
  → 返回普通内核
```

### 2.3 PMAP_CS 与 `code_signing/ppl.c`

`ppl.c` 文件头说明要点：

- PPL 实现 **PMAP_CS** 监视环境：强制「系统执行的代码均经授权」相关不变量；  
- 凡非 PPL 自管的数据，XNU 须**页对齐**，并以**只读**方式引用交给监视器。

CSM 抽象宏 `CSM_PREFIX(name)` 在 PPL 配置下展开为 `ppl_name`（如 trust cache、developer mode、安全通道页等）。

### 2.4 关键源码路径

| 路径 | 角色 |
|------|------|
| `osfmk/arm/pmap/pmap.c` | 经典 pmap + PPL 集成（体量很大） |
| `osfmk/arm/pmap/pmap_ppl_interface.c` | PPL 入口包装、`pmap_mark_page_as_ppl_page` 等 |
| `osfmk/arm/pmap/pmap_cs.c` | PMAP_CS |
| `osfmk/arm/pmap/pmap_internal.h` | `PMAP_SUPPORT_PROTOTYPES` → `aprr_ppl_enter` |
| `osfmk/arm64/locore.s` | trampoline / dispatch |
| `bsd/kern/code_signing/ppl.c` | CSM 胶水 |
| `osfmk/vm/pmap_cs.h` | `PMAP_CS_PPL_MONITOR` 等 |
| `pexpert/.../board_config.h` | 板级是否 `XNU_MONITOR` |

**闭源缺口：** 完整 APRR/GXF 配置与部分入口实现依赖未公开头/固件；树内注释曾指向缺失的 `doc/arm/PPL.md`。

---

## 3. SPTM：页表监视器移出 XNU

### 3.1 角色

摘自树内文档 `doc/allocators/xnu-kernel-restricted.md`：

> Secure Page Table Monitor (SPTM) 是高特权组件，**代表 XNU** 定义并强制页表管理策略；目标是即使内核被攻破，仍保护页表与映射策略。

核心是**物理页类型系统（frame table）**：每个受管物理页有类型，类型决定允许的映射与转换。

### 3.2 重要帧类型（概念）

| 类型（文档/注释中的名字） | 含义 |
|---------------------------|------|
| `XNU_PAGE_TABLE` / `XNU_PAGE_TABLE_COMMPAGE` | 页表页 |
| `XNU_KERNEL_RESTRICTED` | 内核私有：禁止用户/IOMMU 映射；限制多重映射 |
| `XNU_DEFAULT` / `XNU_USER_*` | 普通/用户映射类 |
| `XNU_COMMPAGE_*` | commpage |
| `XNU_PROTECTED_IO` 等 | 受保护 I/O |

用途示例：防止 UAF/逻辑漏洞把内核指针页映射到用户空间；与 **MTE** 标签存储页的生命周期约束协同（见 MTE 文档）。

### 3.3 XNU 如何调用 SPTM

开源侧是**客户端**：

| 符号/概念 | 作用 |
|-----------|------|
| `libsptm_init` / `sptm/sptm_xnu.h` | 初始化与 API（头文件不在本树完整 SDK 中） |
| `sptm_retype` | 改变物理页类型 |
| `sptm_map_page` / `sptm_unmap_table` | 映射/拆页表 |
| `sptm_get_paddr_type` / `sptm_check_inflight` | 查询/同步 |
| `SPTM_DOMAIN_ENTER` | 进入 SPTM 域的汇编宏（闭源头） |
| `start_sptm.s` / `arm_init_sptm.c` | SPTM 跳入 XNU、`sptm_bootstrap_args_xnu_t` |

pmap 实现目录：`osfmk/arm64/sptm/pmap/`（SPTM 时代主路径）。

### 3.4 用户态接口

**无。** 可观测性上可能有 `kern.sptm` 一类 sysctl / 测试（`tests/sptm_info.c`），但不构成应用隔离 API。

---

## 4. TXM：SPTM 时代的代码签名监视器

`txm.c` 文件头：

> TrustedExecutionMonitor 与 SPTM 协同，为关键代码签名与内存隔离数据结构提供强制——确保执行的代码均经授权。

典型协作模式（开源胶水侧）：

```text
XNU 准备签名相关缓冲区（页对齐）
  → 将页所有权/类型交给 TXM（transfer / retype）
  → txm_kernel_call(selector, …)
  → TXM 在隔离环境中更新信任状态
  → XNU 只保留只读引用或经 API 查询
```

`CSM_PREFIX(*)` 在 `CONFIG_SPTM` 下指向 `txm_*`（developer mode、trust 相关、安全通道共享页等）。

与 AMFI 关系：

- **AMFI** 仍做策略/entitlement/CMS 等（kext）；  
- **TXM/PPL** 保护「签名与映射不变量」不被已受损内核任意篡改；  
- Trust Cache / blob 的部分状态可驻留监视器侧（`csb_csm_obj` 等）。

---

## 5. 应用层「用到了什么」——诚实对照表

PPL/SPTM/TXM **不是**像沙盒那样给应用一套 `sandbox_apply` API。应用层隔离间接受益：

| 应用/系统可见接口 | 实际是否进入监视器 | 说明 |
|-------------------|-------------------|------|
| `mmap` / `vm_allocate` / `mach_vm_*` | 可能 | 页表更新经 pmap → PPL 或 SPTM |
| `execve` / dyld / `F_ADDFILESIGS` / `csops` | 可能 | 签名路径经 AMFI + CSM（ppl/txm/xnu） |
| `task_for_pid` 等 | 间接 | 平台硬化与签名/监视器策略相关 |
| 直接 `ppl_*` / `sptm_*` / `txm_*` | **否（用户态）** | 仅内核/固件 |

若问「应用层用内核的哪些接口实现隔离」：

- **能力隔离** → Sandbox（另文）；  
- **身份与 entitlement** → AMFI + `csops`（另文）；  
- **PPL/SPTM** → **内核自我保护与映射完整性**，为上述机制提供硬件/监视器级底座，而不是 App 的「容器 API」。

---

## 6. 一次概念时序：用户 mmap 改页表（SPTM 机）

```text
1. 用户 mach_vm_allocate / mmap
2. XNU VM 决定需要新 PTE
3. arm64/sptm/pmap 组装请求
4. sptm_map_page / 相关 SPTM 调用（更高特权）
5. SPTM 查 frame 类型：允许则写页表；拒绝则失败
6. 返回用户 VA
```

经典 PPL 机把第 4–5 步换成 `aprr_ppl_enter` → `__PPLTEXT` 处理。

签名附着时序（监视器开启时）额外多一步：页对齐 blob → `txm_`/`ppl_` CSM API → 监视器认可后 AMFI/XNU 才视签名状态为最终有效。

---

## 7. 与休眠、MTE、PAC 的交叉

| 主题 | 交叉点 |
|------|--------|
| **Hibernation** | 树内 hibernation 文档提到对 PPL 相关页做 HMAC 等完整性保护 |
| **MTE** | 标签存储页与 `XNU_KERNEL_RESTRICTED` 等类型约束；SPTM 防止非法映射带标签内核页 |
| **PAC** | 指针认证；与 PPL/SPTM 正交，共同提高「损坏后仍难稳利用」的门槛 |
| **AMFI** | 策略引擎；监视器保护其依赖的映射与部分元数据 |

---

## 8. 开源树里能亲手验证的点

1. 读 `code_signing_internal.h` 三选一分支。  
2. 对比 `code_signing/ppl.c` 与 `txm.c` 文件头与导出符号前缀。  
3. 在 `pmap_ppl_interface.c` / `pmap_internal.h` 看 `_ppl` vs `_internal` 模式。  
4. 读 `doc/allocators/xnu-kernel-restricted.md` 理解 SPTM 类型系统动机。  
5. 浏览 `osfmk/arm64/sptm/` 启动与 pmap 客户端（无 libsptm 源码）。  
6. 板级头：`pexpert/pexpert/arm64/H1*.h` 对 `CONFIG_SPTM` 的要求。

---

## 9. 小结（可背）

1. **经典 PPL**：同核 EL1 内用 APRR + 专用段 + trampoline，保护页表与 PMAP_CS。  
2. **SPTM**：页表权威外移；物理页**类型系统**限制映射，即使内核被破仍难任意建非法映射。  
3. **TXM**：SPTM 时代的代码签名监视器；XNU 经 `txm_kernel_call` 等胶水协作。  
4. **用户态无直接 API**；隔离效果体现在 VM/签名路径更难被内核级漏洞一步打穿。  
5. 与 AMFI/Sandbox/MTE 的分工：监视器守「映射与签名不变量」，AMFI 守「信任与 entitlement」，Sandbox 守「能力」。

---

## 10. 参考

### 本树

- `bsd/sys/code_signing_internal.h`  
- `bsd/kern/code_signing/{ppl,txm,xnu}.c`  
- `osfmk/arm/pmap/pmap*.c` / `pmap_ppl_interface.c` / `pmap_cs.c`  
- `osfmk/arm64/sptm/` · `osfmk/arm64/locore.s`  
- `doc/allocators/xnu-kernel-restricted.md`  
- `doc/lifecycle/hibernation.md`（PPL 相关提及）  

### 外部

- Apple 平台安全指南中关于内核完整性 / 页表保护的公开描述  
- 公开研究：PPL、SPTM、TXM、APRR  

---

*文档生成说明：SPTM/TXM 固件与 libsptm/TXM API 头不在本树；经典 PPL 的部分硬件入口亦依赖闭源配置。文中「闭源侧」为基于开源胶水与官方树内文档的机制还原。*
