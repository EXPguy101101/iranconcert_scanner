# -*- coding: utf-8 -*-
"""
User Agent Manager
مدیریت user agent های مختلف برای جلوگیری از تشخیص bot

این ماژول یه مجموعه user agent واقعی و متنوع ارائه می‌ده
"""

import random
from typing import List, Optional

from ..utils import log_debug, log_warning


class UserAgentManager:
    """
    کلاس مدیریت user agent ها
    
    این کلاس یه لیست از user agent های واقعی نگه می‌داره و به صورت تصادفی یکی رو انتخاب می‌کنه
    """
    
    def __init__(self, custom_agents: Optional[List[str]] = None):
        """
        راه‌اندازی UserAgentManager
        
        Args:
            custom_agents: لیست user agent های سفارشی (اختیاری)
        """
        self.custom_agents = custom_agents or []
        
        # یه مجموعه user agent های واقعی و به‌روز
        # این لیست از browser های واقعی جمع‌آوری شده
        self._default_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Firefox on Linux
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
        ]
        
        log_debug(f"UserAgentManager initialized with {len(self._default_agents)} default agents")
        if self.custom_agents:
            log_debug(f"Added {len(self.custom_agents)} custom user agents")
    
    def get_random_agent(self) -> str:
        """
        دریافت یک user agent تصادفی
        
        اگه user agent سفارشی داده شده باشه، اولویت با اونا هست
        وگرنه از لیست پیش‌فرض انتخاب می‌کنه
        
        Returns:
            یک user agent string تصادفی
        """
        # اگه user agent سفارشی داریم، از اونا استفاده می‌کنیم
        if self.custom_agents:
            agent = random.choice(self.custom_agents)
            log_debug(f"Selected custom user agent: {agent[:50]}...")
            return agent
        
        # وگرنه از لیست پیش‌فرض
        agent = random.choice(self._default_agents)
        log_debug(f"Selected default user agent: {agent[:50]}...")
        return agent
    
    def get_chrome_agent(self) -> str:
        """
        دریافت یک Chrome user agent
        
        گاهی نیاز داریم حتماً Chrome باشه
        
        Returns:
            یک Chrome user agent
        """
        chrome_agents = [agent for agent in self._default_agents if "Chrome" in agent]
        
        if not chrome_agents:
            log_warning("No Chrome user agents found, falling back to random agent")
            return self.get_random_agent()
        
        agent = random.choice(chrome_agents)
        log_debug(f"Selected Chrome user agent: {agent[:50]}...")
        return agent
    
    def get_firefox_agent(self) -> str:
        """
        دریافت یک Firefox user agent
        
        Returns:
            یک Firefox user agent
        """
        firefox_agents = [agent for agent in self._default_agents if "Firefox" in agent]
        
        if not firefox_agents:
            log_warning("No Firefox user agents found, falling back to random agent")
            return self.get_random_agent()
        
        agent = random.choice(firefox_agents)
        log_debug(f"Selected Firefox user agent: {agent[:50]}...")
        return agent
    
    def add_custom_agent(self, agent: str):
        """
        اضافه کردن user agent سفارشی
        
        Args:
            agent: user agent string جدید
        """
        if agent and agent not in self.custom_agents:
            self.custom_agents.append(agent)
            log_debug(f"Added custom user agent: {agent[:50]}...")
    
    def get_all_agents(self) -> List[str]:
        """
        دریافت تمام user agent های موجود
        
        Returns:
            لیست تمام user agent ها (سفارشی + پیش‌فرض)
        """
        return self.custom_agents + self._default_agents
    
    def is_valid_agent(self, agent: str) -> bool:
        """
        بررسی معتبر بودن user agent
        
        یه چک ساده می‌کنه که user agent حداقل شامل Mozilla باشه
        
        Args:
            agent: user agent برای بررسی
            
        Returns:
            True اگه معتبر باشه
        """
        if not agent or len(agent) < 20:
            return False
        
        # حداقل باید شامل Mozilla باشه
        return "Mozilla" in agent


# یه instance سراسری برای استفاده راحت
_global_user_agent_manager: Optional[UserAgentManager] = None


def get_user_agent_manager(custom_agents: Optional[List[str]] = None) -> UserAgentManager:
    """
    دریافت UserAgentManager instance
    
    Args:
        custom_agents: لیست user agent های سفارشی
        
    Returns:
        UserAgentManager instance
    """
    global _global_user_agent_manager
    
    if _global_user_agent_manager is None:
        _global_user_agent_manager = UserAgentManager(custom_agents)
    
    return _global_user_agent_manager


def get_random_user_agent() -> str:
    """
    میان‌بر برای دریافت user agent تصادفی
    
    Returns:
        یک user agent تصادفی
    """
    return get_user_agent_manager().get_random_agent()


def get_chrome_user_agent() -> str:
    """
    میان‌بر برای دریافت Chrome user agent
    
    Returns:
        یک Chrome user agent
    """
    return get_user_agent_manager().get_chrome_agent()
