# XNU AMFI 机制完整分析

> 基准源码：本仓库 `xnu/` = **xnu-12377.121.6**  
> 范围：内核 **代码签名管线（开源）** + **AMFI.kext / CoreTrust / amfid（闭源，据 KPI 与 MAC 挂接点还原）**  
> 相关：[`XNU_SANDBOX_MECHANISM.md`](XNU_SANDBOX_MECHANISM.md) · [`XNU_PPL_MECHANISM.md`](XNU_PPL_MECHANISM.md) · Day 65 `csops` · [`SYSCALL_SECURITY_WHITEPAPER.md`](SYSCALL_SECURITY_WHITEPAPER.md)

---

## 0. 先把边界说清楚

| 组件 | 是否在开源 XNU 里 | 角色 |
|------|-------------------|------|
| **cs_blob / UBC 签名附着** | **是**（`bsd/kern/ubc_subr.c`、`kern_cs.c`） | 解析 SuperBlob、算 CDHash、挂到 vnode、维护 `CS_*` 标志 |
| **`csops` / `csops_audittoken`** | **是**（`bsd/kern/kern_proc.c`） | 用户态查询/改进程代码签名状态的主 syscall |
| **MAC Framework** | **是**（`security/mac_*`） | 在签名校验、exec、csops 等路径上调用策略钩子 |
| **`amfi_t` KPI** | **是**（接口声明 + 注册桩：`libkern/amfi/`） | XNU 调用 AMFI 的函数指针表；**实现由 kext 填入** |
| **AppleMobileFileIntegrity.kext** | **否** | 真正的信任裁决：证书链、profile、entitlement、LV、平台二进制策略 |
| **CoreTrust.kext** | **否**（KPI 在 `libkern/coretrust/`） | CMS / 证书策略评估，供 AMFI 使用 |
| **amfid** | **否**（仅有 `HOST_AMFID_PORT`） | 用户态守护进程，协助部分签名/信任判定 |
| **Trust Cache** | 格式与运行时包装在 XNU；装载/查询经 `amfi->TrustCache` | 预置/运行时 CDHash 白名单 |

因此：

> **XNU 开源部分实现「代码签名存储 + 强制标志 + MAC 分发 + AMFI KPI」；**  
> **「这份签名是否可信、能否拿哪些 entitlement」在闭源 AMFI（及 CoreTrust / 监视器）里。**

---

## 1. 总体架构

```text
┌──────────────────────────────────────────────────────────────┐
│ 应用 / 系统用户态                                            │
│  • codesign 工具签 Mach-O（LC_CODE_SIGNATURE）               │
│  • dyld：fcntl(F_ADDFILESIGS*) 为库附着签名                  │
│  • csops(pid, CS_OPS_*, …) 查询状态 / entitlement / CDHash   │
│  • amfid（经 HOST_AMFID_PORT）                               │
└────────────────────────────┬─────────────────────────────────┘
                             │ BSD syscall / fcntl / exec
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ XNU 开源管线                                                 │
│  • ubc_cs_blob_add → 构建 struct cs_blob                     │
│  • mac_vnode_check_signature / mac_vnode_check_exec          │
│  • cs_flags：CS_VALID / CS_ENFORCEMENT / CS_PLATFORM_BINARY  │
│  • csops → mac_proc_check_{get,set}_cs_info                  │
│  • kern_trustcache.c → amfi->TrustCache.*                    │
└───────────────┬────────────────────────────┬─────────────────┘
                │ amfi_interface_register     │ MAC_CHECK(mpo_*)
                ▼                             ▼
┌────────────────────────────┐  ┌──────────────────────────────┐
│ AMFI.kext（闭源）          │  │ AMFI 作为 mac_policy 模块    │
│  amfi_t：                  │  │  mpo_vnode_check_signature   │
│  • OSEntitlements.*        │  │  mpo_vnode_check_exec        │
│  • TrustCache.*            │  │  mpo_cred_*_execve           │
│  • MTE 策略查询            │  │  mpo_proc_check_*_cs_info    │
│  • CoreEntitlements        │  │  mpo_file_check_library_val  │
└────────────┬───────────────┘  └──────────────────────────────┘
             │
             ▼
┌────────────────────────────┐     ┌───────────────────────────┐
│ CoreTrust（闭源）          │     │ 代码签名监视器（可选）    │
│  CMS / 证书评估 KPI        │     │  PPL PMAP_CS 或 SPTM+TXM  │
└────────────────────────────┘     └───────────────────────────┘
```

