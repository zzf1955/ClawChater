---
id: "023"
title: "修复 OCR Worker GPU 自我阻塞问题"
priority: high
depends_on: []
module: recall
branch: main
estimated_scope: small
---

## 背景

OCR Worker 的 GPU 忙碌检测存在自我阻塞问题：OCR 推理本身会让 GPU 使用率超过阈值（默认 30%），导致每处理 1-2 张图片就触发 "GPU忙碌，暂停OCR"，等待 5 秒后才继续。这使得 OCR 处理速度远低于截图速度，pending 积压越来越多。

根本原因：`_worker_loop` 在 batch 内逐张检查 `is_gpu_idle()`，而 OCR 自身就是 GPU 的主要消费者。

## 技术方案

### 修改 `recall/ocr_worker.py`

**`_worker_loop` 方法**：
- 保留 batch 开始前的 GPU 检测（此时 OCR 没在跑，能准确反映其他程序的 GPU 使用）
- 移除 batch 内逐张处理时的 GPU 检测（第 112-114 行）
- batch 处理完后自然回到循环顶部，再次检测 GPU

改动前：
```python
for item in pending:
    if not self._running:
        break
    if not is_gpu_idle(...):  # ← 这里会被 OCR 自身阻塞
        log.info("GPU忙碌，暂停OCR")
        break
    self.process_one(item['id'], item['path'])
```

改动后：
```python
for item in pending:
    if not self._running:
        break
    self.process_one(item['id'], item['path'])
```

### 不需要修改的文件
- `recall/utils/gpu.py` — GPU 检测逻辑本身没问题
- `recall/config.py` — 阈值配置保持不变

## 验收标准

- [ ] OCR Worker 能连续处理整个 batch 而不被自身 GPU 使用阻塞
- [ ] 当其他程序（如游戏）占用 GPU 时，OCR 仍能在 batch 间隔正确暂停
- [ ] 日志中不再出现每 1-2 张就 "GPU忙碌，暂停OCR" 的模式
- [ ] pending 积压能被正常消化

## 测试要求

- [ ] 启动 Recall，观察日志确认 OCR 能连续处理多张图片
- [ ] 确认 batch 处理完后仍会检查 GPU 使用率
