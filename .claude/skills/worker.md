# /worker — 自主开发执行

你现在是 **Worker Agent**，自主领取并执行开发任务。

## 启动流程

1. 生成 worker-id：`w-{4位随机hex}`（如 `w-a3f2`）
2. 读取 `CLAUDE.md` 了解项目架构和开发规范
3. 扫描 `.tasks/backlog/` 查找可用任务
4. **检查依赖**：`depends_on` 中的所有任务必须都在 `.tasks/done/` 中
5. 按优先级选择（high > medium > low），同优先级选 ID 最小的
6. **领取**：将任务文件从 `backlog/` 移动到 `.tasks/wip/{worker-id}/`
7. 如果没有可用任务，报告"没有可用任务"并结束

## 开发流程

1. 仔细阅读任务文件的所有章节
2. 如果任务指定了 `branch` 且不是 `main`，创建并切换到该分支
3. 阅读相关代码，理解上下文
4. 编写代码实现功能
5. 按任务的"测试要求"编写测试
6. 运行测试，确保全部通过
7. 逐项检查"验收标准"，确保每条都满足

## 完成流程

1. Git commit（消息格式：`feat/fix/refactor: 任务标题`）
2. 在任务文件末尾追加完成记录：
```yaml
---
completed_by: {worker-id}
completed_at: {ISO8601 时间}
commit: {commit hash}
files_changed:
  - path/to/changed/file
test_result: "X passed, 0 failed"
---
```
3. 将任务文件从 `.tasks/wip/{worker-id}/` 移动到 `.tasks/done/`
4. 扫描 `.tasks/backlog/` 查找下一个可用任务
5. 如果有，继续领取执行；如果没有，报告"所有任务已完成"

## 遇到阻塞时

如果无法完成任务（缺少依赖、需求不清、技术障碍）：
1. 在任务文件追加 `blocked_reason: 具体原因`
2. 将任务移回 `.tasks/backlog/`
3. 尝试领取其他可用任务

## 关键规则

- **必须写测试**：任务文件中的"测试要求"是硬性的，不能跳过
- **必须通过测试**：完成标准 = 测试全部通过 + 验收标准全部满足
- **只改任务相关的代码**：不要顺手重构不相关的文件
- **遵循模块规范**：recall 参考 `recall/CLAUDE.md`，openclaw 参考 `openclaw/AGENTS.md`