**与沙盒的分工（直觉）：**

| | AMFI | Sandbox |
|--|------|---------|
| 回答的问题 | 「这段代码是谁签的、可信吗、有哪些 entitlement？」 | 「在已可信的前提下，允许做什么？」 |
| 强制面 | 签名校验、库验证(LV)、平台位、csops | MAC 钩子上的能力白名单 |
| 共同依赖 | entitlement 真伪由 AMFI 保证；Sandbox 用其内容生成规则 | |

---

## 2. 内核侧：开源代码签名管线

### 2.1 源码地图（本树）

| 路径 | 内容 |
|------|------|
| `libkern/libkern/amfi/amfi.h` | **`amfi_t`**、`KERN_AMFI_INTERFACE_VERSION`（当前 **7**） |
| `libkern/amfi/amfi.c` | `amfi_interface_register()` —— kext 注册唯一入口 |
| `osfmk/kern/cs_blobs.h` | `CS_*` 标志、`CS_CodeDirectory`、CDHash 长度 |
| `bsd/sys/codesign.h` | 用户态 `csops` 操作码与声明 |
| `bsd/sys/ubc_internal.h` | **`struct cs_blob`** |
| `bsd/kern/ubc_subr.c` | `ubc_cs_blob_add`、调用 `mac_vnode_check_signature` |
| `bsd/kern/kern_cs.c` | 强制、`cs_invalid_page`、blob 访问器 |
| `bsd/kern/kern_proc.c` | **`csops` / `csops_internal`** |
| `bsd/kern/kern_codesigning.c` | 启动配置、`amfi*` boot-arg 解析 |
| `bsd/kern/kern_trustcache.c` | Trust Cache 运行时包装 |
| `bsd/kern/code_signing/{xnu,ppl,txm}.c` | 无监视器 / PPL / TXM 后端 |
| `security/mac_vfs.c` / `mac_process.c` | 签名与 csops 相关 MAC 封装 |
| `osfmk/mach/host_special_ports.h` | `HOST_AMFID_PORT` |

### 2.2 `struct cs_blob`：签名在内核里长什么样

附着在 vnode/UBC 上的只读结构，关键字段概念：

| 字段（概念） | 含义 |
|--------------|------|
| `csb_cdhash[CS_CDHASH_LEN]` | Code Directory 哈希（默认 20 字节） |
| `csb_flags` | `CS_VALID`、`CS_HARD`、`CS_KILL`、`CS_ENFORCEMENT`、`CS_PLATFORM_BINARY` 等 |
| `csb_cd` / SuperBlob | 原始签名数据视图 |
| `csb_entitlements` | **AMFI 分配的 OSEntitlements 对象**（另有 ptrauth 签名） |
| `csb_signer_type` / validation category | 签名者类别（平台、开发者等） |
| `csb_csm_obj`（监视器路径） | 交给 PPL/TXM 的监视器侧对象 |

XNU 负责解析布局与存盘；**是否把 `CS_VALID` 立上、entitlement 对象如何构造**，由 AMFI MAC 钩子与 KPI 决定。

### 2.3 附着签名：`ubc_cs_blob_add`

典型路径（库加载 / 映像签名注入）：

```text
fcntl(F_ADDFILESIGS / F_ADDFILESIGS_RETURN / …)
  → kern_descrip.c
  → ubc_cs_blob_add(vp, …)
       1. 解析 SuperBlob / Code Directory，算 CDHash
       2. 填充临时 cs_blob
       3. mac_vnode_check_signature(vp, blob, …, &cs_flags, &signer_type, …)
            → AMFI mpo_vnode_check_signature：信任裁决，可改 flags / 填 fatal 原因
       4. 成功则挂到 vnode；加速 entitlement 查询 → amfi->OSEntitlements.adjustContext*
```

exec 主路径还会走：

