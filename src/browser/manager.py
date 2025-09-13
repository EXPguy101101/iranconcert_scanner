# -*- coding: utf-8 -*-
"""
Browser Manager
مدیریت مرورگر و context های playwright

این ماژول مسئول راه‌اندازی، تنظیم و مدیریت browser هست
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from ..config import ConfigModel
from ..utils import BrowserError, log_debug, log_error, log_info, log_warning
from .user_agent import get_chrome_user_agent, get_random_user_agent


class BrowserManager:
    """
    کلاس مدیریت browser

    این کلاس تمام کارهای مربوط به browser رو انجام می‌ده:
    راه‌اندازی، تنظیم کوکی‌ها، user agent و غیره
    """

    def __init__(self, config: ConfigModel):
        """
        راه‌اندازی BrowserManager

        Args:
            config: تنظیمات پروژه
        """
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        log_debug("BrowserManager initialized")

    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()

    async def start(self):
        """شروع playwright و راه‌اندازی browser"""
        try:
            log_info("Starting browser...")

            self.playwright = await async_playwright().start()

            if self.config.use_persistent:
                await self._create_persistent_context()
            else:
                await self._create_regular_browser()

            # دریافت صفحه
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()

            log_info("Browser started successfully")

        except Exception as e:
            log_error(f"Failed to start browser: {e}")
            raise BrowserError(f"Browser startup failed: {e}") from e

    async def _create_persistent_context(self):
        """ایجاد persistent context"""
        log_debug("Creating persistent context...")

        # مسیر user data directory
        user_data_dir = Path("/tmp/iranconcert")
        user_data_dir.mkdir(exist_ok=True)

        # انتخاب user agent
        user_agent = self._get_user_agent()

        try:
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=not self.config.headful,
                locale="fa-IR",
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                # تنظیمات اضافی برای جلوگیری از تشخیص bot
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            log_debug(
                f"Persistent context created with user agent: {user_agent[:50]}..."
            )

        except Exception as e:
            log_error(f"Failed to create persistent context: {e}")
            raise BrowserError(f"Persistent context creation failed: {e}") from e

    async def _create_regular_browser(self):
        """ایجاد browser معمولی"""
        log_debug("Creating regular browser...")

        try:
            # راه‌اندازی browser
            self.browser = await self.playwright.chromium.launch(
                headless=not self.config.headful,
                args=[
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # انتخاب user agent
            user_agent = self._get_user_agent()

            # ایجاد context
            self.context = await self.browser.new_context(
                locale="fa-IR",
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
            )

            log_debug(f"Regular browser created with user agent: {user_agent[:50]}...")

        except Exception as e:
            log_error(f"Failed to create regular browser: {e}")
            raise BrowserError(f"Regular browser creation failed: {e}") from e

    def _get_user_agent(self) -> str:
        """انتخاب user agent مناسب"""
        # اگه user agent سفارشی داده شده، از اون استفاده می‌کنیم
        if self.config.user_agent:
            log_debug(f"Using custom user agent: {self.config.user_agent[:50]}...")
            return self.config.user_agent

        # وگرنه یکی تصادفی انتخاب می‌کنیم
        # ترجیح با Chrome چون بیشتر سایت‌ها باهاش مشکل ندارن
        try:
            user_agent = get_chrome_user_agent()
            log_debug("Selected Chrome user agent")
            return user_agent
        except Exception:
            # اگه مشکلی بود، یکی تصادفی
            log_warning("Failed to get Chrome user agent, using random")
            return get_random_user_agent()

    async def setup_cookies(self):
        """تنظیم کوکی‌ها"""
        if not self.config.cookies:
            log_debug("No cookies to set")
            return

        log_info(f"Setting up {len(self.config.cookies)} cookies...")

        try:
            # تبدیل کوکی‌ها به فرمت playwright
            playwright_cookies = []
            for cookie in self.config.cookies:
                cookie_dict = cookie.to_dict()

                # اگه domain مشخص نشده، از URL استفاده می‌کنیم
                if not cookie_dict.get("domain"):
                    parsed_url = urlparse(self.config.url)
                    cookie_dict["domain"] = parsed_url.hostname or "www.iranconcert.com"

                playwright_cookies.append(cookie_dict)

            # اضافه کردن کوکی‌ها
            await self.context.add_cookies(playwright_cookies)

            log_info("Cookies set successfully")

        except Exception as e:
            log_error(f"Failed to set cookies: {e}")
            # کوکی‌ها critical نیستن، ادامه می‌دیم
            log_warning("Continuing without cookies...")

    async def navigate_to_url(self, url: Optional[str] = None) -> Page:
        """
        رفتن به URL مشخص

        Args:
            url: آدرس مقصد (اگه نداده شه از config استفاده می‌کنه)

        Returns:
            Page instance
        """
        target_url = url or self.config.url

        if not target_url:
            raise BrowserError("No URL specified")

        log_info(f"Navigating to: {target_url}")

        try:
            # اول کوکی‌ها رو تنظیم می‌کنیم
            await self.setup_cookies()

            # بعد به صفحه می‌ریم
            await self.page.goto(target_url, wait_until="domcontentloaded")

            log_info("Navigation completed")
            return self.page

        except Exception as e:
            log_error(f"Navigation failed: {e}")
            raise BrowserError(f"Failed to navigate to {target_url}: {e}") from e

    async def get_page(self) -> Page:
        """
        دریافت page فعلی

        Returns:
            Page instance
        """
        if not self.page:
            raise BrowserError("No page available - browser not started")

        return self.page

    async def new_page(self) -> Page:
        """
        ایجاد صفحه جدید

        Returns:
            Page instance جدید
        """
        if not self.context:
            raise BrowserError("No context available - browser not started")

        try:
            new_page = await self.context.new_page()
            log_debug("New page created")
            return new_page
        except Exception as e:
            log_error(f"Failed to create new page: {e}")
            raise BrowserError(f"New page creation failed: {e}") from e

    async def close(self):
        """بستن browser و تمیز کردن منابع"""
        log_info("Closing browser...")

        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            log_info("Browser closed successfully")

        except Exception as e:
            log_error(f"Error while closing browser: {e}")
            # حتی اگه خطا باشه، منابع رو null می‌کنیم
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

    def is_running(self) -> bool:
        """بررسی اینکه browser در حال اجرا هست یا نه"""
        return self.context is not None and self.page is not None

    async def reload_page(self):
        """reload کردن صفحه فعلی"""
        if not self.page:
            raise BrowserError("No page available")

        try:
            log_debug("Reloading page...")
            await self.page.reload(wait_until="domcontentloaded")
            log_debug("Page reloaded")
        except Exception as e:
            log_error(f"Failed to reload page: {e}")
            raise BrowserError(f"Page reload failed: {e}") from e

    async def wait_for_load_state(
        self, state: str = "networkidle", timeout: int = 30000
    ):
        """
        انتظار برای load state مشخص

        Args:
            state: نوع state (load, domcontentloaded, networkidle)
            timeout: timeout به میلی‌ثانیه
        """
        if not self.page:
            raise BrowserError("No page available")

        try:
            log_debug(f"Waiting for load state: {state}")
            await self.page.wait_for_load_state(state, timeout=timeout)
            log_debug(f"Load state {state} reached")
        except Exception as e:
            log_warning(f"Load state {state} timeout: {e}")
            # timeout رو critical نمی‌دونیم، فقط warning می‌دیم


# تابع کمکی برای ایجاد BrowserManager
async def create_browser_manager(config: ConfigModel) -> BrowserManager:
    """
    ایجاد و راه‌اندازی BrowserManager

    Args:
        config: تنظیمات پروژه

    Returns:
        BrowserManager instance آماده
    """
    manager = BrowserManager(config)
    await manager.start()
    return manager
