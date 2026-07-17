# APK 加固样例

## 主路径：已有 APK

对编好的包加固（不改工程）：

→ **[`pipeline/`](pipeline/)** · [`pipeline/README.md`](pipeline/README.md)

```bash
cd pipeline
./harden-existing-apk.sh \
  --apk /path/to/existing.apk \
  --keystore /path/to/release.jks \
  --alias your_alias \
  --storepass '***' \
  --cert-sha256 '<证书SHA256>' \
  --out /path/to/hardened.apk
```

总览文档：[docs/android/APK_HARDENING.md](../../docs/android/APK_HARDENING.md)

## 补充：源码期（有工程时）

```
proguard-rules.pro          # R8 规则模板
app/build.gradle.kts        # minify / 指纹注入示例
app/src/main/java/.../      # Kotlin 运行时防护（工程内接入）
app/src/main/cpp/           # Native 辅助
```

有源码时建议：**先 R8 出包 → 再跑 pipeline / 商业壳**。

## 计算证书指纹

```bash
keytool -list -v -keystore release.jks -alias your_alias \
  | awk -F'SHA256: ' '/SHA256:/{print $2}' | tr -d ':' | tr 'a-f' 'A-F'
```
