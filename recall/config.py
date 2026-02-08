"""配置模块 - 支持数据库存储和热更新"""

# ============ 默认配置 ============
# 这些值作为初始化和回退使用

DEFAULT_SETTINGS = {
    # 截图设置
    'SCREENSHOT_DIR': 'screenshots',
    'CHANGE_THRESHOLD': 0.8,        # 像素变化阈值 (0-1)
    'FORCE_CAPTURE_INTERVAL': 300,  # 强制截图间隔（秒）
    'MIN_CAPTURE_INTERVAL': 10,     # 最小截图间隔（秒）
    'JPEG_QUALITY': 85,             # JPEG质量 (1-100)

    # GPU/OCR 设置
    'GPU_USAGE_THRESHOLD': 30,
    'OCR_BATCH_SIZE': 10,

    # 数据聚合
    'SIMILARITY_THRESHOLD': 0.9,
    'GROUP_TIME_WINDOW': 3600,

}


# ============ 配置读取函数 ============

def get(key: str, default=None):
    """从数据库获取配置值，支持热更新"""
    try:
        import db
        value = db.get_setting(key)
        if value is not None:
            return value
    except Exception:
        pass
    # 回退到默认值
    return DEFAULT_SETTINGS.get(key, default)


def get_all() -> dict:
    """获取所有配置（合并默认值和数据库值）"""
    result = DEFAULT_SETTINGS.copy()
    try:
        import db
        db_settings = db.get_all_settings()
        result.update(db_settings)
    except Exception:
        pass
    return result


def set(key: str, value):
    """设置配置值到数据库"""
    import db
    db.set_setting(key, value)


def set_all(settings: dict):
    """批量设置配置值"""
    import db
    db.set_all_settings(settings)


def init_defaults():
    """初始化默认配置到数据库（仅当配置不存在时）"""
    import db
    existing = db.get_all_settings()
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            db.set_setting(key, value)


# ============ 路径常量 ============
# SCREENSHOT_DIR 是路径常量，不需要热更新，保留为模块级变量
SCREENSHOT_DIR = DEFAULT_SETTINGS['SCREENSHOT_DIR']
