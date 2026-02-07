# Recall

Windows Recall 的本地开源替代品，结合 LLM 聊天功能。

## 项目概述

一个跨平台的个人数字记忆助手：
- **自动记录**：后台截图 + OCR 文字提取
- **智能检索**：通过 LLM 对话查询历史记录
- **多端同步**：PC + Android 数据统一管理

## 功能模块

### PC 端（已完成）
- [x] 屏幕变化检测 + 自动截图
- [x] OCR 文字识别（GPU 加速）
- [x] 系统托盘 + Web GUI
- [x] 截图浏览、搜索、预览

### Android 端（基础框架已完成）
- [x] 后台截图服务（MediaProjection + 前台服务）
- [x] 屏幕变化检测（缩略图像素对比）
- [x] 本地存储（Pictures/Recall/YYYY-MM-DD/HH/）
- [x] 设置界面（截图间隔、变化阈值、强制间隔）
- [ ] WiFi 同步到 PC

### LLM 聊天（开发中）
- [ ] 接入 LLM API
- [ ] 基于截图/OCR 内容的问答
- [ ] 时间线回溯查询

## 技术栈

| 模块 | 技术 |
|------|------|
| PC 后端 | Python 3.11, Flask, SQLite |
| PC 前端 | Vue 3, Vite, Tailwind CSS |
| PC GUI | PyWebView, pystray |
| OCR | RapidOCR + onnxruntime-gpu |
| Android | Kotlin, MediaProjection API |
| LLM | 待定 |

## 快速开始

### PC 端
```bash
# 安装依赖
conda run -n recall pip install -r requirements.txt

# 启动应用
conda run -n recall python main.py
```

### 前端开发
```bash
cd web/frontend
npm install
npm run dev    # 开发模式
npm run build  # 构建
```

### Android 端
```bash
# 构建 APK
cd android/RecallMobile
./gradlew assembleDebug

# 安装到设备
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

**使用说明：**
1. 打开 RecallMobile 应用
2. 点击"开始截图"按钮
3. 授权屏幕录制权限（选择"整个屏幕"）
4. 应用会在后台定期截图，截图保存在 `Pictures/Recall/` 目录
5. 点击"设置"可调整截图间隔、变化阈值等参数

**要求：**
- Android 10 (API 29) 及以上
- JDK 17（构建时需要）

## 文档

- [需求单](REQUIREMENTS.md) - 功能需求和待办事项
- [更新日志](CHANGELOG.md) - 版本历史
