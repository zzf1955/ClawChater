"""测试配置系统"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import config

db.init_db()

print("=== 当前数据库配置 ===")
print(db.get_all_settings())

print("\n=== 通过 config.get() 读取 ===")
for key in config.DEFAULT_SETTINGS:
    print(f"{key}: {config.get(key)}")

print("\n=== 测试修改配置 ===")
db.set_setting('JPEG_QUALITY', 90)
print("JPEG_QUALITY:", config.get('JPEG_QUALITY'))

print("\n=== 恢复默认值 ===")
db.set_setting('JPEG_QUALITY', config.DEFAULT_SETTINGS['JPEG_QUALITY'])
print("已恢复")
