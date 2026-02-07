"""Screen Agent 配置"""
import os

# Recall 截图服务
RECALL_API_URL = os.getenv('RECALL_API_URL', 'http://127.0.0.1:5000')

# OpenClaw Hooks（暂时不用，dry_run 模式）
OPENCLAW_HOOKS_URL = os.getenv('OPENCLAW_HOOKS_URL', 'http://127.0.0.1:18789')
OPENCLAW_HOOK_TOKEN = os.getenv('OPENCLAW_HOOK_TOKEN', '')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL', 'wechat')
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# LLM 配置（复用 Recall 的 packyapi）
LLM_API_KEY = os.getenv('LLM_API_KEY', 'sk-ImDyKdFFrsYLWdiclrfUbT3Hkw7kGzZahJTjHrhxNRCNzzsQ')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://www.packyapi.com/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'claude-haiku-4-5-20251001')

# 行为配置
ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', '300'))  # 5 分钟
QUESTION_COOLDOWN = int(os.getenv('QUESTION_COOLDOWN', '600'))  # 10 分钟
MAX_SCREENSHOTS = int(os.getenv('MAX_SCREENSHOTS', '50'))

# 日志
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
