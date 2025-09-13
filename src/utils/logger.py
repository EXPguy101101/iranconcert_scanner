# -*- coding: utf-8 -*-
"""
Logger Module
سیستم لاگ‌گیری یکپارچه برای پروژه

این ماژول یه logger ساده و کاربردی ارائه می‌ده که می‌تونه هم روی کنسول و هم توی فایل لاگ بگیره
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """
    کلاس Logger برای مدیریت لاگ‌ها

    این کلاس یه wrapper ساده روی logging استاندارد پایتون هست که کارش رو راحت‌تر می‌کنه
    """

    def __init__(
        self,
        name: str = "IranConcert",
        log_file: Optional[str] = None,
        console_level: str = "INFO",
        file_level: str = "DEBUG",
    ):
        """
        راه‌اندازی logger

        Args:
            name: اسم logger (معمولاً اسم ماژول یا کلاس)
            log_file: مسیر فایل لاگ (اختیاری)
            console_level: سطح لاگ برای کنسول
            file_level: سطح لاگ برای فایل
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # پاک کردن handler های قبلی تا duplicate نشه
        self.logger.handlers.clear()

        # رنگ‌های ANSI برای console
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                "DEBUG": "\033[36m",  # Cyan
                "INFO": "\033[32m",  # Green
                "WARNING": "\033[33m",  # Yellow
                "ERROR": "\033[31m",  # Red
                "CRITICAL": "\033[35m",  # Magenta
            }
            RESET = "\033[0m"

            def format(self, record):
                color = self.COLORS.get(record.levelname, self.RESET)
                record.levelname = f"{color}{record.levelname}{self.RESET}"
                return super().format(record)

        # تنظیم فرمت لاگ - ساده و خوانا
        console_format = ColoredFormatter("[%(levelname)s] %(message)s")

        file_format = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler اگه مسیر داده شده باشه
        if log_file:
            # مطمئن می‌شیم که پوشه والد وجود داره
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(getattr(logging, file_level.upper()))
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """لاگ debug - برای اطلاعات تکمیلی"""
        self.logger.debug(message)

    def info(self, message: str):
        """لاگ info - برای اطلاعات عمومی"""
        self.logger.info(message)

    def warning(self, message: str):
        """لاگ warning - برای هشدارها"""
        self.logger.warning(message)

    def error(self, message: str):
        """لاگ error - برای خطاها"""
        self.logger.error(message)

    def critical(self, message: str):
        """لاگ critical - برای خطاهای جدی"""
        self.logger.critical(message)


# یه instance سراسری که همه جا ازش استفاده کنیم
_global_logger: Optional[Logger] = None


def get_logger(name: str = "IranConcert", log_file: Optional[str] = None) -> Logger:
    """
    دریافت logger instance

    اگه قبلاً logger ساخته نشده باشه، یکی جدید می‌سازه
    وگرنه همون قبلی رو برمی‌گردونه
    """
    global _global_logger

    if _global_logger is None:
        # اگه log_file نداده شده، یه فایل پیش‌فرض می‌سازیم
        if log_file is None:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / f"scanner_{datetime.now().strftime('%Y%m%d')}.log"

        _global_logger = Logger(name=name, log_file=str(log_file))

    return _global_logger


def setup_logger(
    log_file: Optional[str] = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG",
) -> Logger:
    """
    تنظیم logger با پارامترهای سفارشی

    این تابع معمولاً یه بار در شروع برنامه صدا زده می‌شه
    """
    global _global_logger

    if log_file is None:
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / f"scanner_{datetime.now().strftime('%Y%m%d')}.log"

    _global_logger = Logger(
        name="IranConcert",
        log_file=str(log_file),
        console_level=console_level,
        file_level=file_level,
    )

    return _global_logger


# برای راحتی کار، چند تا shortcut function
def log_info(message: str):
    """میان‌بر برای لاگ info"""
    get_logger().info(message)


def log_debug(message: str):
    """میان‌بر برای لاگ debug"""
    get_logger().debug(message)


def log_warning(message: str):
    """میان‌بر برای لاگ warning"""
    get_logger().warning(message)


def log_error(message: str):
    """میان‌بر برای لاگ error"""
    get_logger().error(message)


def log_critical(message: str):
    """میان‌بر برای لاگ critical"""
    get_logger().critical(message)
