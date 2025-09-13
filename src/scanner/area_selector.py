# -*- coding: utf-8 -*-
"""
Area Selector
انتخاب و کلیک روی بهترین area در نقشه سالن

این ماژول مسئول پیدا کردن و کلیک روی area های موجود در image map هست
"""

import re
from typing import Any, Dict, List, Optional

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PWTimeoutError

from ..utils import extract_part_id, log_debug, log_error, log_info, log_warning


class AreaSelector:
    """
    کلاس انتخاب area
    
    این کلاس کارهای مربوط به پیدا کردن، تجزیه و کلیک روی area های نقشه رو انجام می‌ده
    """
    
    def __init__(self, page: Page):
        """
        راه‌اندازی AreaSelector
        
        Args:
            page: صفحه playwright برای کار
        """
        self.page = page
        log_debug("AreaSelector initialized")
    
    async def find_best_area(self, section_preferences: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        پیدا کردن بهترین area برای کلیک
        
        اول اولویت‌های کاربر رو چک می‌کنه، بعد بزرگ‌ترین area رو انتخاب می‌کنه
        
        Args:
            section_preferences: لیست اولویت‌های section (مثل ["part4118", "part4119"])
            
        Returns:
            dictionary شامل اطلاعات area یا None
        """
        log_info("Looking for best area to select...")
        
        # اول چک می‌کنیم که اصلاً area داریم یا نه
        if not await self._wait_for_areas():
            log_error("No map areas found on page")
            return None
        
        # اگه اولویت داده شده، اول اونا رو امتحان می‌کنیم
        if section_preferences:
            preferred_area = await self._find_preferred_area(section_preferences)
            if preferred_area:
                log_info(f"Found preferred area: {preferred_area.get('part_id', 'unknown')}")
                return preferred_area
        
        # اگه اولویت پیدا نشد، بزرگ‌ترین رو انتخاب می‌کنیم
        largest_area = await self._find_largest_area()
        if largest_area:
            log_info(f"Selected largest area: {largest_area.get('part_id', 'unknown')}")
            return largest_area
        
        log_error("No suitable area found")
        return None
    
    async def _wait_for_areas(self, timeout: int = 12000) -> bool:
        """انتظار برای ظاهر شدن area ها"""
        try:
            await self.page.wait_for_selector("map area", state="attached", timeout=timeout)
            log_debug("Map areas found")
            return True
        except PWTimeoutError:
            log_warning("No map areas found within timeout")
            return False
    
    async def _find_preferred_area(self, preferences: List[str]) -> Optional[Dict[str, Any]]:
        """پیدا کردن area بر اساس اولویت‌های کاربر"""
        for pref in preferences:
            log_debug(f"Looking for preferred section: {pref}")
            
            # selector برای پیدا کردن area با onclick مشخص
            selector = f"map area[onclick*='{pref}']:not([onclick*='toastr.error'])"
            
            try:
                element_count = await self.page.locator(selector).count()
                if element_count > 0:
                    # اطلاعات area رو می‌گیریم
                    area_info = await self._get_area_info(selector)
                    if area_info:
                        area_info['is_preferred'] = True
                        area_info['preference'] = pref
                        return area_info
            except Exception as e:
                log_debug(f"Error checking preference {pref}: {e}")
        
        log_debug("No preferred areas found")
        return None
    
    async def _find_largest_area(self) -> Optional[Dict[str, Any]]:
        """پیدا کردن بزرگ‌ترین area"""
        log_debug("Finding largest area...")
        
        # JavaScript برای محاسبه مساحت و انتخاب بزرگ‌ترین
        js_code = """
(() => {
  // تابع محاسبه مساحت از روی coordinates
  function calculateArea(coordsStr) {
    if (!coordsStr) return 0;
    
    // تبدیل coordinates به نقاط
    const nums = coordsStr.split(",")
      .map(s => parseFloat(s.trim()))
      .filter(n => !Number.isNaN(n));
    
    const points = [];
    for (let i = 0; i + 1 < nums.length; i += 2) {
      points.push([nums[i], nums[i + 1]]);
    }
    
    if (points.length < 3) return 0;
    
    // محاسبه مساحت با فرمول Shoelace
    let area = 0;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const [x0, y0] = points[j];
      const [x1, y1] = points[i];
      area += (x0 * y1) - (x1 * y0);
    }
    
    return Math.abs(area) / 2;
  }
  
  // پیدا کردن تمام area ها
  const areas = Array.from(document.querySelectorAll("map area"));
  
  // فیلتر کردن area های مناسب
  const candidates = areas.map(el => {
    const onclick = el.getAttribute("onclick") || "";
    const coords = el.getAttribute("coords") || "";
    const area = calculateArea(coords);
    
    return {
      element: el,
      onclick: onclick,
      coords: coords,
      area: area,
      hasAjax: onclick.includes("ajax("),
      hasError: onclick.includes("toastr.error")
    };
  }).filter(item => 
    item.hasAjax && 
    !item.hasError && 
    item.area > 0
  );
  
  if (candidates.length === 0) return null;
  
  // مرتب کردن بر اساس مساحت (بزرگ‌ترین اول)
  candidates.sort((a, b) => b.area - a.area);
  
  // علامت‌گذاری بزرگ‌ترین area
  const largest = candidates[0];
  largest.element.setAttribute("data-autopick", "1");
  
  return {
    onclick: largest.onclick,
    coords: largest.coords,
    area: largest.area,
    selector: "map area[data-autopick='1']"
  };
})();
"""
        
        try:
            result = await self.page.evaluate(js_code)
            
            if not result:
                log_warning("No suitable areas found for auto-selection")
                return None
            
            # اطلاعات اضافی رو اضافه می‌کنیم
            area_info = {
                'onclick': result['onclick'],
                'coords': result['coords'],
                'area': result['area'],
                'selector': result['selector'],
                'is_preferred': False,
                'part_id': extract_part_id(result['onclick'])
            }
            
            log_debug(f"Largest area found with area: {result['area']}")
            return area_info
            
        except Exception as e:
            log_error(f"Error finding largest area: {e}")
            return None
    
    async def _get_area_info(self, selector: str) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات کامل یک area"""
        try:
            info = await self.page.evaluate(f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    
                    const onclick = el.getAttribute('onclick') || '';
                    const coords = el.getAttribute('coords') || '';
                    
                    return {{
                        onclick: onclick,
                        coords: coords,
                        selector: '{selector}'
                    }};
                }})()
            """)
            
            if info:
                info['part_id'] = extract_part_id(info['onclick'])
                return info
            
        except Exception as e:
            log_debug(f"Error getting area info for {selector}: {e}")
        
        return None
    
    async def click_area(self, area_info: Dict[str, Any]) -> bool:
        """
        کلیک روی area انتخاب شده
        
        Args:
            area_info: اطلاعات area که از find_best_area دریافت شده
            
        Returns:
            True اگه کلیک موفق بود
        """
        if not area_info:
            log_error("No area info provided for clicking")
            return False
        
        onclick = area_info.get('onclick', '')
        selector = area_info.get('selector', '')
        part_id = area_info.get('part_id', 'unknown')
        
        log_info(f"Attempting to click area: {part_id}")
        
        # اول سعی می‌کنیم با onclick مستقیم
        if onclick and await self._force_select_by_onclick(onclick):
            log_info("Area selected successfully via onclick")
            return True
        
        # اگه onclick کار نکرد، کلیک فیزیکی می‌کنیم
        if selector and await self._click_area_physically(selector):
            log_info("Area selected successfully via physical click")
            return True
        
        log_error(f"Failed to click area: {part_id}")
        return False
    
    async def _force_select_by_onclick(self, onclick_str: str) -> bool:
        """اجرای مستقیم onclick از طریق JavaScript"""
        # استخراج URL از onclick
        match = re.search(r"ajax\(.*?'([^']+/concert/seat/[^']+)'", onclick_str or "")
        if not match:
            log_debug("No ajax URL found in onclick")
            return False
        
        rel_url = match.group(1)
        
        try:
            # تبدیل به URL کامل
            abs_url = await self.page.evaluate("(u) => new URL(u, location.origin).href", rel_url)
            
            # اول سعی می‌کنیم با تابع ajax خود صفحه
            ajax_success = await self.page.evaluate("""
                (absUrl) => {
                    try {
                        if (typeof ajax === 'function') {
                            ajax(null, absUrl, 'buyPanel', 'seatsPanel', 'seatsPanel', '', '', 0, 0, 0, '');
                            return true;
                        }
                        return false;
                    } catch(e) {
                        return false;
                    }
                }
            """, abs_url)
            
            if ajax_success:
                log_debug(f"Ajax call successful: {abs_url}")
                return True
            
            # اگه ajax کار نکرد، با fetch امتحان می‌کنیم
            fetch_success = await self._try_fetch_request(abs_url)
            return fetch_success
            
        except Exception as e:
            log_debug(f"Force select failed: {e}")
            return False
    
    async def _try_fetch_request(self, url: str) -> bool:
        """امتحان کردن fetch request"""
        try:
            status = await self.page.evaluate("""
                async (absUrl) => {
                    const response = await fetch(absUrl, {
                        method: 'POST',
                        credentials: 'include',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Referer': location.href
                        },
                        redirect: 'follow'
                    });
                    
                    const html = await response.text();
                    
                    // سعی می‌کنیم DOM رو بروزرسانی کنیم
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const seats = doc.querySelector('#seatsPanel') || 
                                 doc.querySelector('.seatRow') || 
                                 doc.querySelector('#seatmap');
                    
                    const target = document.querySelector('#seatsPanel') || 
                                  document.querySelector('#seatmap');
                    
                    if (seats && target) {
                        target.innerHTML = seats.innerHTML || seats.outerHTML || html;
                    }
                    
                    return response.status;
                }
            """, url)
            
            log_debug(f"Fetch request completed with status: {status}")
            return status < 400
            
        except Exception as e:
            log_debug(f"Fetch request failed: {e}")
            return False
    
    async def _click_area_physically(self, selector: str) -> bool:
        """کلیک فیزیکی روی area"""
        try:
            log_debug(f"Attempting physical click on: {selector}")
            
            # اول mouse رو حرکت می‌دیم
            await self._move_mouse_to_area(selector)
            
            # بعد کلیک می‌کنیم
            click_info = await self._calculate_click_position(selector)
            if not click_info:
                return False
            
            # کلیک فیزیکی
            await self.page.mouse.down()
            await self.page.mouse.up()
            await self.page.mouse.click(click_info['x'], click_info['y'])
            
            # dispatch کردن event روی area
            await self.page.eval_on_selector(
                selector,
                "el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))"
            )
            
            # dispatch کردن event روی image هم
            if click_info.get('img_selector'):
                await self.page.evaluate("""
                    (data) => {
                        const img = document.querySelector(data.imgSelector);
                        if (img) {
                            img.dispatchEvent(new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                clientX: data.x,
                                clientY: data.y
                            }));
                        }
                    }
                """, {
                    'imgSelector': click_info['img_selector'],
                    'x': click_info['x'],
                    'y': click_info['y']
                })
            
            log_debug("Physical click completed")
            return True
            
        except Exception as e:
            log_error(f"Physical click failed: {e}")
            return False
    
    async def _move_mouse_to_area(self, selector: str):
        """حرکت mouse به area"""
        click_info = await self._calculate_click_position(selector)
        if click_info:
            await self.page.mouse.move(click_info['x'], click_info['y'])
    
    async def _calculate_click_position(self, selector: str) -> Optional[Dict[str, Any]]:
        """محاسبه موقعیت کلیک روی area"""
        js_code = """
        (el) => {
            // تابع محاسبه مرکز از coordinates
            function calculateCentroid(coordsStr) {
                if (!coordsStr) return null;
                
                const nums = coordsStr.split(",")
                    .map(s => parseFloat(s.trim()))
                    .filter(n => !Number.isNaN(n));
                
                const points = [];
                for (let i = 0; i + 1 < nums.length; i += 2) {
                    points.push([nums[i], nums[i + 1]]);
                }
                
                if (points.length < 3) return null;
                
                let area = 0, cx = 0, cy = 0;
                for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
                    const [x0, y0] = points[j];
                    const [x1, y1] = points[i];
                    const cross = (x0 * y1) - (x1 * y0);
                    area += cross;
                    cx += (x0 + x1) * cross;
                    cy += (y0 + y1) * cross;
                }
                
                if (area === 0) return null;
                
                return {
                    cx: cx / (3 * area),
                    cy: cy / (3 * area)
                };
            }
            
            const areaEl = el;
            const mapEl = areaEl.closest("map");
            if (!mapEl) return null;
            
            const mapName = mapEl.getAttribute("name");
            if (!mapName) return null;
            
            const img = document.querySelector(`img[usemap="#${CSS.escape(mapName)}"]`);
            if (!img) return null;
            
            const centroid = calculateCentroid(areaEl.getAttribute("coords"));
            if (!centroid) return null;
            
            // محاسبه scale
            const naturalW = img.naturalWidth || img.width;
            const naturalH = img.naturalHeight || img.height;
            const clientW = img.clientWidth;
            const clientH = img.clientHeight;
            const scaleX = clientW / naturalW;
            const scaleY = clientH / naturalH;
            
            // محاسبه موقعیت نهایی
            const x = centroid.cx * scaleX;
            const y = centroid.cy * scaleY;
            const rect = img.getBoundingClientRect();
            
            return {
                x: rect.left + x + window.scrollX,
                y: rect.top + y + window.scrollY,
                imgSelector: `img[usemap="#${CSS.escape(mapName)}"]`
            };
        }
        """
        
        try:
            result = await self.page.eval_on_selector(selector, js_code)
            if result:
                return {
                    'x': result['x'],
                    'y': result['y'],
                    'img_selector': result['imgSelector']
                }
        except Exception as e:
            log_debug(f"Error calculating click position: {e}")
        
        return None


# تابع کمکی برای سازگاری با کد قدیمی
async def click_best_map_area(page: Page, section_prefs: Optional[List[str]] = None, timeout_ms: int = 12000) -> bool:
    """
    تابع ساده برای سازگاری با کد قدیمی
    
    Args:
        page: صفحه playwright
        section_prefs: اولویت‌های section
        timeout_ms: timeout (فعلاً استفاده نمی‌شه)
        
    Returns:
        True اگه area انتخاب شد
    """
    selector = AreaSelector(page)
    
    # پیدا کردن بهترین area
    area_info = await selector.find_best_area(section_prefs)
    if not area_info:
        return False
    
    # کلیک روی area
    return await selector.click_area(area_info)