```text
kern_exec / mach_loader
  → mac_vnode_check_exec
  → mac_cred_check_label_update_execve / mac_cred_label_update_execve
       → AMFI 在凭证/进程上落实 entitlement 与 cs 状态
```

### 2.4 强制与失效：`CS_VALID` 生命周期

| 事件 | 行为（开源侧） |
|------|----------------|
| 校验通过 | 进程/映像带 `CS_VALID` 等标志 |
| 映射页与签名哈希不匹配 | `cs_invalid_page` → 清 `CS_VALID` |
| `CS_KILL` / `CS_HARD` | 失效后杀进程或拒绝继续 |
| 调试例外 | `mac_proc_check_run_cs_invalid`（AMFI 可允许「带着无效签名跑」） |
| 通知 | `mpo_proc_notify_cs_invalidated` |

系统级开关：`cs_system_enforcement` / `cs_process_enforcement`；开发机可用 boot-arg 放宽（见 §4）。

### 2.5 MAC 钩子：AMFI 真正「坐」在哪里

AMFI.kext 作为 MAC 策略注册后，开源树通过这些封装调用它：

| MAC 封装 | 策略钩子（概念） | 用途 |
|----------|------------------|------|
| `mac_vnode_check_signature` | `mpo_vnode_check_signature` | **核心信任裁决**（附着/重验签名） |
| `mac_vnode_check_supplemental_signature` | 同族 | 补充签名 |
| `mac_vnode_check_exec` | `mpo_vnode_check_exec` | 执行许可 + csflags |
| `mac_cred_*_execve` | `mpo_cred_*_execve` | exec 时标签 / entitlement 过渡 |
| `mac_proc_check_get_cs_info` / `set_cs_info` | `mpo_proc_check_*_cs_info` | **门禁 `csops`** |
| `mac_proc_check_run_cs_invalid` | 同名 | 是否允许无效签名继续跑 |
| `mac_file_check_library_validation` | LV 相关 | dyld 加载库时的库验证 |

`MAC_CHECK` 语义与沙盒相同：多策略同时存在时错误合成（拒绝优先）。AMFI 与 Sandbox、Quarantine 可并存。

### 2.6 `amfi_t`：开源 XNU 调用闭源实现的总线

注册：

```c
void amfi_interface_register(const amfi_t *mfi);  // 仅允许注册一次，重复则 panic
```

`amfi_t` 主要能力组（`amfi.h`）：

| 组 | 能力 |
|----|------|
| **OSEntitlements** | invalidate / asdict / query / get_xml / get_transmuted；`adjustContext*`；按名查 bool/string；拷贝为 OSObject |
| **CoreEntitlements** | 新版 DER entitlement 查询 API |
| **TrustCache** | `load` / `loadModule` / `query` / UUID·能力查询 / runtime 检查 |
| **MTE 策略**（`KERN_AMFI_SUPPORTS_MTE`） | soft mode、opt-out、inheritance、data tagging、alias restriction |

XNU 各处（UBC、trustcache、IOKit entitlement 查询、pmap、exec/MTE）通过全局指针 `amfi` 间接调用；**若 AMFI 未注册而走到 Trust Cache 等路径会 panic/失败**。

### 2.7 Trust Cache

- 格式：`osfmk/kern/trustcache.h`（v0/v1 条目、模块、`CS_TRUST_CACHE_AMFID` 等标志）  
- 运行时：`kern_trustcache.c` **只**经 `amfi->TrustCache.*` 装载与查询  
- 用途：系统映像/平台组件的 CDHash 快速放行；与完整 CMS 验签互补  

监视器时代（PPL/TXM）下，信任根与部分 blob 状态会进一步放到更高特权域（见 PPL 文档）。

---

## 3. 应用层：用哪些接口与 AMFI/签名体系交互

### 3.1 `csops` —— 主用户态内核接口

声明（`bsd/sys/codesign.h`）：

```c
int csops(pid_t pid, unsigned int ops, void *useraddr, size_t usersize);
int csops_audittoken(pid_t pid, unsigned int ops, void *useraddr, size_t usersize,
                     audit_token_t *token);
```

Syscall：**169 / 170**（`syscalls.master`）。

