# -*- coding: utf-8 -*-
"""
User Agent Fallback
پشتیبان برای user agent با استفاده از fake-useragent library

این فایل یه fallback ارائه می‌ده اگه کسی بخواد از fake-useragent استفاده کنه
"""

from typing import Optional

from ..utils import log_debug, log_error, log_warning

try:
    from fake_useragent import UserAgent
    HAS_FAKE_USERAGENT = True
except ImportError:
    HAS_FAKE_USERAGENT = False
    log_warning("fake-useragent library not found, using built-in user agents")


class FakeUserAgentManager:
    """
    مدیریت user agent با استفاده از fake-useragent library
    
    این کلاس wrapper روی fake-useragent هست
    """
    
    def __init__(self):
        """راه‌اندازی FakeUserAgentManager"""
        self.ua = None
        
        if HAS_FAKE_USERAGENT:
            try:
                self.ua = UserAgent()
                log_debug("FakeUserAgentManager initialized successfully")
            except Exception as e:
                log_error(f"Failed to initialize fake-useragent: {e}")
                self.ua = None
        else:
            log_warning("fake-useragent not available, falling back to manual agents")
    
    def get_random_agent(self) -> Optional[str]:
        """
        دریافت user agent تصادفی از fake-useragent
        
        Returns:
            user agent string یا None اگه مشکلی باشه
        """
        if not self.ua:
            return None
        
        try:
            agent = self.ua.random
            log_debug(f"Generated fake user agent: {agent[:50]}...")
            return agent
        except Exception as e:
            log_error(f"Failed to get random user agent: {e}")
            return None
    
    def get_chrome_agent(self) -> Optional[str]:
        """
        دریافت Chrome user agent از fake-useragent
        
        Returns:
            Chrome user agent یا None
        """
        if not self.ua:
            return None
        
        try:
            agent = self.ua.chrome
            log_debug(f"Generated fake Chrome agent: {agent[:50]}...")
            return agent
        except Exception as e:
            log_error(f"Failed to get Chrome user agent: {e}")
            return None
    
    def get_firefox_agent(self) -> Optional[str]:
        """
        دریافت Firefox user agent از fake-useragent
        
        Returns:
            Firefox user agent یا None
        """
        if not self.ua:
            return None
        
        try:
            agent = self.ua.firefox
            log_debug(f"Generated fake Firefox agent: {agent[:50]}...")
            return agent
        except Exception as e:
            log_error(f"Failed to get Firefox user agent: {e}")
            return None
