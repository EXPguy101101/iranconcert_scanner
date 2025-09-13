# -*- coding: utf-8 -*-
"""
Configuration Settings
تنظیمات و مدل‌های پیکربندی پروژه

این فایل شامل dataclass ها و تنظیمات پیش‌فرض هست
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TimingConfig:
    """
    تنظیمات زمان‌بندی و تاخیرها

    این کلاس تمام timing های مربوط به عملیات مختلف رو نگه می‌داره
    """

    after_nav_ms: int = 700
    after_datetime_click_ms: int = 900
    before_section_action_ms: int = 600
    post_section_action_ms: int = 1300
    retries: int = 2
    retry_sleep_ms: int = 1000


@dataclass
class SeatConfig:
    """
    تنظیمات مربوط به اسکن صندلی‌ها

    این کلاس تمام پارامترهای JavaScript scanner رو شامل می‌شه
    """

    row_from: int = 1
    row_to: int = 35
    group_size: int = 3
    groups_to_click: int = 1
    aisle_margin_px: int = 10
    scan_interval_ms: int = 150
    seat_from: Optional[int] = 8
    seat_to: Optional[int] = 31
    require_strict_adjacent: bool = True
    avoid_overlap_in_scan: bool = True
    auto_submit: bool = True
    submit_selector: Optional[str] = None
    before_submit_delay_ms: int = 400

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary برای JavaScript"""
        return {
            "ROW_FROM": self.row_from,
            "ROW_TO": self.row_to,
            "GROUP_SIZE": self.group_size,
            "GROUPS_TO_CLICK": self.groups_to_click,
            "AISLE_MARGIN_PX": self.aisle_margin_px,
            "SCAN_INTERVAL_MS": self.scan_interval_ms,
            "SEAT_FROM": self.seat_from,
            "SEAT_TO": self.seat_to,
            "REQUIRE_STRICT_ADJACENT": self.require_strict_adjacent,
            "AVOID_OVERLAP_IN_SCAN": self.avoid_overlap_in_scan,
            "AUTO_SUBMIT": self.auto_submit,
            "SUBMIT_SELECTOR": self.submit_selector,
            "BEFORE_SUBMIT_DELAY_MS": self.before_submit_delay_ms,
        }


