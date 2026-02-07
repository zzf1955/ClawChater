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

    # CuriousAI 配置
    'AI_EXPLORE_INTERVAL': 300,      # 探索间隔（秒）
    'AI_MIN_QUESTION_INTERVAL': 600, # 最小提问间隔（秒）
    'AI_ENABLED': True,
}

# LLM API 配置（敏感信息，不存数据库）
LLM_API_KEY = "sk-ImDyKdFFrsYLWdiclrfUbT3Hkw7kGzZahJTjHrhxNRCNzzsQ"
LLM_BASE_URL = "https://www.packyapi.com/v1"
LLM_MODEL = "claude-haiku-4-5-20251001"


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


# ============ 兼容旧代码的模块级变量 ============
# 这些变量在模块加载时初始化，不支持热更新
# 新代码应使用 config.get('KEY') 方式读取

SCREENSHOT_DIR = DEFAULT_SETTINGS['SCREENSHOT_DIR']
CHANGE_THRESHOLD = 0.8
FORCE_CAPTURE_INTERVAL = 1111
MIN_CAPTURE_INTERVAL = 5
JPEG_QUALITY = 100
GPU_USAGE_THRESHOLD = 30
OCR_BATCH_SIZE = 10
SIMILARITY_THRESHOLD = DEFAULT_SETTINGS['SIMILARITY_THRESHOLD']
GROUP_TIME_WINDOW = DEFAULT_SETTINGS['GROUP_TIME_WINDOW']
AI_EXPLORE_INTERVAL = 300
AI_MIN_QUESTION_INTERVAL = 600
AI_ENABLED = True
