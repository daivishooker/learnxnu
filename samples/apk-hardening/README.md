# APK 加固样例代码

可复制到 Android 工程的**防御侧**片段，不是完整可编译 App。

## 目录

```
proguard-rules.pro          # R8 规则模板
app/build.gradle.kts        # minify / 指纹注入示例
app/src/main/java/.../      # Kotlin 运行时防护
app/src/main/cpp/           # Native 辅助
```

## 接入步骤

1. 合并 `proguard-rules.pro` 到你的规则文件
2. 按 `build.gradle.kts` 开启 minify，并用 CI 注入 `EXPECTED_CERT_SHA256`
3. 在 `Application.onCreate` 调用 `HardeningBootstrap.init(this)`
4. 按产品策略处理 `GuardResult`（上报 / 降级 / 阻断）

## 计算证书指纹（本机）

```bash
# 替换为你的 release 密钥库与别名
keytool -list -v -keystore release.jks -alias your_alias \
  | awk '/SHA256:/{print toupper($2)}' | tr -d ':'
```

将 64 位十六进制（无冒号）写入 `EXPECTED_CERT_SHA256`。
