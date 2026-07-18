# Android APK 加固指南（已有 APK）

目标：**对已经编好的 APK** 做加固——不改源码工程，输入 `app.apk`，输出可安装的加固包。

配套：

- 流水线：[`samples/apk-hardening/pipeline/`](../../samples/apk-hardening/pipeline/)
- 笔记：[`notes/android-apk-hardening/`](../../notes/android-apk-hardening/)
- 源码级补充（可选）：[`samples/apk-hardening/app/`](../../samples/apk-hardening/app/)

---

## 两种路径

| 路径 | 适用 | 本仓库 |
|------|------|--------|
| **A. 已有 APK 加固** | 只有 Release APK / 外包交付包 / 不能改工程 | **主路径**：`pipeline/harden-existing-apk.sh` |
| B. 源码期加固 | 能改 Gradle | R8 + 源码检测（`app/` 样例） |

商业壳（乐固、梆梆、爱加密、360 等）也是 **A 类**：上传/喂入 APK → 拿回加固包 → 按厂商要求重签。

---

## 推荐流程（已有 APK）

```text
原 APK ──►（可选）商业壳加固 ──► 注入运行时防护 / 仅重签 ──► zipalign + 签名 ──► 冒烟
              │                      │
              │                      └─ 本仓库 DIY：Application 壳（签名校验 + 反调试信号）
              └─ 厂商：DEX/SO 加密、反 Dump（深度防护）
```

### 1）DIY 轻量加固（本仓库流水线）

```bash
cd samples/apk-hardening/pipeline

./harden-existing-apk.sh \
  --apk /path/to/app-release.apk \
  --keystore /path/to/release.jks \
  --alias your_alias \
  --storepass '***' \
  --keypass '***' \
  --cert-sha256 '你的证书SHA256无冒号大写' \
  --out /path/to/app-hardened.apk
```

脚本会：

1. `apktool d` 反编译  
2. 注入 `com.hardening.shell.HardeningApp`  
3. 改 `AndroidManifest.xml`：用壳 `Application` 包裹原 `Application`  
4. `apktool b` 回编  
5. `zipalign`（若可用）+ `apksigner`/`jarsigner` 重签  

### 2）商业壳 + 本仓库重签

```bash
# 先在厂商控制台/CLI 加固，得到 protected.apk
./harden-existing-apk.sh \
  --resign-only \
  --apk /path/to/protected.apk \
  --keystore /path/to/release.jks \
  --alias your_alias \
  --storepass '***' \
  --keypass '***' \
  --out /path/to/app-signed.apk
```

---

## 加固能力对照

| 手段 | 已有 APK 可否 | 说明 |
|------|----------------|------|
| 商业 DEX/SO 壳 | ✅ | 深度防护首选 |
| 注入 Application 壳 | ✅ | 本流水线：签名校验、调试信号 |
| 重签 v2/v3 | ✅ | 加固后几乎总要重签 |
| R8 混淆 | ❌（需源码构建） | 应在出包前完成 |
| Play Integrity | 半 | 需源码接入 API；壳不替代 |

原则：**有源码先 R8 再出包；无源码或已出包 → 商业壳 / 本流水线；密钥永不进 git。**

---

## 明确不做

- 不提供破解、脱壳、绕过他人加固的步骤  
- 不面向恶意软件分发  
- 仅服务**自有 APK** 的发布防护  

---

## 延伸阅读

- [Sign your app](https://developer.android.com/studio/publish/app-signing)
- [Play Integrity API](https://developer.android.com/google/play/integrity)
- 流水线说明：[`samples/apk-hardening/pipeline/README.md`](../../samples/apk-hardening/pipeline/README.md)
