<div align="center">

# 🎫 IranConcert Scanner

<img src="https://img.shields.io/badge/python-3.8+-blue.svg">
<img src="https://img.shields.io/badge/playwright-1.43.0-green.svg">
<img src="https://img.shields.io/badge/license-MIT-blue.svg">
<img src="https://img.shields.io/badge/status-educational-yellow.svg">

اسکنر خودکار برای سایت ایران کنسرت که صندلی‌های مورد نظرتون رو پیدا می‌کنه و رزرو می‌کنه.

</div>

---

## ✨ ویژگی‌ها

- 🤖 **اسکن خودکار** صندلی‌های متوالی و چسبیده  
- 🎯 **انتخاب هوشمند** بهترین section  
- 🔄 **User Agent تصادفی** برای جلوگیری از تشخیص bot  
- 🍪 **مدیریت کوکی** برای حفظ session  
- 📊 **Logging کامل** برای عیب‌یابی  

---

## 🚀 نصب و راه‌اندازی

```bash
# کلون پروژه
git clone https://github.com/dibbed/iranconcert-scanner.git
cd iranconcert-scanner

# نصب وابستگی‌ها
pip install -r requirements.txt
python -m playwright install
```

---

## ⚙️ تنظیمات

فایل `config.py` رو ویرایش کنید:

```python
CONFIG = {
    "url": "https://www.iranconcert.com/concert/...",  # لینک کنسرت
    "datetime": "2025-01-15 20:00",                    # زمان کنسرت
    "headful": True,                                   # نمایش مرورگر
    "user_agent": None,                                # User Agent سفارشی (اختیاری)
    "cookies": [                                       # کوکی‌های لاگین
        {
            "name": "__arcsco",
            "value": "YOUR_ARCSCO_COOKIE_VALUE_HERE",
            "domain": ".iranconcert.com"
        }
    ],
    "seat_config": {
        "GROUP_SIZE": 3,
        "ROW_FROM": 1,
        "ROW_TO": 35,
        "SEAT_FROM": 8,
        "SEAT_TO": 31,
        "AUTO_SUBMIT": True
    }
}
```

### 🍪 نحوه تنظیم کوکی‌ها:

1. وارد سایت ایران کنسرت بشید  
2. دکمه F12 رو بزنید و برید به تب **Application → Cookies**  
3. کوکی‌های `__arcsco` و `.AspNetCore.Cookies` رو پیدا کنید  
4. مقدارهاشون رو در `config.py` جایگزین کنید  

---

## ▶️ استفاده

```bash
# روش پیشنهادی (با کنترل رنگی)
python start.py

# یا اجرای نسخه جدیدتر
python src/main.py
```

---

## 🎮 کنترل Scanner

بعد از اجرا، ترمینال کنترل رنگی زیر رو نشون می‌ده:

```
🎮 SCANNER CONTROL PANEL
Commands:
  [s] - 🛑 Stop Scanner
  [r] - ▶️  Restart Scanner
  [c] - 🧹 Clear Memory
  [h] - ❓ Show Help
  [q] - 🚪 Quit Program
```

---

## 🛠️ عیب‌یابی

### 🎯 صندلی‌ها شناسایی نمی‌شن:

```python
"debug": True
```

### ⏱ خطای Timeout:

```python
"timing": {
    "retries": 5,
    "retry_sleep_ms": 2000
}
```

### 🧭 تغییر User Agent:

```python
"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
# یا بذارید None بمونه برای انتخاب تصادفی
```

### 📄 مشاهده لاگ‌ها:

```bash
tail -f logs/scanner_*.log
```

---

## ⚠️ هشدار قانونی

> **این پروژه فقط برای اهداف آموزشی ساخته شده است.**  
> **مسئولیت هرگونه استفاده عملی از آن، به‌عهده کاربر است.**

---

<div align="center">

👨‍💻 **نویسنده:** [dibbed](https://github.com/dibbed)  
⭐️ اگه پروژه واست مفید بود، یه ستاره بده! ❤️

</div>