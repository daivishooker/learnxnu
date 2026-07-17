# LeoCounter 学习看板

仓库源码（vendored）：[`projects/leocounter/`](../../projects/leocounter/)  
上游：https://github.com/anacforcelli/leocounter  
机制说明：[MECHANISM.md](MECHANISM.md)

状态图例：`[ ]` 待学 · `[~]` 进行中 · `[x]` 完成

---

## Backlog（待办）

- [ ] 跑通本地：`npm install` → `node index.js` → 打开 `http://localhost:3333`
- [ ] 读懂 Express 静态资源路径（`public/`）
- [ ] 标出 `index.js` 里 `/` 路由的双 `res.send*` 问题
- [ ] 读懂 `public/app.js` 英雄列表的数据模型意图
- [ ] 画出「浏览器 ↔ Express ↔ 静态文件」请求链
- [ ] 设想计数器状态应存在哪（内存 / localStorage / 文件 / DB）
- [ ] 补齐前端：每个英雄一行 + `+1` 按钮 + 显示次数
- [ ] （可选）加 API：`GET/POST /api/counts`
- [ ] （可选）持久化 counts 到 JSON 文件

## Doing（进行中）

- [~] 开板：机制文档 + 源码入库

## Done（已完成）

- [x] 定位上游仓库并 vendored 到 `projects/leocounter/`
- [x] 写出当前机制与缺口说明

---

## 建议学习顺序（一天可走完）

1. **服务器壳** — `index.js`  
2. **页面骨架** — `public/index.html` + `styles.css`  
3. **数据意图** — `public/app.js` 的 `heroes`  
4. **缺口推演** — 计数状态机还缺什么  
5. **小改动实验** — 先修语法/路由，再画最小可点计数 UI
