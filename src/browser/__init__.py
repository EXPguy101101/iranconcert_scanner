# -*- coding: utf-8 -*-
"""
Browser Management Module
ماژول مدیریت مرورگر و عملیات وب

این ماژول شامل کلاس‌ها و توابع مربوط به مدیریت مرورگر، user agent و instrumentation است
"""

from .instrumentation import (
                              InstrumentationManager,
                              attach_debug_instrumentation,
                              setup_instrumentation,
)
from .manager import BrowserManager, create_browser_manager
from .user_agent import (
                              UserAgentManager,
                              get_chrome_user_agent,
                              get_random_user_agent,
                              get_user_agent_manager,
)
from .user_agent_fallback import FakeUserAgentManager

__all__ = [
    'BrowserManager', 
    'create_browser_manager',
    'UserAgentManager', 
    'get_user_agent_manager',
    'get_random_user_agent',
    'get_chrome_user_agent',
    'FakeUserAgentManager',
    'InstrumentationManager',
    'setup_instrumentation',
    'attach_debug_instrumentation'
]
