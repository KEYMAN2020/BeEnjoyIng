# 银发活力 uni-app 操作手册

> `/opt/drq/uniapp/`

---

## 一、项目结构

```
uniapp/
├── src/
│   ├── pages/           ← 15 个页面（源码）
│   ├── api/index.js     ← API 层（uni.request）
│   ├── stores/auth.js   ← Pinia 状态管理
│   ├── pages.json       ← 路由 + tabBar
│   ├── manifest.json    ← 应用配置（AppID 填这里）
│   ├── App.vue          ← 根组件
│   ├── main.js          ← 入口
│   └── uni.scss         ← 全局样式（rpx）
├── dist/build/
│   ├── h5/              ← H5 编译产物
│   └── mp-weixin/       ← 微信小程序编译产物
├── package.json
└── vite.config.js
```

---

## 二、编译命令

```bash
cd /opt/drq/uniapp

# H5 浏览器版（无需 AppID，改完码立刻看）
npx uni build -p h5

# 微信小程序版（需要 AppID）
npx uni build -p mp-weixin
```

---

## 三、三种调试方式

### 方式 1：H5 浏览器调试（推荐，零门槛）

```bash
cd /opt/drq/uniapp
npx uni build -p h5
cp -r dist/build/h5 /opt/silver-vitality/backend/backend/frontend_dist/h5
```
然后打开 `http://124.220.16.67:5000/h5/`

> 优点：不需要任何开发者工具、不需要 AppID、改完码 10 秒看效果  
> 限制：微信特有 API 不可用（但本项目用手机号登录，不影响）

### 方式 2：微信开发者工具（测试号模式）

1. 下载[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 编译：
```bash
cd /opt/drq/uniapp
npx uni build -p mp-weixin
```
3. 微信开发者工具 → 新建项目 → 选择「测试号」→ 导入目录 `dist/build/mp-weixin`

> 测试号模式不需要真实 AppID，大部分功能可调试。

### 方式 3：真机扫码预览（需要 AppID）

```bash
cd /opt/drq/uniapp
npx uni build -p mp-weixin
```
微信开发者工具 → 预览 → 生成二维码 → 手机微信扫码

---

## 四、拿到 AppID 后的操作

1. 在 `src/manifest.json` 的 `mp-weixin.appid` 填入 AppID
2. 重新编译：
```bash
cd /opt/drq/uniapp
npx uni build -p mp-weixin
```
3. 微信开发者工具 → 导入 `dist/build/mp-weixin` → 上传

---

## 五、后端 API 地址

API 地址硬编码在 `src/api/index.js` 第 2 行：

```javascript
const BASE = 'http://124.220.16.67:5000/api/v1'
```

*上线前需改为 HTTPS 域名，微信小程序要求域名 HTTPS + 已备案。*

---

## 六、改代码后的标准流程

```bash
# 1. 改代码（任意 .vue / .js / .css）
vim src/pages/xxx/xxx.vue

# 2. 编译 H5（浏览器看效果）
npx uni build -p h5
cp -r dist/build/h5 /opt/silver-vitality/backend/backend/frontend_dist/h5

# 3. 编译小程序（确认微信端也正常）
npx uni build -p mp-weixin

# 4. 用浏览器打开 http://124.220.16.67:5000/h5/ 验证
```

---

## 七、常见问题

| 问题 | 解决 |
|------|------|
| 构建报 `sass not found` | `npm install -D sass --legacy-peer-deps` |
| 构建报 `pinia not found` | `npm install pinia --legacy-peer-deps` |
| H5 页面空白 | 检查 API 地址是否可达：`curl http://124.220.16.67:5000/api/v1/activities/categories` |
| `<select>` 编译报错 | uni-app 不支持 HTML `<select>`，改用 `<picker>` |
| `localStorage` 报错 | 小程序端用 `uni.setStorageSync` 替代 |
