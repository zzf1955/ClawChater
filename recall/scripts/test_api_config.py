"""测试 API 保存配置"""
import sys
sys.path.insert(0, 'D:/BaiduSyncdisk/Desktop/recall')

import db
import config

db.init_db()

print("=== 保存前 ===")
print(config.get_all())

# 模拟前端发送的配置
frontend_config = {
    'CHANGE_THRESHOLD': 0.5,
    'FORCE_CAPTURE_INTERVAL': 600,
    'MIN_CAPTURE_INTERVAL': 20,
    'JPEG_QUALITY': 90,
    'GPU_USAGE_THRESHOLD': 50,
    'OCR_BATCH_SIZE': 20,
    'AI_EXPLORE_INTERVAL': 120,
    'AI_MIN_QUESTION_INTERVAL': 300,
    'AI_ENABLED': False
}

print("\n=== 模拟前端保存 ===")
config.set_all(frontend_config)

print("\n=== 保存后 ===")
print(config.get_all())

print("\n=== 恢复默认值 ===")
config.set_all(config.DEFAULT_SETTINGS)
print("已恢复")
