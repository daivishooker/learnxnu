# APK 加固发布检查清单

## 构建

- [ ] `release` 开启 `minifyEnabled` + `shrinkResources`
- [ ] `proguard-rules.pro` 已审；第三方 keep 来自官方
- [ ] `mapping.txt` / `seeds.txt` 已归档（版本号对应）
- [ ] Release 包用 jadx 抽查：核心业务类已混淆

## 签名与分发

- [ ] 使用独立 upload key；密钥不在仓库
- [ ] 启用 v2/v3（及需要时的 v4）签名
- [ ] 若走 Play：已开启 Play App Signing
- [ ] 渠道包签名与指纹白名单一致

## 运行时

- [ ] Debug 构建不启用硬失败检测
- [ ] 签名校验期望指纹由 CI 注入
- [ ] 风险事件可上报服务端
- [ ] 敏感 API 有服务端二次鉴权

## Native / 壳（如有）

- [ ] `.so` 已 strip
- [ ] 加固后在真机矩阵冒烟（冷启动、支付、推送、升级）
- [ ] 加固工具版本锁定进 CI

## 合规

- [ ] 隐私政策与实际采集一致（含完整性/设备信号）
- [ ] 无多余高危权限
