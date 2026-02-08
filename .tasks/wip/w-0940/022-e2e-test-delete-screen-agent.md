---
id: "022"
title: "端到端集成测试 + 删除 Screen Agent"
priority: medium
depends_on: ["020", "021"]
module: [openclaw, recall]
branch: main
estimated_scope: medium
---

## 背景

所有组件就绪后，需要端到端验证完整流程，确认无误后删除已废弃的 screen-agent/ 目录。

## 技术方案

### 1. 测试场景

**场景 A：有趣变化 → 触发聊天**
1. 确保 Recall 中有 OCR 数据（正常使用即可）
2. 等待 Cron 触发 Thinking Agent
3. 验证 Thinking Agent 正确分析并写入 intent
4. 验证 Chat Agent 被触发并在 Telegram 发出消息
5. 回复消息，验证 facts 被提取

**场景 B：无趣 → 静默**
1. Recall 中只有持续的同类 OCR 数据
2. Cron 触发 Thinking Agent
3. 验证 Thinking Agent 判断不有趣，不写 intent
4. 验证 Chat Agent 未被触发

**场景 C：摘要生成**
1. 运行超过 30 分钟
2. 验证 Thinking Agent 生成摘要
3. 验证摘要通过 API 写入 Recall DB
4. 查询 GET /api/summaries 确认数据

### 2. 验证清单

- [ ] Cron 按时触发（查看 OpenClaw 日志）
- [ ] Thinking Agent 成功调用 Recall API
- [ ] intents.json 格式正确
- [ ] Chat Agent 在 Telegram 发出自然的消息
- [ ] facts.json 正确积累
- [ ] summaries 正确写入 Recall DB
- [ ] 冷却机制生效（Cron interval 天然控制）
- [ ] 错误处理：Recall 不可用时不崩溃

### 3. 删除 Screen Agent

确认端到端测试通过后：
1. 删除 `screen-agent/` 整个目录
2. 更新 `CLAUDE.md` 中的架构描述
3. 更新模块速查表（移除 screen-agent 行）
4. 更新架构图（Recall → OpenClaw 直连）

### 4. 更新文档

CLAUDE.md 中的架构图更新为：
```
Recall (:5000) ──HTTP API──▶ OpenClaw (:18789)
截图+OCR+存储                 Thinking Agent (分析决策)
(PC + Android)                Chat Agent (Telegram 聊天)
```

## 验收标准

- [ ] 三个测试场景全部通过
- [ ] Telegram 消息风格自然（人工审核）
- [ ] 摘要正确写入 Recall DB
- [ ] facts.json 正确积累新信息
- [ ] screen-agent/ 目录已删除
- [ ] CLAUDE.md 文档已更新
- [ ] 连续运行 1 小时无异常

## 测试要求

- [ ] 手动端到端测试：完整 Cron → Thinking → Chat → Telegram 流程
- [ ] 验证 Recall API 不可用时的降级行为
- [ ] 验证 facts.json 并发写入安全性
