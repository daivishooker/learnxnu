# 03 · 签名与完整性

## 签名方案

| 方案 | 说明 |
|------|------|
| APK Signature Scheme v2/v3 | 现行默认；安装器校验整包摘要 |
| Play App Signing | Google 持最终分发密钥；你持 upload key |
| 自建分发 | 密钥进 HSM/密钥库；禁止进 git |

## 重打包如何被发现

攻击者改 DEX 后必须**重新签名** → 证书指纹变化。  
应用启动时读取自身签名证书，与**编译期嵌入的期望指纹**比对：

```text
PackageManager → SigningInfo → 证书 SHA-256 → 与 BuildConfig 期望值比较
```

不一致 → 本地降级 + 上报服务端。

## 安装来源

`InstallSourceInfo`（API 30+）可区分：

- Play 商店
- 企业 MDM
- 未知侧载

侧载不一定恶意（内测包），但应作为风险分因子。

## Play Integrity（推荐）

比本地指纹更强：由 Google 签发完整性令牌，服务端验证。  
本地签名校验适合无 Play 渠道或作为补充信号。

## 注意

- 多签名 / 轮换证书时要支持**指纹白名单**
- Debug 构建不要启用硬失败，否则开发体验崩坏
- 期望指纹用 CI 注入，避免手抄错