| ops | 含义 |
|-----|------|
| `CS_OPS_STATUS` | 读进程代码签名状态标志 |
| `CS_OPS_MARKINVALID` / `MARKHARD` / `MARKKILL` / `MARKRESTRICT` | 标记无效或粘性 HARD/KILL/RESTRICT |
| `CS_OPS_CDHASH` / `CDHASH_WITH_INFO` | 取 CDHash |
| `CS_OPS_ENTITLEMENTS_BLOB` / `DER_ENTITLEMENTS_BLOB` | 取 entitlement（XML/DER；经 AMFI 对象） |
| `CS_OPS_BLOB` / `IDENTITY` / `TEAMID` | SuperBlob / 身份 / Team ID |
| `CS_OPS_SET_STATUS` / `CLEAR_LV` / … | 设标志、清库验证位等（受 MAC/entitlement 约束） |
| `CS_OPS_VALIDATION_CATEGORY` | 验证类别 |

路径：

```text
csops
  → csops_internal
  → mac_proc_check_get_cs_info / set_cs_info   // AMFI 可拒绝
  → 读 CS 状态，或 amfi->OSEntitlements_get_xml 等
```

### 3.2 `fcntl(F_ADDFILESIGS*)`

dyld / 加载器为已映射文件注入签名 blob，触发 `ubc_cs_blob_add` → AMFI 校验。  
这是**库加载时**应用层间接使用内核签名模块的主路径（应用通常不手写，而由 dyld 完成）。

### 3.3 代码签名与 Entitlement（构建/分发侧）

| 层次 | 机制 |
|------|------|
| 构建 | `codesign` / Xcode 写入 `LC_CODE_SIGNATURE` + entitlement plist/DER |
| 分发 | App Store / Notarization / 企业/开发证书链 |
| 运行 | 内核+AMFI 验签；IOKit/沙盒/系统服务用 entitlement 做授权 |
| 内核消费者 | `amfi->OSEntitlements.query*`（驱动查进程 entitlement） |

应用**不会**直接调用 `mpo_vnode_check_signature`；那是 kext 提供给 MACF 的回调。

### 3.4 amfid

- 内核仅暴露特殊端口：`HOST_AMFID_PORT` / `host_get_amfid_port`  
- 守护进程与 AMFI.kext 用户客户端协作（闭源）  
- Trust Cache 标志 `CS_TRUST_CACHE_AMFID` 表示「对 amfid 而言有效的 CDHash」一类语义  

### 3.5 接口汇总（应用/库作者视角）

| # | 接口 | 层 | 说明 |
|---|------|-----|------|
| 1 | `csops` / `csops_audittoken` | BSD syscall | **查询/标记代码签名状态与 entitlement** |
| 2 | `fcntl(F_ADDFILESIGS*)` | BSD | 为文件附着签名（dyld） |
| 3 | exec / `posix_spawn` | BSD | 触发 exec 侧 MAC + AMFI 标签更新 |
| 4 | `codesign` 工具 / 签名 blob | 用户态工具链 | 产出内核消费的签名 |
| 5 | Entitlement（嵌入签名） | 签名 blob | 能力声明；由 AMFI 解析为 OSEntitlements |
| 6 | amfid 端口 | Mach | 系统组件与闭源守护进程通信 |
| 7 | （内核）`amfi_t` / MAC 钩子 | 无稳定第三方 API | kext/KPI；第三方内核扩展不应依赖私有细节 |

---

## 4. Boot-arg、开发与强制开关（DEV/DEBUG 语境）

`kern_codesigning.c` 等路径解析（名称以树内为准；生产设备常忽略或被 TXM/AMFI 钳制）：

| 概念 | 作用 |
|------|------|
| `amfi` / `amfi_get_out_of_my_way` | 大幅放宽 AMFI |
| `amfi_allow_any_signature` | 允许任意签名（开发） |
| `amfi_unrestrict_task_for_pid` | 放宽 task_for_pid 相关限制 |
| `cs_enforcement_disable` | 关代码签名强制 |
| `security.mac.amfi.*` sysctl | **闭源 AMFI** 暴露；测试引用，实现不在本树 |
| 开源侧 | `vm.cs_*`、`security.codesigning.*` 等 |

