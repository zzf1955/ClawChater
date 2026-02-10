---
id: "005"
title: "清理前端 — 删除 AI 聊天路由和导航"
priority: medium
depends_on: ["001"]
module: recall
branch: main
estimated_scope: small
---

## 背景

前端 App.vue 和 Sidebar.vue 中包含 AI 聊天和 AI 日志的路由/导航，api/index.js 中包含聊天相关 API 调用，需要清理。

## 技术方案

### 修改 `recall/web/frontend/src/App.vue`
- 删除 ChatView 和 AILogView 的 import
- 删除对应的路由/组件切换逻辑

### 修改 `recall/web/frontend/src/components/Sidebar.vue`
- 删除"AI 助手"和"AI 日志"导航项

### 修改 `recall/web/frontend/src/api/index.js`
- 删除所有聊天/对话/AI 相关 API 函数：
  - `getConversations`, `createConversation`, `deleteConversation`, `setActiveConversation`
  - `sendMessage`, `getAIMessages`, `getAIHistory`, `getAILogs`

### 修改 `recall/web/frontend/src/views/ConfigView.vue`
- 删除 AI 设置分组（探索开关/间隔等）

## 验收标准

- [x] 前端只有"截图浏览"和"配置"两个页面
- [x] 侧边栏无 AI 相关导航
- [x] api/index.js 无聊天/AI 相关函数
- [x] ConfigView 无 AI 设置项

## 测试要求

- [x] `npm run build --prefix "D:/BaiduSyncdisk/Desktop/ClawChater/recall/web/frontend"` 构建成功无报错

---
completed_by: w-d4a1
completed_at: 2026-02-08T00:00:00+08:00
commit: 80946c2
files_changed:
  - recall/web/frontend/src/App.vue
  - recall/web/frontend/src/components/Sidebar.vue
  - recall/web/frontend/src/api/index.js
  - recall/web/frontend/src/views/ConfigView.vue
test_result: "npm run build 成功, 0 errors"
---
