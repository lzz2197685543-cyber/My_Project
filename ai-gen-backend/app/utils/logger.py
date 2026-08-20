"""
日志工具模块
"""
import logging
import sys
from datetime import datetime

from config.settings import settings


def get_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    获取日志器

    Args:
        name: 日志器名称
        log_level: 日志级别

    Returns:
        logging.Logger: 日志器实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # ========== 日志格式 ==========
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ========== 控制台输出 ==========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ========== 文件输出 ==========
    log_file = settings.LOGS_DIR / f"{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger