# -*- coding: utf-8 -*-
"""
Helper Functions
توابع کمکی و utility های مشترک

این فایل شامل توابعی هست که توی چندین جای پروژه استفاده می‌شن
"""

import re
from typing import Optional, Union


def to_ascii_digits(text: str) -> str:
    """
    تبدیل اعداد فارسی و عربی به انگلیسی
    
    این تابع اعداد فارسی (۰۱۲۳...) و عربی (٠١٢٣...) رو به انگلیسی تبدیل می‌کنه
    
    Args:
        text: متن ورودی که ممکنه شامل اعداد فارسی/عربی باشه
        
    Returns:
        متن با اعداد انگلیسی
    """
    if not isinstance(text, str):
        text = str(text)
    
    # اعداد فارسی
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    # اعداد عربی
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    
    # تبدیل فارسی به انگلیسی
    for i, persian_digit in enumerate(persian_digits):
        text = text.replace(persian_digit, str(i))
    
    # تبدیل عربی به انگلیسی
    for i, arabic_digit in enumerate(arabic_digits):
        text = text.replace(arabic_digit, str(i))
    
    return text


def to_int(value: Union[str, int, None]) -> int:
    """
    تبدیل امن به integer
    
    این تابع سعی می‌کنه هر چیزی رو به int تبدیل کنه
    اگه نتونه، NaN برمی‌گردونه
    
    Args:
        value: مقداری که باید به int تبدیل بشه
        
    Returns:
        عدد integer یا NaN اگه تبدیل ممکن نباشه
    """
    if value is None:
        return float('nan')
    
    if isinstance(value, int):
        return value
    
    # اول اعداد فارسی/عربی رو تبدیل می‌کنیم
    text = to_ascii_digits(str(value))
    
    # سعی می‌کنیم عدد رو پیدا کنیم
    match = re.search(r'-?\d+', text)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            pass
    
    return float('nan')


def extract_part_id(onclick_str: Optional[str]) -> Optional[str]:
    """
    استخراج part ID از onclick string
    
    توی سایت ایران کنسرت، onclick ها معمولاً شامل !part123 هستن
    این تابع اون part رو استخراج می‌کنه
    
    Args:
        onclick_str: رشته onclick که ممکنه شامل part باشه
        
    Returns:
        part ID (مثل "part123") یا None اگه پیدا نشه
    """
    if not onclick_str:
        return None
    
    # دنبال pattern مثل !part123 می‌گردیم
    match = re.search(r'!part(\d+)', onclick_str)
    if match:
        return f"part{match.group(1)}"
    
    return None


def is_valid_datetime_format(datetime_str: str) -> bool:
    """
    بررسی فرمت datetime
    
    چک می‌کنه که datetime به فرمت درست باشه (YYYY-MM-DD HH:MM)
    
    Args:
        datetime_str: رشته datetime برای بررسی
        
    Returns:
        True اگه فرمت درست باشه، وگرنه False
    """
    if not datetime_str:
        return False
    
    # pattern برای فرمت YYYY-MM-DD HH:MM
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'
    return bool(re.match(pattern, datetime_str))


def clean_text(text: str) -> str:
    """
    تمیز کردن متن
    
    فضاهای اضافی رو حذف می‌کنه و متن رو normalize می‌کنه
    
    Args:
        text: متن ورودی
        
    Returns:
        متن تمیز شده
    """
    if not text:
        return ""
    
    # حذف فضاهای اضافی از اول و آخر
    text = text.strip()
    
    # تبدیل چندین فضای پشت سر هم به یکی
    text = re.sub(r'\s+', ' ', text)
    
    return text


def safe_get_attribute(element, attribute: str, default: str = "") -> str:
    """
    دریافت امن attribute از element
    
    اگه element یا attribute وجود نداشته باشه، مقدار پیش‌فرض برمی‌گردونه
    
    Args:
        element: element برای دریافت attribute
        attribute: نام attribute
        default: مقدار پیش‌فرض
        
    Returns:
        مقدار attribute یا مقدار پیش‌فرض
    """
    try:
        if hasattr(element, 'getAttribute'):
            return element.getAttribute(attribute) or default
        elif hasattr(element, 'get_attribute'):
            return element.get_attribute(attribute) or default
        else:
            return default
    except Exception:
        return default


