"""测试配置系统"""
import sys
sys.path.insert(0, 'D:/BaiduSyncdisk/Desktop/recall')

import db
import config

db.init_db()

print("=== 当前数据库配置 ===")
print(db.get_all_settings())

print("\n=== 测试修改 AI 配置 ===")
db.set_setting('AI_EXPLORE_INTERVAL', 999)
db.set_setting('AI_ENABLED', False)

print("AI_EXPLORE_INTERVAL:", db.get_setting('AI_EXPLORE_INTERVAL'))
print("AI_ENABLED:", db.get_setting('AI_ENABLED'))

print("\n=== 通过 config.get() 读取 ===")
print("AI_EXPLORE_INTERVAL:", config.get('AI_EXPLORE_INTERVAL'))
print("AI_ENABLED:", config.get('AI_ENABLED'))

print("\n=== 恢复默认值 ===")
db.set_setting('AI_EXPLORE_INTERVAL', 300)
db.set_setting('AI_ENABLED', True)
print("已恢复")
