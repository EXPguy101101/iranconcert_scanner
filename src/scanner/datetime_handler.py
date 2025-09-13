# -*- coding: utf-8 -*-
"""
DateTime Handler
مدیریت کلیک روی datetime selector ها

این ماژول مسئول پیدا کردن و کلیک روی datetime های موجود در صفحه هست
"""

from typing import List, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PWTimeoutError

from ..utils import (
    is_valid_datetime_format,
    log_debug,
    log_error,
    log_info,
    log_warning,
)


class DateTimeHandler:
    """
    کلاس مدیریت datetime selection
    
    این کلاس کارهای مربوط به پیدا کردن و کلیک روی datetime ها رو انجام می‌ده
    """
    
    def __init__(self, page: Page):
        """
        راه‌اندازی DateTimeHandler
        
        Args:
            page: صفحه playwright برای کار
        """
        self.page = page
        log_debug("DateTimeHandler initialized")
    
    async def click_datetime(self, target_datetime: str, timeout: int = 15000) -> bool:
        """
        کلیک روی datetime مشخص
        
        این تابع دنبال time element با datetime مشخص می‌گرده و روش کلیک می‌کنه
        
        Args:
            target_datetime: datetime مورد نظر (مثل "2025-01-15 20:00")
            timeout: timeout به میلی‌ثانیه
            
        Returns:
            True اگه موفق بود، False اگه نه
        """
        # اول چک می‌کنیم که فرمت datetime درست باشه
        if not is_valid_datetime_format(target_datetime):
            log_error(f"Invalid datetime format: {target_datetime}")
            return False
        
        log_info(f"Looking for datetime: {target_datetime}")
        
        # selector برای پیدا کردن time element
        selector = f'time.btn-day[datetime="{target_datetime}"]'
        
        try:
            # صبر می‌کنیم تا element ظاهر بشه
            locator = self.page.locator(selector)
            await locator.first.wait_for(state="visible", timeout=timeout)
            
            log_debug(f"Found datetime element: {target_datetime}")
            
            # حالا باید ببینیم که element کلیک‌پذیر هست یا نه
            # گاهی time element داخل button یا link هست
            clickable_locator = locator.first.locator(
                "xpath=ancestor-or-self::*[self::button or @role='button' or self::a][1]"
            )
            
            if await clickable_locator.count() > 0:
                # اگه parent clickable داره، روی اون کلیک می‌کنیم
                await clickable_locator.first.click()
                log_debug("Clicked on parent clickable element")
            else:
                # وگرنه مستقیم روی خود time element
                await locator.first.click()
                log_debug("Clicked directly on time element")
            
            log_info(f"Successfully clicked on datetime: {target_datetime}")
            return True
            
        except PWTimeoutError:
            log_warning(f"Datetime element not found within {timeout}ms: {target_datetime}")
            
            # سعی می‌کنیم لیست datetime های موجود رو نشون بدیم
            await self._show_available_datetimes()
            return False
            
        except Exception as e:
            log_error(f"Failed to click datetime {target_datetime}: {e}")
            return False
    
    async def _show_available_datetimes(self):
        """نمایش datetime های موجود در صفحه"""
        try:
            log_debug("Searching for available datetimes...")
            
            # تمام time.btn-day ها رو پیدا می‌کنیم
            datetimes = await self.page.eval_on_selector_all(
                "time.btn-day", 
                "elements => elements.map(el => el.getAttribute('datetime')).filter(dt => dt)"
            )
            
            if datetimes:
                log_info(f"Available datetimes: {', '.join(datetimes)}")
            else:
                log_warning("No datetime elements found on page")
                
        except Exception as e:
            log_debug(f"Could not retrieve available datetimes: {e}")
    
    async def get_available_datetimes(self) -> List[str]:
        """
        دریافت لیست datetime های موجود
        
        Returns:
            لیست datetime های موجود در صفحه
        """
        try:
            log_debug("Getting available datetimes...")
            
            datetimes = await self.page.eval_on_selector_all(
                "time.btn-day",
                "elements => elements.map(el => el.getAttribute('datetime')).filter(dt => dt)"
            )
            
            log_debug(f"Found {len(datetimes)} available datetimes")
            return datetimes
            
        except Exception as e:
            log_error(f"Failed to get available datetimes: {e}")
            return []
    
    async def find_closest_datetime(self, target_datetime: str) -> Optional[str]:
        """
        پیدا کردن نزدیک‌ترین datetime به target
        
        این تابع وقتی مفیده که datetime دقیق موجود نباشه
        
        Args:
            target_datetime: datetime مورد نظر
            
        Returns:
            نزدیک‌ترین datetime موجود یا None
        """
        available = await self.get_available_datetimes()
        
        if not available:
            return None
        
        # اگه دقیقاً همون datetime موجود باشه
        if target_datetime in available:
            return target_datetime
        
        log_debug(f"Exact datetime not found, looking for closest to: {target_datetime}")
        
        # فعلاً ساده‌ترین روش: اولین datetime موجود
        # می‌شه پیچیده‌تر کرد با محاسبه فاصله زمانی
        closest = available[0]
        log_info(f"Using closest available datetime: {closest}")
        
        return closest
    
    async def click_any_available_datetime(self) -> bool:
        """
        کلیک روی اولین datetime موجود
        
        این تابع وقتی مفیده که فقط می‌خوایم یه datetime انتخاب کنیم
        
        Returns:
            True اگه موفق بود
        """
        available = await self.get_available_datetimes()
        
        if not available:
            log_error("No datetime available to click")
            return False
        
        first_datetime = available[0]
        log_info(f"Clicking first available datetime: {first_datetime}")
        
        return await self.click_datetime(first_datetime)
    
    async def wait_for_datetime_elements(self, timeout: int = 10000) -> bool:
        """
        انتظار برای ظاهر شدن datetime elements
        
        Args:
            timeout: timeout به میلی‌ثانیه
            
        Returns:
            True اگه element ها ظاهر شدن
        """
        try:
            log_debug("Waiting for datetime elements to appear...")
            
            await self.page.wait_for_selector("time.btn-day", timeout=timeout)
            log_debug("Datetime elements appeared")
            return True
            
        except PWTimeoutError:
            log_warning(f"Datetime elements did not appear within {timeout}ms")
            return False
        except Exception as e:
            log_error(f"Error waiting for datetime elements: {e}")
            return False
    
    async def is_datetime_available(self, target_datetime: str) -> bool:
        """
        بررسی اینکه datetime مشخص موجود هست یا نه
        
        Args:
            target_datetime: datetime برای بررسی
            
        Returns:
            True اگه موجود باشه
        """
        available = await self.get_available_datetimes()
        return target_datetime in available
    
    async def click_datetime_with_retry(self, target_datetime: str, max_retries: int = 3) -> bool:
        """
        کلیک روی datetime با retry
        
        گاهی اوقات صفحه هنوز کاملاً لود نشده و باید چند بار تلاش کنیم
        
        Args:
            target_datetime: datetime مورد نظر
            max_retries: حداکثر تعداد تلاش
            
        Returns:
            True اگه موفق بود
        """
        for attempt in range(1, max_retries + 1):
            log_debug(f"Datetime click attempt {attempt}/{max_retries}")
            
            # اول صبر می‌کنیم تا element ها ظاهر بشن
            if not await self.wait_for_datetime_elements():
                log_warning(f"Datetime elements not ready on attempt {attempt}")
                continue
            
            # حالا سعی می‌کنیم کلیک کنیم
            if await self.click_datetime(target_datetime):
                log_info(f"Datetime clicked successfully on attempt {attempt}")
                return True
            
            # اگه موفق نبودیم، کمی صبر می‌کنیم
            if attempt < max_retries:
                log_debug(f"Attempt {attempt} failed, waiting before retry...")
                await self.page.wait_for_timeout(1000)
        
        log_error(f"Failed to click datetime after {max_retries} attempts")
        return False


# تابع کمکی برای سازگاری با کد قدیمی
async def click_datetime(page: Page, target_datetime: str) -> bool:
    """
    تابع ساده برای سازگاری با کد قدیمی
    
    Args:
        page: صفحه playwright
        target_datetime: datetime مورد نظر
        
    Returns:
        True اگه موفق بود
    """
    handler = DateTimeHandler(page)
    return await handler.click_datetime(target_datetime)
