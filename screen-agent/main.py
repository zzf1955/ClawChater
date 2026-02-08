"""Screen Agent 主入口 — 后台持续浏览截图数据库，两步编排 Thinking + Chat"""
import time
import logging
from datetime import datetime

import config
from recall_client import RecallClient
from openclaw_client import OpenClawClient

# 日志配置
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger('screen-agent')


def main():
    log.info("Screen Agent 启动")
    log.info(f"Recall API: {config.RECALL_API_URL}")
    log.info(f"DRY_RUN: {config.DRY_RUN}")
    log.info(f"分析间隔: {config.ANALYSIS_INTERVAL}s")
    log.info(f"提问冷却: {config.QUESTION_COOLDOWN}s")

    # 初始化客户端
    recall = RecallClient(config.RECALL_API_URL)
    openclaw = OpenClawClient(
        config.OPENCLAW_HOOKS_URL,
        config.OPENCLAW_HOOK_TOKEN,
        dry_run=config.DRY_RUN
    )

    last_check_time = None
    last_heartbeat_time = 0

    log.info("进入主循环...")

    try:
        while True:
            now = time.time()

            # 检查冷却
            if now - last_heartbeat_time < config.QUESTION_COOLDOWN:
                remaining = int(config.QUESTION_COOLDOWN - (now - last_heartbeat_time))
                log.debug(f"冷却中，剩余 {remaining}s")
                time.sleep(min(60, remaining))
                continue

            # 从 Recall 拉取最新截图摘要
            log.info("拉取最新截图...")
            screenshots = recall.get_recent(
                since=last_check_time,
                limit=config.MAX_SCREENSHOTS
            )
            last_check_time = datetime.now().isoformat()

            if not screenshots:
                log.info("没有新截图")
                time.sleep(config.ANALYSIS_INTERVAL)
                continue

            log.info(f"获取到 {len(screenshots)} 条截图摘要")

            # 两步编排：Thinking → 等待 → Chat
            log.info("开始 Heartbeat 流程...")
            success = openclaw.run_heartbeat(
                screenshots,
                channel=config.TARGET_CHANNEL,
                to=config.TARGET_USER_ID
            )
            if success:
                last_heartbeat_time = time.time()
                log.info("Heartbeat 完成")

            # 等待下一轮
            time.sleep(config.ANALYSIS_INTERVAL)

    except KeyboardInterrupt:
        log.info("Screen Agent 停止")


if __name__ == '__main__':
    main()
