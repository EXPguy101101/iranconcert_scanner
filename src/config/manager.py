# -*- coding: utf-8 -*-
"""
Configuration Manager
مدیریت تنظیمات پروژه

این ماژول مسئول بارگذاری، validation و مدیریت تنظیمات هست
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils import ConfigurationError, log_debug, log_error, log_info, log_warning
from .settings import (
    DEFAULT_CONFIG,
    ConfigModel,
    create_cookie_from_dict,
    create_seat_config_from_dict,
    create_timing_config_from_dict,
)


class ConfigManager:
    """
    کلاس مدیریت تنظیمات
    
    این کلاس تنظیمات رو از فایل، environment variable ها و مقادیر پیش‌فرض می‌خونه
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        راه‌اندازی ConfigManager
        
        Args:
            config_path: مسیر فایل config (اختیاری)
        """
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[ConfigModel] = None
        
        log_debug(f"ConfigManager initialized with config path: {self.config_path}")
    
    def _find_config_file(self) -> str:
        """
        پیدا کردن فایل config
        
        اول دنبال config.py می‌گرده، بعد config.json
        
        Returns:
            مسیر فایل config
        """
        # اول توی همین پوشه دنبال config.py می‌گردیم
        current_dir = Path.cwd()
        
        # اولویت با config.py (فایل اصلی)
        config_py = current_dir / "config.py"
        if config_py.exists():
            log_debug(f"Found config.py at: {config_py}")
            return str(config_py)
        
        # بعد config.json
        config_json = current_dir / "config.json"
        if config_json.exists():
            log_debug(f"Found config.json at: {config_json}")
            return str(config_json)
        
        # اگه هیچکدوم نبود، از config.py استفاده می‌کنیم
        log_warning("No config file found, will use config.py")
        return str(config_py)
    
    def load_config(self) -> ConfigModel:
        """
        بارگذاری تنظیمات
        
        اول از فایل config.py می‌خونه، بعد environment variable ها رو چک می‌کنه
        
        Returns:
            ConfigModel instance با تنظیمات بارگذاری شده
        """
        if self._config is not None:
            return self._config
        
        log_info("Loading configuration...")
        
        # شروع با تنظیمات پیش‌فرض
        config_dict = self._load_default_config()
        
        # بارگذاری از فایل config.py
        file_config = self._load_from_file()
        if file_config:
            config_dict.update(file_config)
            log_debug("Merged file configuration")
        
        # بارگذاری از environment variables
        env_config = self._load_from_env()
        if env_config:
            config_dict.update(env_config)
            log_debug("Merged environment configuration")
        
        # تبدیل به ConfigModel
        self._config = self._dict_to_config_model(config_dict)
        
        # validation
        errors = self._config.validate()
        if errors:
            error_msg = f"Configuration validation failed: {', '.join(errors)}"
            log_error(error_msg)
            raise ConfigurationError(error_msg)
        
        log_info("Configuration loaded successfully")
        return self._config
    
    def _load_default_config(self) -> Dict[str, Any]:
        """بارگذاری تنظیمات پیش‌فرض"""
        return {
            "url": DEFAULT_CONFIG.url,
            "datetime": DEFAULT_CONFIG.datetime,
            "headful": DEFAULT_CONFIG.headful,
            "debug": DEFAULT_CONFIG.debug,
            "use_persistent": DEFAULT_CONFIG.use_persistent,
            "cookies": [],
            "section_preferences": [],
            "seat_config": DEFAULT_CONFIG.seat_config.to_dict(),
            "timing": {
                "after_nav_ms": DEFAULT_CONFIG.timing.after_nav_ms,
                "after_datetime_click_ms": DEFAULT_CONFIG.timing.after_datetime_click_ms,
                "before_section_action_ms": DEFAULT_CONFIG.timing.before_section_action_ms,
                "post_section_action_ms": DEFAULT_CONFIG.timing.post_section_action_ms,
                "retries": DEFAULT_CONFIG.timing.retries,
                "retry_sleep_ms": DEFAULT_CONFIG.timing.retry_sleep_ms,
            }
        }
    
    def _load_from_file(self) -> Optional[Dict[str, Any]]:
        """
        بارگذاری از فایل
        
        Returns:
            Dictionary شامل تنظیمات یا None اگه فایل نباشه
        """
        config_path = Path(self.config_path)
        
        if not config_path.exists():
            log_warning(f"Config file not found: {config_path}")
            return None
        
        try:
            if config_path.suffix == ".py":
                return self._load_from_python_file(config_path)
            elif config_path.suffix == ".json":
                return self._load_from_json_file(config_path)
            else:
                log_warning(f"Unsupported config file format: {config_path.suffix}")
                return None
        except Exception as e:
            log_error(f"Failed to load config from {config_path}: {e}")
            return None
    
    def _load_from_python_file(self, config_path: Path) -> Dict[str, Any]:
        """بارگذاری از فایل Python"""
        import importlib.util
        
        spec = importlib.util.spec_from_file_location("config", config_path)
        if spec is None or spec.loader is None:
            raise ConfigurationError(f"Cannot load config from {config_path}")
        
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        if not hasattr(config_module, "CONFIG"):
            raise ConfigurationError("CONFIG variable not found in config.py")
        
        log_debug(f"Loaded config from Python file: {config_path}")
        return config_module.CONFIG
    
    def _load_from_json_file(self, config_path: Path) -> Dict[str, Any]:
        """بارگذاری از فایل JSON"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        log_debug(f"Loaded config from JSON file: {config_path}")
        return config_data
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        بارگذاری از environment variables
        
        متغیرهایی که با IRANCONCERT_ شروع می‌شن رو می‌خونه
        
        Returns:
            Dictionary شامل تنظیمات از env
        """
        env_config = {}
        
        # لیست متغیرهایی که پشتیبانی می‌کنیم
        env_mappings = {
            "IRANCONCERT_URL": "url",
            "IRANCONCERT_DATETIME": "datetime", 
            "IRANCONCERT_HEADFUL": ("headful", bool),
            "IRANCONCERT_DEBUG": ("debug", bool),
            "IRANCONCERT_USE_PERSISTENT": ("use_persistent", bool),
            "IRANCONCERT_LOG_LEVEL": "log_level",
            "IRANCONCERT_USER_AGENT": "user_agent",
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # اگه tuple باشه، یعنی نیاز به type conversion داره
                if isinstance(config_key, tuple):
                    actual_key, value_type = config_key
                    if value_type == bool:
                        env_config[actual_key] = env_value.lower() in ("true", "1", "yes", "on")
                    else:
                        env_config[actual_key] = value_type(env_value)
                else:
                    env_config[config_key] = env_value
                
                log_debug(f"Loaded from env: {env_key} = {env_value}")
        
        return env_config
    
    def _dict_to_config_model(self, config_dict: Dict[str, Any]) -> ConfigModel:
        """
        تبدیل dictionary به ConfigModel
        
        Args:
            config_dict: dictionary شامل تنظیمات
            
        Returns:
            ConfigModel instance
        """
        # تبدیل کوکی‌ها
        cookies = []
        for cookie_data in config_dict.get("cookies", []):
            if isinstance(cookie_data, dict):
                cookies.append(create_cookie_from_dict(cookie_data))
        
        # تبدیل seat config
        seat_config_dict = config_dict.get("seat_config", {})
        seat_config = create_seat_config_from_dict(seat_config_dict)
        
        # تبدیل timing config
        timing_dict = config_dict.get("timing", {})
        timing_config = create_timing_config_from_dict(timing_dict)
        
        return ConfigModel(
            url=config_dict.get("url", ""),
            datetime=config_dict.get("datetime", ""),
            headful=config_dict.get("headful", True),
            debug=config_dict.get("debug", True),
            use_persistent=config_dict.get("use_persistent", True),
            cookies=cookies,
            section_preferences=config_dict.get("section_preferences", []),
            seat_config=seat_config,
            timing=timing_config,
            user_agent=config_dict.get("user_agent"),
            log_level=config_dict.get("log_level", "INFO"),
            log_file=config_dict.get("log_file")
        )
    
    def get_timing(self, key: str, default: int) -> int:
        """
        دریافت مقدار timing مشخص
        
        این تابع برای سازگاری با کد قدیمی هست
        
        Args:
            key: کلید timing
            default: مقدار پیش‌فرض
            
        Returns:
            مقدار timing
        """
        if self._config is None:
            self.load_config()
        
        timing_map = {
            "after_nav_ms": self._config.timing.after_nav_ms,
            "after_datetime_click_ms": self._config.timing.after_datetime_click_ms,
            "before_section_action_ms": self._config.timing.before_section_action_ms,
            "post_section_action_ms": self._config.timing.post_section_action_ms,
            "retries": self._config.timing.retries,
            "retry_sleep_ms": self._config.timing.retry_sleep_ms,
        }
        
        return timing_map.get(key, default)
    
    def reload_config(self):
        """بارگذاری مجدد تنظیمات"""
        self._config = None
        return self.load_config()


# یه instance سراسری برای استفاده راحت
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """
    دریافت ConfigManager instance
    
    Args:
        config_path: مسیر فایل config (اختیاری)
        
    Returns:
        ConfigManager instance
    """
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_path)
    
    return _global_config_manager


def load_config(config_path: Optional[str] = None) -> ConfigModel:
    """
    میان‌بر برای بارگذاری تنظیمات
    
    Args:
        config_path: مسیر فایل config (اختیاری)
        
    Returns:
        ConfigModel instance
    """
    return get_config_manager(config_path).load_config()
