# AGENT.md

## 流程

- 用户提出了需求，首先读取 `.agents/skills/l1/SKILL.md` ，然后按照此 skill 执行
- 用户未提出需求，仅发送了此文件，直接读取 `.agents/skills/l2/SKILL.md` ，然后按照此 skill 去领取任务执行。不要再次询问用户是否有需求。

## 行为原则

- 如果遇到环境问题，或者反复出错，首先查询 `doc/notice.md` 有没有解决方案。
- 如果一个问题反复调试，或者工具调用出现问题，解决后记录到 `doc/notice.md` 中

## skill/角色

- `/l1`：需求澄清、方案设计、任务拆解、与用户确认。
- `/l2`：任务认领、开发实现、测试、代码审查、合并与收口。

## 文档目录

- doc/env.md: 开发环境
- doc/framework.md: 项目整体架构
- doc/notice.md: 项目踩坑记录
- tasks/: agent 任务规划
- .agents/skills: skill 存放位置

## Git Worktree 规则

- 并行开发使用 `git worktree`。
- 每个活跃任务绑定一个分支和一个 worktree 路径，禁止多个任务复用同一工作目录。
- 主分支仅用于任务创建、状态同步、合并，不直接进行并行任务实现。
- 使用 zzf621 为名字进行提交
