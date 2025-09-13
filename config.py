# config.py
# ----------------------------
# تنظیمات اسکریپت iranconcert_scanner
# حالا می‌تونی آزادانه توضیح/کامنت بذاری و مقادیر رو راحت تغییر بدی.
# ----------------------------

CONFIG = {
    # لینک صفحه‌ی کنسرت (همونی که داخل مرورگر باز می‌کنی)
    "url": "https://www.iranconcert.com/concert/.../....",
    # مقدار دقیقِ datetime از تگ <time class="btn-day" datetime="...">
    "datetime": "2025-09-23 19:00",
    # اجرای مرورگر با UI (True) یا headless (False)
    "headful": True,
    # لاگ‌های کامل (کنسول/شبکه/کلیک‌ها) برای دیباگ
    "debug": True,
    # اگر بخوای از پروفایل پایدار کرومیوم استفاده کنی (کش/لوگین ذخیره می‌شه)
    "use_persistent": True,
    # --- کوکی‌ها ---
    # نکته بسیار مهم: برای جلوگیری از redirect به لاگین،
    # بهتره domain = ".iranconcert.com" و path = "/" باشه،
    # و مقدارها جدید/معتبر باشن (مستقیم از مرورگرت کپی کن).
    "cookies": [
        {
            "name": "__arcsco",
            "value": "YOUR_ARCSCO_COOKIE_VALUE_HERE",
            "domain": ".iranconcert.com",  # پیشنهاد: دامنه ریشه با نقطه
            "path": "/",  # پیشنهاد: ریشه
            "httpOnly": True,
            "secure": False,  # اگه سایت روی https-only بود، True بذار
        },
        {
            "name": ".AspNetCore.Cookies",
            "value": "YOUR_ASPNETCORE_COOKIE_VALUE_HERE",
            "domain": "www.iranconcert.com",  # قبلاً گذاشته بودی www و path /user → موجب redirect می‌شد
            "path": "/user",
            "httpOnly": True,
            "secure": True,
        },
    ],
    # --- اولویت سکشن‌ها (اختیاری) ---
    # خالی بذار تا خودش بزرگ‌ترین <area> را انتخاب کند (Auto-pick).
    "section_preferences": [
        # "part4118", "part4119"
    ],
    # --- تنظیمات اسکن و کلیک روی صندلی‌ها (برای seat_scanner.js) ---
    "seat_config": {
        "ROW_FROM": 1,  # از ردیف چندم
        "ROW_TO": 35,  # تا ردیف چندم
        "GROUP_SIZE": 3,  # چند صندلی کنار هم می‌خوای
        "GROUPS_TO_CLICK": 1,  # در هر چرخه چند گروه کلیک بشه
        "AISLE_MARGIN_PX": 10,  # آستانه تشخیص راهرو (margin-left)
        "SCAN_INTERVAL_MS": 150,  # فاصله اسکن‌ها (ms)
        "SEAT_FROM": 8,  # بازه شماره صندلی از
        "SEAT_TO": 31,  # تا
        "REQUIRE_STRICT_ADJACENT": True,  # دقیقاً پشت‌سرهم و چسبیده
        "AVOID_OVERLAP_IN_SCAN": True,  # گروه‌های هم‌پوشان انتخاب نشن
        "AUTO_SUBMIT": True,  # بعد از پیدا کردن گروه، ثبت سفارش بزن
        "SUBMIT_SELECTOR": None,  # در صورت لزوم سلکتور سفارشی دکمه
        "BEFORE_SUBMIT_DELAY_MS": 400,
    },
    # --- User Agent سفارشی (اختیاری) ---
    # اگه خالی باشه، به صورت تصادفی انتخاب می‌شه
    "user_agent": None,  # مثال: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
    # --- زمان‌بندی/ریتـرای (برای کلیک سالن) ---
    "timing": {
        "after_nav_ms": 700,  # مکث بعد از رفتن به URL (اگر در کد استفاده شد)
        "after_datetime_click_ms": 900,  # مکث بعد از کلیک روی time
        "before_section_action_ms": 600,  # مکث قبل از اقدام روی سکشن
        "post_section_action_ms": 1300,  # مکث بعد از اقدام (فرصت برای Ajax/DOM)
        "retries": 2,  # تعداد تلاش برای فعال‌سازی سکشن
        "retry_sleep_ms": 1000,  # مکث بین تلاش‌ها
    },
}
