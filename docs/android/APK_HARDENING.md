# Android APK 加固指南

面向**自有应用**的发布前防护：提高逆向、篡改、调试的成本，而不是追求“绝对不可破解”。

配套笔记：[`notes/android-apk-hardening/`](../../notes/android-apk-hardening/)  
可复用样例：[`samples/apk-hardening/`](../../samples/apk-hardening/)

---

## 加固分层

| 层级 | 手段 | 作用 | 成本 |
|------|------|------|------|
| 构建 | R8/ProGuard 混淆、资源收缩 | 抹符号、缩体积、抬静态分析成本 | 低 |
| 签名 | v2/v3/v4、密钥托管、Play App Signing | 防二次打包冒充 | 低 |
| 完整性 | 签名校验、安装源校验 | 发现被重打包/非官方渠道 | 中 |
| 运行时 | 反调试、Root/模拟器检测 | 抬动态分析成本 | 中 |
| 资产 | 字符串/配置加密、密钥勿硬编码 | 降低明文泄露 | 中 |
| Native | NDK 关键逻辑、`.so` 符号剥离 | 保护核心算法 | 中高 |
| 商业壳 | 腾讯乐固、梆梆、爱加密、360 加固等 | DEX/SO 加密、反 Dump | 高（授权） |

原则：**先做构建与签名基线，再加运行时检测；核心密钥放服务端或硬件密钥库。**

---

## 推荐落地顺序

1. **Release 开启 R8**（混淆 + 收缩 + 优化）
2. **正式签名**（上传密钥与签名密钥分离；优先 Play App Signing）
3. **接入签名校验**（启动时比对证书指纹）
4. **敏感逻辑下沉**（NDK / 服务端；客户端只做会话态）
5. **按需加反调试 / Root 检测**（误报要可降级，勿一刀切崩进程）
6. **高价值 App 再上商业加固**（选与业务合规、可过审的方案）

---

## 本仓库样例覆盖

| 文件 | 内容 |
|------|------|
| `samples/apk-hardening/proguard-rules.pro` | R8 常用规则模板 |
| `samples/apk-hardening/app/build.gradle.kts` | minify / shrink 配置片段 |
| `IntegrityGuard.kt` | 签名指纹校验 |
| `RuntimeGuard.kt` | 调试器 / TracerPid / 可疑安装源 |
| `native-guard.cpp` | 轻量 native 完整性辅助 |
| `notes/android-apk-hardening/*.md` | 原理与坑点 |

---

## 明确不做

- 不提供破解他人加固包、脱壳、绕过版权保护的步骤
- 不写可用于恶意软件分发的加壳流水线
- 运行时检测仅作**自有 App 防护**参考，需结合产品体验与误报策略

---

## 延伸阅读（官方）

- [Shrink, obfuscate, and optimize your app](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)
- [Sign your app](https://developer.android.com/studio/publish/app-signing)
- [Play Integrity API](https://developer.android.com/google/play/integrity)
