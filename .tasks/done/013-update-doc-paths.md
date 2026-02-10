---
id: "013"
title: "更新文档中的旧路径引用"
priority: low
depends_on: ["012"]
module: recall
branch: main
estimated_scope: small
---

## 背景

项目从 `D:/BaiduSyncdisk/Desktop/recall` 迁移到了 `D:/BaiduSyncdisk/Desktop/ClawChater/recall`，但部分文档中的路径引用未更新。

## 技术方案

### 1. 更新 recall/CLAUDE.md

npm 命令中的路径需要更新：
```
# 旧
npm run dev --prefix "D:/BaiduSyncdisk/Desktop/recall/web/frontend"

# 新
npm run dev --prefix "D:/BaiduSyncdisk/Desktop/ClawChater/recall/web/frontend"
```

同样更新：
- `npm run build` 命令的路径
- Android 编译命令的路径
- adb install 命令的路径

### 2. 检查其他文档

- `recall/doc/framework.md`
- `recall/doc/REQUIREMENTS.md`
- `recall/doc/BUGS.md`
- `CLAUDE.md`（根目录）

搜索所有包含 `Desktop/recall` 但不包含 `ClawChater` 的路径引用。

## 验收标准

- [x] 所有文档中的路径引用已更新为当前项目路径
- [x] 无残留的旧路径 `Desktop/recall`（不含 ClawChater）

## 测试要求

- [x] 全局搜索确认无旧路径残留

---
completed_by: w-7e3b
completed_at: 2026-02-08T12:25:00+08:00
commit: 3b6400e
files_changed:
  - recall/CLAUDE.md
test_result: "grep confirmed no old paths"
---