注意：启动早期 `code_signing_configuration()` 可能先假定功能全开，**AMFI kext 上线后再 `disable_code_signing_feature()` 裁剪**。

---

## 5. 一次完整时序：从启动 App 到库校验

```text
1. 用户启动 App（已 codesign + entitlement）
2. 内核加载主执行体，解析 LC_CODE_SIGNATURE
3. ubc_cs_blob_add / 等价路径 → mac_vnode_check_signature
4. AMFI：验 CMS/证书或 Trust Cache → 设 CS_VALID、平台位、构建 OSEntitlements
5. mac_vnode_check_exec + cred label update → 进程带着签名状态与 entitlement 运行
6. dyld 加载 libc 等：F_ADDFILESIGS → 再次 check_signature
7. 若开启 Library Validation：mac_file_check_library_validation
8. 应用或系统调用 csops(CS_OPS_STATUS / ENTITLEMENTS_BLOB) 自省
9. 若某页哈希失配：cs_invalid_page → 清 CS_VALID → 可能 SIGKILL（CS_KILL）
```

Sandbox 侧（并行）：`libsecinit` 读到 `com.apple.security.app-sandbox` 后装 profile——**依赖 AMFI 保证 entitlement 未被伪造**。

---

## 6. 与其它安全机制的拼图

| 机制 | 和 AMFI 的关系 |
|------|----------------|
| **Sandbox** | AMFI 证明 entitlement；Sandbox 按 entitlement 约束行为 |
| **PPL / SPTM+TXM** | 把页表与部分签名元数据放到更高特权监视器；AMFI/CSM 协同 |
| **PAC / MTE** | 指针完整性 / 内存标签；AMFI 提供部分 **MTE 进程策略**查询（`has_mte_*`） |
| **SIP / CSR** | 平台完整性；与平台二进制、受保护路径相关 |
| **Quarantine** | 另一 MAC 策略；下载隔离属性 |

---

## 7. 开源树里能亲手验证的点

1. 读 `amfi.h` 的 `amfi_t` → 知道 XNU 向 AMFI 要什么。  
2. 在 `ubc_subr.c` 搜 `mac_vnode_check_signature` → 看附着签名后的裁决点。  
3. 读 `kern_proc.c` 的 `csops_internal` → 对照 `CS_OPS_*`。  
4. 读 `mac_policy.h` 里 `mpo_vnode_check_signature_t` 参数表。  
5. 读 `code_signing_internal.h` 的 `CONFIG_SPTM` / `PMAP_CS_PPL_MONITOR` 分支 → 监视器后端选择。  
6. 对照 Day 65 与安全白皮书中 `csops` 的 SEC 标记。

---

## 8. 小结（可背）

1. **XNU 实现签名 blob 存储、CS 标志强制、`csops` 与 MAC 分发；策略在 AMFI.kext。**  
2. 信任裁决主钩子是 **`mpo_vnode_check_signature`**；exec 与 LV 是另外两条强制带。  
3. 应用层主接口是 **`csops`** +（由 dyld 发起的）**`F_ADDFILESIGS*`**；entitlement 嵌在签名里。  
4. **`amfi_t`** 是内核其它子系统查询 entitlement / Trust Cache / MTE 策略的 KPI。  
5. 现代平台上 AMFI 与 **PPL 或 SPTM+TXM** 一起构成「谁能跑代码」的完整栈。

---

## 9. 参考

### 本树

- `libkern/libkern/amfi/amfi.h` / `libkern/amfi/amfi.c`  
- `bsd/sys/codesign.h` / `osfmk/kern/cs_blobs.h` / `bsd/sys/ubc_internal.h`  
- `bsd/kern/ubc_subr.c` / `kern_cs.c` / `kern_proc.c` / `kern_trustcache.c`  
- `bsd/kern/code_signing/{xnu,ppl,txm}.c`  
- `security/mac_vfs.c` / `mac_process.c` / `mac_policy.h`  

### 外部

- Apple Code Signing Guide / Notarization  
- 公开研究：AMFI、amfid、Trust Cache、Library Validation  

---

*文档生成说明：AMFI.kext / amfid / CoreTrust 策略实现无开源；标注「闭源侧」的内容基于 KPI、MAC 挂接点与公开资料的机制还原。*
