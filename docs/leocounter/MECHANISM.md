# LeoCounter 机制说明

源码：[`projects/leocounter/`](../../projects/leocounter/)（上游 [anacforcelli/leocounter](https://github.com/anacforcelli/leocounter)）

一句话：一个很轻的 **Express 静态站点壳**，主题是「Leo 从卡包里抽出各英雄多少次」；**计数逻辑尚未写完**。

---

## 1. 整体结构

```text
projects/leocounter/
├── index.js          # Node/Express 入口：静态托管 + 监听 3333
├── package.json      # 依赖 express（写在 devDependencies）
├── public/
│   ├── index.html    # 页面：标题 + 占位 contador
│   ├── app.js        # 前端脚本：heroes 数组（未完成）
│   └── styles.css    # 简单样式（Bangers 字体）
└── images/
    └── favicon.ico
```

```text
浏览器
  │  GET /
  ▼
Express (index.js)
  ├─ express.static('public')  → /app.js /styles.css /images/...
  └─ app.get('/')              → 意图：送 index.html（当前实现有 bug）
```

---

## 2. 服务器：`index.js`

```js
app.use(express.static(path.join(__dirname, 'public')))
app.get('/', (req, res) => {
    res.sendFile(`${__dirname}/public/index.html`);
    res.send({ message: 'Olá Muleteiro!' });  // 问题：响应已开始后又 send
});
app.listen(3333, ...)
```

机制要点：

| 点 | 含义 |
|----|------|
| `express.static` | 把 `public/` 映射成 URL 根路径下的静态文件 |
| 端口 `3333` | 本地访问 `http://localhost:3333` |
| `/` 路由 | 想回 HTML，但又 `res.send(JSON)`，**同一次响应写两次** → 易报错/行为未定义 |

学习时先把「静态中间件 vs 路由 handler」分清：静态文件不经过你的 `app.get('/')` 业务逻辑（除非路径正好撞上）。

---

## 3. 页面：`public/index.html`

- 标题：`Leo Counter 1.0`
- 副标题（葡语）：*Quantas vezes o Leo tirou cada heroi da pasta?*  
  → 「Leo 从卡包里抽出每个英雄多少次？」
- 引入 `/app.js`、`/styles.css`
- `<div name="contador">` 只有占位文字 `contador`，**还没有按英雄渲染列表**

---

## 4. 前端数据：`public/app.js`

- 定义 `heroes` 字符串数组（Flesh and Blood 风格英雄名 + 一些玩笑名）
- **当前文件不完整**：
  - `"Florian"` 后缺逗号 → 语法错误，脚本无法执行
  - 后面大量空行，没有 `DOMContentLoaded`、没有渲染、没有 click/+1
- 意图上：应以 `heroes` 为目录，为每个英雄维护一个计数

---

## 5. 还缺的「计数机制」（设计推演）

完整 LeoCounter 通常需要：

```text
状态： counts = { "Arakni": 0, "Azalea": 0, ... }

读：页面加载 → 渲染每个英雄 + 当前次数
写：点 +1 → counts[hero]++ → 更新 DOM
（可选）持久化：localStorage 或 POST 到服务器写 JSON
```

可选后端 API（源码里**还没有**）：

| 方法 | 路径 | 作用 |
|------|------|------|
| GET | `/api/counts` | 读取全部计数 |
| POST | `/api/counts/:hero` | 某英雄 +1 |
| PUT | `/api/counts` | 整体覆盖保存 |

现在只有静态壳，计数状态机尚未落地。

---

## 6. 和 XNU 学习线的关系

这是一条**独立小板**：Web/Express 小应用机制，不替换 Day N syscall 日程。  
看板见 [LEARNING_BOARD.md](LEARNING_BOARD.md)。

---

## 7. 本地跑（学习用）

```bash
cd projects/leocounter
npm install
node index.js
# 浏览器打开 http://localhost:3333
```

若 `/` 报错，先注释掉第二次 `res.send`，或只保留 `res.sendFile`。