@dataclass
class CookieConfig:
    """
    تنظیمات یک کوکی

    این کلاس اطلاعات یک کوکی رو نگه می‌داره
    """

    name: str
    value: str
    domain: str = ".iranconcert.com"
    path: str = "/"
    http_only: bool = True
    secure: bool = False
    same_site: str = "Lax"

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به dictionary برای playwright"""
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "httpOnly": self.http_only,
            "secure": self.secure,
            "sameSite": self.same_site,
        }


@dataclass
class ConfigModel:
    """
    مدل اصلی تنظیمات پروژه

    این کلاس تمام تنظیمات پروژه رو در یک جا نگه می‌داره
    """

    # تنظیمات اصلی
    url: str = ""
    datetime: str = ""
    headful: bool = True
    debug: bool = True
    use_persistent: bool = True

    # کوکی‌ها
    cookies: List[CookieConfig] = field(default_factory=list)

    # اولویت‌های سکشن
    section_preferences: List[str] = field(default_factory=list)

    # تنظیمات صندلی
    seat_config: SeatConfig = field(default_factory=SeatConfig)

    # تنظیمات زمان‌بندی
    timing: TimingConfig = field(default_factory=TimingConfig)

    # تنظیمات اضافی
    user_agent: Optional[str] = None
    log_level: str = "INFO"
    log_file: Optional[str] = None

    def validate(self) -> List[str]:
        """
        اعتبارسنجی تنظیمات

        Returns:
            لیست خطاهای validation (خالی اگه همه چی درست باشه)
        """
        errors = []

        # بررسی URL
        if not self.url:
            errors.append("URL is required")
        elif not self.url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")

        # بررسی datetime
        if not self.datetime:
            errors.append("Datetime is required")
        # می‌تونیم regex validation هم اضافه کنیم

        # بررسی seat config
        if self.seat_config.row_from < 1:
            errors.append("row_from must be >= 1")
        if self.seat_config.row_to < self.seat_config.row_from:
            errors.append("row_to must be >= row_from")
        if self.seat_config.group_size < 1:
            errors.append("group_size must be >= 1")

        # بررسی timing
        if self.timing.retries < 0:
            errors.append("retries must be >= 0")

        return errors


# تنظیمات پیش‌فرض
DEFAULT_CONFIG = ConfigModel(
    url="https://www.iranconcert.com/",
    datetime="2025-01-01 20:00",
    headful=True,
    debug=True,
    use_persistent=True,
    cookies=[],
    section_preferences=[],
    seat_config=SeatConfig(),
    timing=TimingConfig(),
    log_level="INFO",
)


def create_cookie_from_dict(cookie_dict: Dict[str, Any]) -> CookieConfig:
    """
    ایجاد CookieConfig از dictionary

    این تابع برای تبدیل کوکی‌های config.py قدیمی به فرمت جدید هست

    Args:
        cookie_dict: dictionary شامل اطلاعات کوکی

    Returns:
        CookieConfig instance
    """
    return CookieConfig(
        name=cookie_dict.get("name", ""),
        value=cookie_dict.get("value", ""),
        domain=cookie_dict.get("domain", ".iranconcert.com"),
        path=cookie_dict.get("path", "/"),
        http_only=cookie_dict.get("httpOnly", True),
        secure=cookie_dict.get("secure", False),
        same_site=cookie_dict.get("sameSite", "Lax"),
    )


def create_seat_config_from_dict(seat_dict: Dict[str, Any]) -> SeatConfig:
    """
    ایجاد SeatConfig از dictionary

    Args:
        seat_dict: dictionary شامل تنظیمات صندلی

    Returns:
        SeatConfig instance
    """
    return SeatConfig(
        row_from=seat_dict.get("ROW_FROM", 1),
        row_to=seat_dict.get("ROW_TO", 35),
        group_size=seat_dict.get("GROUP_SIZE", 3),
        groups_to_click=seat_dict.get("GROUPS_TO_CLICK", 1),
        aisle_margin_px=seat_dict.get("AISLE_MARGIN_PX", 10),
        scan_interval_ms=seat_dict.get("SCAN_INTERVAL_MS", 150),
        seat_from=seat_dict.get("SEAT_FROM"),
        seat_to=seat_dict.get("SEAT_TO"),
        require_strict_adjacent=seat_dict.get("REQUIRE_STRICT_ADJACENT", True),
        avoid_overlap_in_scan=seat_dict.get("AVOID_OVERLAP_IN_SCAN", True),
        auto_submit=seat_dict.get("AUTO_SUBMIT", True),
        submit_selector=seat_dict.get("SUBMIT_SELECTOR"),
        before_submit_delay_ms=seat_dict.get("BEFORE_SUBMIT_DELAY_MS", 400),
    )


def create_timing_config_from_dict(timing_dict: Dict[str, Any]) -> TimingConfig:
    """
    ایجاد TimingConfig از dictionary

    Args:
        timing_dict: dictionary شامل تنظیمات زمان‌بندی

    Returns:
        TimingConfig instance
    """
    return TimingConfig(
        after_nav_ms=timing_dict.get("after_nav_ms", 700),
        after_datetime_click_ms=timing_dict.get("after_datetime_click_ms", 900),
        before_section_action_ms=timing_dict.get("before_section_action_ms", 600),
        post_section_action_ms=timing_dict.get("post_section_action_ms", 1300),
        retries=timing_dict.get("retries", 2),
        retry_sleep_ms=timing_dict.get("retry_sleep_ms", 1000),
    )
