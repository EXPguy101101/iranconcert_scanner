# -*- coding: utf-8 -*-
"""
JavaScript Injector
تزریق و مدیریت کدهای JavaScript در صفحه

این ماژول مسئول بارگذاری و تزریق seat scanner JavaScript هست
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import Page

from ..config import SeatConfig
from ..utils import ScannerError, log_debug, log_error, log_info, log_warning


class JSInjector:
    """
    کلاس تزریق JavaScript
    
    این کلاس کارهای مربوط به بارگذاری، تنظیم و تزریق JavaScript رو انجام می‌ده
    """
    
    def __init__(self, page: Page, js_file_path: Optional[str] = None):
        """
        راه‌اندازی JSInjector
        
        Args:
            page: صفحه playwright برای کار
            js_file_path: مسیر فایل JavaScript (اختیاری)
        """
        self.page = page
        
        # اگه مسیر داده نشده، مسیر پیش‌فرض رو استفاده می‌کنیم
        if js_file_path:
            self.js_path = Path(js_file_path)
        else:
            # مسیر نسبت به فایل فعلی
            current_dir = Path(__file__).parent.parent.parent
            self.js_path = current_dir / "assets" / "seat_scanner.js"
        
        log_debug(f"JSInjector initialized with JS path: {self.js_path}")
    
    async def inject_scanner(self, seat_config: SeatConfig) -> bool:
        """
        تزریق seat scanner JavaScript
        
        این تابع فایل JavaScript رو می‌خونه، config رو جایگزین می‌کنه و تزریق می‌کنه
        
        Args:
            seat_config: تنظیمات صندلی برای JavaScript
            
        Returns:
            True اگه تزریق موفق بود
        """
        log_info("Injecting seat scanner JavaScript...")
        
        try:
            # بارگذاری فایل JavaScript
            js_code = await self._load_js_file()
            if not js_code:
                return False
            
            # تنظیم config
            configured_js = await self._configure_js(js_code, seat_config)
            
            # تزریق در صفحه
            await self.page.evaluate(configured_js)
            
            log_info("Seat scanner JavaScript injected successfully")
            
            # چک می‌کنیم که تابع‌های مورد نظر در دسترس هستن
            await self._verify_injection()
            
            return True
            
        except Exception as e:
            log_error(f"Failed to inject JavaScript: {e}")
            return False
    
    async def _load_js_file(self) -> Optional[str]:
        """بارگذاری فایل JavaScript"""
        try:
            if not self.js_path.exists():
                log_error(f"JavaScript file not found: {self.js_path}")
                return None
            
            log_debug(f"Loading JavaScript from: {self.js_path}")
            
            with open(self.js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            log_debug(f"JavaScript loaded successfully ({len(js_code)} characters)")
            return js_code
            
        except Exception as e:
            log_error(f"Failed to load JavaScript file: {e}")
            return None
    
    async def _configure_js(self, js_code: str, seat_config: SeatConfig) -> str:
        """تنظیم config در JavaScript"""
        try:
            # تبدیل seat_config به dictionary
            config_dict = seat_config.to_dict()
            
            # تبدیل به JSON با پشتیبانی از فارسی
            config_json = json.dumps(config_dict, ensure_ascii=False, indent=2)
            
            log_debug("Configuration prepared for JavaScript")
            log_debug(f"Config keys: {list(config_dict.keys())}")
            
            # جایگزینی __CONFIG__ با config واقعی
            configured_js = js_code.replace("__CONFIG__", config_json)
            
            return configured_js
            
        except Exception as e:
            log_error(f"Failed to configure JavaScript: {e}")
            raise ScannerError(f"JavaScript configuration failed: {e}")
    
    async def _verify_injection(self):
        """تایید موفقیت تزریق"""
        try:
            # چک می‌کنیم که تابع‌های اصلی موجود هستن
            functions_exist = await self.page.evaluate("""
                () => {
                    return {
                        seatScannerStart: typeof window.__seatScannerStart === 'function',
                        seatScannerStop: typeof window.__seatScannerStop === 'function',
                        clearSeatMemory: typeof window.__clearSeatMemory === 'function'
                    };
                }
            """)
            
            missing_functions = [name for name, exists in functions_exist.items() if not exists]
            
            if missing_functions:
                log_warning(f"Some scanner functions not available: {missing_functions}")
            else:
                log_debug("All scanner functions verified successfully")
                
        except Exception as e:
            log_debug(f"Function verification failed: {e}")
    
    async def start_scanner(self) -> bool:
        """شروع اسکن صندلی‌ها"""
        try:
            log_info("Starting seat scanner...")
            
            result = await self.page.evaluate("""
                () => {
                    if (typeof window.__seatScannerStart === 'function') {
                        window.__seatScannerStart();
                        return true;
                    }
                    return false;
                }
            """)
            
            if result:
                log_info("Seat scanner started successfully")
            else:
                log_error("Seat scanner start function not available")
            
            return result
            
        except Exception as e:
            log_error(f"Failed to start scanner: {e}")
            return False
    
    async def stop_scanner(self, loud: bool = False) -> bool:
        """توقف اسکن صندلی‌ها"""
        try:
            log_info("Stopping seat scanner...")
            
            result = await self.page.evaluate(f"""
                () => {{
                    if (typeof window.__seatScannerStop === 'function') {{
                        window.__seatScannerStop({str(loud).lower()});
                        return true;
                    }}
                    return false;
                }}
            """)
            
            if result:
                log_info("Seat scanner stopped successfully")
            else:
                log_warning("Seat scanner stop function not available")
            
            return result
            
        except Exception as e:
            log_error(f"Failed to stop scanner: {e}")
            return False
    
    async def clear_seat_memory(self) -> bool:
        """پاک کردن حافظه صندلی‌های انتخاب شده"""
        try:
            log_debug("Clearing seat memory...")
            
            result = await self.page.evaluate("""
                () => {
                    if (typeof window.__clearSeatMemory === 'function') {
                        window.__clearSeatMemory();
                        return true;
                    }
                    return false;
                }
            """)
            
            if result:
                log_debug("Seat memory cleared successfully")
            else:
                log_warning("Clear memory function not available")
            
            return result
            
        except Exception as e:
            log_error(f"Failed to clear seat memory: {e}")
            return False
    
    async def get_scanner_status(self) -> Dict[str, Any]:
        """دریافت وضعیت اسکنر"""
        try:
            status = await self.page.evaluate("""
                () => {
                    // چک می‌کنیم که متغیرهای اسکنر موجود هستن یا نه
                    const hasScanner = typeof window.__seatScannerStart === 'function';
                    
                    if (!hasScanner) {
                        return { available: false };
                    }
                    
                    // سعی می‌کنیم اطلاعات بیشتری بگیریم
                    // این قسمت بستگی به پیاده‌سازی JavaScript داره
                    return {
                        available: true,
                        functions: {
                            start: typeof window.__seatScannerStart === 'function',
                            stop: typeof window.__seatScannerStop === 'function',
                            clear: typeof window.__clearSeatMemory === 'function'
                        }
                    };
                }
            """)
            
            return status
            
        except Exception as e:
            log_debug(f"Failed to get scanner status: {e}")
            return {"available": False, "error": str(e)}
    
    async def inject_custom_script(self, script: str, script_name: str = "custom") -> bool:
        """
        تزریق JavaScript سفارشی
        
        Args:
            script: کد JavaScript
            script_name: نام script برای logging
            
        Returns:
            True اگه تزریق موفق بود
        """
        try:
            log_debug(f"Injecting custom script: {script_name}")
            
            await self.page.evaluate(script)
            
            log_debug(f"Custom script '{script_name}' injected successfully")
            return True
            
        except Exception as e:
            log_error(f"Failed to inject custom script '{script_name}': {e}")
            return False
    
    async def wait_for_scanner_ready(self, timeout: int = 10000) -> bool:
        """انتظار برای آماده شدن اسکنر"""
        try:
            log_debug("Waiting for scanner to be ready...")
            
            # منتظر می‌مونیم تا تابع‌های اسکنر در دسترس باشن
            await self.page.wait_for_function("""
                () => {
                    return typeof window.__seatScannerStart === 'function' &&
                           typeof window.__seatScannerStop === 'function' &&
                           typeof window.__clearSeatMemory === 'function';
                }
            """, timeout=timeout)
            
            log_debug("Scanner is ready")
            return True
            
        except Exception as e:
            log_warning(f"Scanner readiness timeout: {e}")
            return False
    
    def get_js_path(self) -> Path:
        """دریافت مسیر فایل JavaScript"""
        return self.js_path
    
    def set_js_path(self, new_path: str):
        """تنظیم مسیر جدید برای فایل JavaScript"""
        self.js_path = Path(new_path)
        log_debug(f"JavaScript path updated to: {self.js_path}")


# تابع کمکی برای سازگاری با کد قدیمی
async def inject_js(page: Page, seat_config: Dict[str, Any]) -> bool:
    """
    تابع ساده برای سازگاری با کد قدیمی
    
    Args:
        page: صفحه playwright
        seat_config: تنظیمات صندلی (dictionary format)
        
    Returns:
        True اگه تزریق موفق بود
    """
    # تبدیل dictionary به SeatConfig
    from ..config import create_seat_config_from_dict
    
    config_obj = create_seat_config_from_dict(seat_config)
    
    # ایجاد injector و تزریق
    injector = JSInjector(page)
    return await injector.inject_scanner(config_obj)


# تابع کمکی برای ایجاد injector
def create_js_injector(page: Page, js_file_path: Optional[str] = None) -> JSInjector:
    """
    ایجاد JSInjector instance
    
    Args:
        page: صفحه playwright
        js_file_path: مسیر فایل JavaScript (اختیاری)
        
    Returns:
        JSInjector instance
    """
    return JSInjector(page, js_file_path)