def format_duration(seconds: float) -> str:
    """
    فرمت کردن مدت زمان به شکل خوانا
    
    Args:
        seconds: مدت زمان به ثانیه
        
    Returns:
        رشته فرمت شده (مثل "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    کوتاه کردن متن با حفظ خوانایی
    
    Args:
        text: متن اصلی
        max_length: حداکثر طول
        suffix: پسوند برای متن کوتاه شده
        
    Returns:
        متن کوتاه شده
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_coordinates(coords_str: str) -> list:
    """
    تجزیه coordinates از رشته
    
    این تابع coordinates area های HTML رو تجزیه می‌کنه
    
    Args:
        coords_str: رشته coordinates (مثل "100,200,300,400")
        
    Returns:
        لیست نقاط [(x1,y1), (x2,y2), ...]
    """
    if not coords_str:
        return []
    
    try:
        # تبدیل اعداد فارسی/عربی
        coords_str = to_ascii_digits(coords_str)
        
        # استخراج اعداد
        numbers = [float(x.strip()) for x in coords_str.split(",") if x.strip()]
        
        # تبدیل به نقاط
        points = []
        for i in range(0, len(numbers) - 1, 2):
            points.append((numbers[i], numbers[i + 1]))
        
        return points
        
    except (ValueError, IndexError):
        return []


def calculate_polygon_area(points: list) -> float:
    """
    محاسبه مساحت چندضلعی با فرمول Shoelace
    
    Args:
        points: لیست نقاط [(x1,y1), (x2,y2), ...]
        
    Returns:
        مساحت چندضلعی
    """
    if len(points) < 3:
        return 0.0
    
    try:
        area = 0.0
        n = len(points)
        
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area) / 2.0
        
    except (TypeError, IndexError):
        return 0.0


def get_polygon_centroid(points: list) -> Optional[tuple]:
    """
    محاسبه مرکز چندضلعی
    
    Args:
        points: لیست نقاط [(x1,y1), (x2,y2), ...]
        
    Returns:
        مختصات مرکز (x, y) یا None
    """
    if len(points) < 3:
        return None
    
    try:
        area = calculate_polygon_area(points)
        if area == 0:
            return None
        
        cx = cy = 0.0
        n = len(points)
        
        for i in range(n):
            j = (i + 1) % n
            cross = (points[i][0] * points[j][1] - points[j][0] * points[i][1])
            cx += (points[i][0] + points[j][0]) * cross
            cy += (points[i][1] + points[j][1]) * cross
        
        factor = 1.0 / (6.0 * area)
        return (cx * factor, cy * factor)
        
    except (TypeError, IndexError, ZeroDivisionError):
        return None


def sanitize_filename(filename: str) -> str:
    """
    تمیز کردن نام فایل از کاراکترهای غیرمجاز
    
    Args:
        filename: نام فایل اصلی
        
    Returns:
        نام فایل تمیز شده
    """
    if not filename:
        return "untitled"
    
    # حذف کاراکترهای غیرمجاز
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # حذف فضاهای اضافی
    filename = clean_text(filename)
    
    # محدود کردن طول
    filename = truncate_text(filename, max_length=100, suffix="")
    
    return filename or "untitled"


def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """
    دکوراتور برای retry کردن تابع در صورت خطا
    
    Args:
        max_retries: حداکثر تعداد تلاش
        delay: تاخیر بین تلاش‌ها (ثانیه)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import asyncio
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if asyncio.iscoroutinefunction(func):
                            await asyncio.sleep(delay)
                        else:
                            import time
                            time.sleep(delay)
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


def is_url_valid(url: str) -> bool:
    """
    بررسی معتبر بودن URL
    
    Args:
        url: آدرس برای بررسی
        
    Returns:
        True اگه URL معتبر باشه
    """
    if not url:
        return False
    
    # چک کردن شروع URL
    if not url.startswith(('http://', 'https://')):
        return False
    
    # چک کردن وجود domain
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return bool(parsed.netloc)
    except Exception:
        return False
