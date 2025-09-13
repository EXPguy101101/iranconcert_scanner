# -*- coding: utf-8 -*-
"""
Custom Exceptions
کلاس‌های exception سفارشی پروژه

این فایل شامل تمام exception هایی هست که ممکنه توی پروژه پیش بیاد
"""


class IranConcertError(Exception):
    """
    Base exception برای تمام خطاهای پروژه

    همه exception های دیگه از این ارث‌بری می‌کنن
    """

    def __init__(self, message: str = "An error occurred in IranConcert scanner"):
        self.message = message
        super().__init__(self.message)


class ConfigurationError(IranConcertError):
    """
    خطاهای مربوط به configuration و تنظیمات

    مثلاً وقتی config file نباشه یا فرمتش اشتباه باشه
    """

    def __init__(self, message: str = "Configuration error occurred"):
        super().__init__(f"Config Error: {message}")


class BrowserError(IranConcertError):
    """
    خطاهای مربوط به browser operations

    مثل مشکل در راه‌اندازی browser، timeout ها و غیره
    """

    def __init__(self, message: str = "Browser operation failed"):
        super().__init__(f"Browser Error: {message}")


class ScannerError(IranConcertError):
    """
    خطاهای مربوط به scanning operations

    مثل نتونستن پیدا کردن element ها، مشکل در کلیک و غیره
    """

    def __init__(self, message: str = "Scanner operation failed"):
        super().__init__(f"Scanner Error: {message}")


class NetworkError(IranConcertError):
    """
    خطاهای مربوط به شبکه و اتصال

    مثل timeout، connection refused و غیره
    """

    def __init__(self, message: str = "Network operation failed"):
        super().__init__(f"Network Error: {message}")


class ValidationError(IranConcertError):
    """
    خطاهای مربوط به validation داده‌ها

    وقتی داده‌ای که دریافت کردیم فرمت درستی نداره
    """

    def __init__(self, message: str = "Data validation failed"):
        super().__init__(f"Validation Error: {message}")
