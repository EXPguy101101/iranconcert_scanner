# -*- coding: utf-8 -*-
"""
Seat Map Detector
تشخیص و انتظار برای نمایش نقشه صندلی‌ها

این ماژول مسئول پیدا کردن seat map در صفحه هست
"""

from typing import List, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PWTimeoutError

from ..utils import log_debug, log_error, log_info, log_warning


class SeatMapDetector:
    """
    کلاس تشخیص seat map
    
    این کلاس با selector های مختلف سعی می‌کنه seat map رو پیدا کنه
    """
    
    def __init__(self, page: Page):
        """
        راه‌اندازی SeatMapDetector
        
        Args:
            page: صفحه playwright برای کار
        """
        self.page = page
        
        # لیست selector هایی که معمولاً برای seat map استفاده می‌شن
        # این لیست بر اساس تجربه و بررسی سایت‌های مختلف تهیه شده
        self.seat_map_selectors = [
            ".seatRow",              # معمولی‌ترین selector
            ".seat-row",             # نسخه kebab-case
            "#seatmap",              # ID مستقیم
            ".seat-map",             # class مستقیم
            ".seats",                # ساده‌تر
            "[class*=seat][class*=Row]",  # ترکیبی
            "[id*=seat][class*=map]",     # ID و class ترکیبی
            ".seating-chart",        # نام دیگه
            ".venue-map",            # نقشه سالن
            "#seats-container",      # container صندلی‌ها
            ".seat-selection",       # انتخاب صندلی
        ]
        
        log_debug(f"SeatMapDetector initialized with {len(self.seat_map_selectors)} selectors")
    
    async def wait_for_seatmap(self, timeout_ms: int = 25000) -> bool:
        """
        انتظار برای ظاهر شدن seat map
        
        این تابع با selector های مختلف سعی می‌کنه seat map رو پیدا کنه
        
        Args:
            timeout_ms: timeout به میلی‌ثانیه
            
        Returns:
            True اگه seat map پیدا شد
        """
        log_info("Looking for seat map...")
        
        # هر selector رو امتحان می‌کنیم
        for selector in self.seat_map_selectors:
            try:
                log_debug(f"Trying selector: {selector}")
                
                await self.page.wait_for_selector(
                    selector, 
                    state="visible", 
                    timeout=timeout_ms
                )
                
                log_info(f"Seat map found with selector: {selector}")
                return True
                
            except PWTimeoutError:
                # این selector کار نکرد، بعدی رو امتحان می‌کنیم
                continue
            except Exception as e:
                log_debug(f"Error with selector {selector}: {e}")
                continue
        
        log_warning("Seat map not detected with any known selector")
        
        # اگه هیچکدوم کار نکرد، سعی می‌کنیم ببینیم چه element هایی توی صفحه هست
        await self._debug_page_elements()
        
        return False
    
    async def _debug_page_elements(self):
        """نمایش element های موجود در صفحه برای debug"""
        try:
            log_debug("Analyzing page elements for debugging...")
            
            # دنبال element هایی می‌گردیم که ممکنه seat map باشن
            potential_selectors = [
                "[class*='seat']",
                "[id*='seat']", 
                "[class*='map']",
                "[id*='map']",
                "div[class*='row']",
                "section",
                "main"
            ]
            
            found_elements = []
            
            for selector in potential_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # اطلاعات element ها رو جمع می‌کنیم
                        element_info = await self.page.evaluate(f"""
                            Array.from(document.querySelectorAll('{selector}')).slice(0, 3).map(el => ({{
                                tag: el.tagName,
                                id: el.id || '',
                                className: el.className || '',
                                textContent: (el.textContent || '').slice(0, 50)
                            }}))
                        """)
                        
                        found_elements.extend(element_info)
                        
                except Exception:
                    continue
            
            if found_elements:
                log_debug(f"Found {len(found_elements)} potentially relevant elements")
                for elem in found_elements[:5]:  # فقط 5 تای اول
                    log_debug(f"  - {elem['tag']} id='{elem['id']}' class='{elem['className'][:30]}'")
            else:
                log_debug("No potentially relevant elements found")
                
        except Exception as e:
            log_debug(f"Debug analysis failed: {e}")
    
    async def detect_seatmap_selectors(self) -> List[str]:
        """
        تشخیص selector های seat map موجود در صفحه
        
        Returns:
            لیست selector هایی که seat map دارن
        """
        found_selectors = []
        
        log_debug("Detecting available seat map selectors...")
        
        for selector in self.seat_map_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    # چک می‌کنیم که element visible هست یا نه
                    is_visible = await self.page.is_visible(selector)
                    if is_visible:
                        found_selectors.append(selector)
                        log_debug(f"Found visible seat map: {selector}")
                    else:
                        log_debug(f"Found hidden seat map: {selector}")
                        
            except Exception as e:
                log_debug(f"Error checking selector {selector}: {e}")
        
        log_info(f"Detected {len(found_selectors)} visible seat map selectors")
        return found_selectors
    
    async def get_seat_map_info(self) -> Optional[dict]:
        """
        دریافت اطلاعات seat map
        
        Returns:
            dictionary شامل اطلاعات seat map یا None
        """
        selectors = await self.detect_seatmap_selectors()
        
        if not selectors:
            return None
        
        # اولین selector موجود رو انتخاب می‌کنیم
        main_selector = selectors[0]
        
        try:
            # اطلاعات element رو می‌گیریم
            info = await self.page.evaluate(f"""
                (() => {{
                    const element = document.querySelector('{main_selector}');
                    if (!element) return null;
                    
                    const rect = element.getBoundingClientRect();
                    const rows = element.querySelectorAll('[class*="row"], .seatRow, .seat-row');
                    const seats = element.querySelectorAll('[class*="seat"], [class*="chair"]');
                    
                    return {{
                        selector: '{main_selector}',
                        visible: !element.hidden && rect.width > 0 && rect.height > 0,
                        dimensions: {{
                            width: rect.width,
                            height: rect.height,
                            x: rect.x,
                            y: rect.y
                        }},
                        rowCount: rows.length,
                        seatCount: seats.length,
                        id: element.id || '',
                        className: element.className || ''
                    }};
                }})()
            """)
            
            if info:
                log_info(f"Seat map info: {info['rowCount']} rows, {info['seatCount']} seats")
                return info
            
        except Exception as e:
            log_error(f"Failed to get seat map info: {e}")
        
        return None
    
    async def wait_for_seat_elements(self, timeout_ms: int = 15000) -> bool:
        """
        انتظار برای ظاهر شدن seat element ها
        
        Args:
            timeout_ms: timeout به میلی‌ثانیه
            
        Returns:
            True اگه seat element ها ظاهر شدن
        """
        seat_selectors = [
            '[class*="seat"]',
            '[class*="chair"]', 
            '.seat',
            '.chair'
        ]
        
        log_debug("Waiting for seat elements...")
        
        for selector in seat_selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout_ms)
                log_debug(f"Seat elements found: {selector}")
                return True
            except PWTimeoutError:
                continue
        
        log_warning("No seat elements found")
        return False
    
    async def is_seat_map_ready(self) -> bool:
        """
        بررسی اینکه seat map آماده هست یا نه
        
        Returns:
            True اگه seat map کاملاً لود شده باشه
        """
        # اول چک می‌کنیم که seat map وجود داره
        if not await self.wait_for_seatmap(timeout_ms=5000):
            return False
        
        # بعد چک می‌کنیم که seat element ها هم هستن
        if not await self.wait_for_seat_elements(timeout_ms=5000):
            return False
        
        # در نهایت چک می‌کنیم که تعداد کافی seat داریم
        try:
            seat_count = await self.page.evaluate("""
                document.querySelectorAll('[class*="seat"], [class*="chair"]').length
            """)
            
            if seat_count > 0:
                log_info(f"Seat map is ready with {seat_count} seats")
                return True
            else:
                log_warning("Seat map found but no seats detected")
                return False
                
        except Exception as e:
            log_error(f"Error checking seat readiness: {e}")
            return False
    
    async def wait_with_network_idle(self, timeout_ms: int = 25000) -> bool:
        """
        انتظار برای seat map با network idle
        
        گاهی seat map از طریق AJAX لود می‌شه و باید صبر کنیم
        
        Args:
            timeout_ms: timeout کل
            
        Returns:
            True اگه seat map آماده شد
        """
        log_debug("Waiting for seat map with network idle...")
        
        try:
            # اول صبر می‌کنیم تا network idle بشه
            await self.page.wait_for_load_state("networkidle", timeout=timeout_ms // 2)
            log_debug("Network idle reached")
            
            # حالا دنبال seat map می‌گردیم
            return await self.wait_for_seatmap(timeout_ms // 2)
            
        except PWTimeoutError:
            log_debug("Network idle timeout, trying direct detection")
            # اگه network idle نشد، مستقیم سعی می‌کنیم
            return await self.wait_for_seatmap(timeout_ms // 2)
        except Exception as e:
            log_error(f"Error in network idle wait: {e}")
            return False


# تابع کمکی برای سازگاری با کد قدیمی
async def wait_for_seatmap(page: Page, timeout_ms: int = 25000) -> bool:
    """
    تابع ساده برای سازگاری با کد قدیمی
    
    Args:
        page: صفحه playwright
        timeout_ms: timeout به میلی‌ثانیه
        
    Returns:
        True اگه seat map پیدا شد
    """
    detector = SeatMapDetector(page)
    return await detector.wait_for_seatmap(timeout_ms)
