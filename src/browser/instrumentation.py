# -*- coding: utf-8 -*-
"""
Instrumentation Manager
مدیریت debug و monitoring صفحات وب

این ماژول برای نظارت بر console، network و user interactions استفاده می‌شه
"""

from playwright.async_api import Page

from ..utils import log_debug, log_error, log_info, log_warning


class InstrumentationManager:
    """
    کلاس مدیریت instrumentation

    این کلاس listener های مختلف رو به صفحه اضافه می‌کنه تا بتونیم
    console logs، network requests و user clicks رو ببینیم
    """

    def __init__(self, page: Page, enabled: bool = True):
        """
        راه‌اندازی InstrumentationManager

        Args:
            page: صفحه playwright برای attach کردن listeners
            enabled: فعال بودن instrumentation
        """
        self.page = page
        self.enabled = enabled
        self._listeners_attached = False

        log_debug(f"InstrumentationManager initialized (enabled: {enabled})")

    async def attach_all(self):
        """اتصال تمام listener ها"""
        if not self.enabled:
            log_debug("Instrumentation disabled, skipping attach")
            return

        if self._listeners_attached:
            log_debug("Listeners already attached")
            return

        log_info("Attaching debug instrumentation...")

        try:
            await self._attach_console_logging()
            await self._attach_network_monitoring()
            await self._attach_click_tracking()

            self._listeners_attached = True
            log_info("Debug instrumentation attached successfully")

        except Exception as e:
            log_error(f"Failed to attach instrumentation: {e}")
            # اگه instrumentation fail بشه، ادامه می‌دیم

    async def _attach_console_logging(self):
        """اتصال console logging"""

        def on_console(msg):
            try:
                # فقط console های مهم رو لاگ می‌کنیم
                msg_type = msg.type.upper()
                msg_text = msg.text

                if msg_type in ["ERROR", "WARN"]:
                    log_warning(f"Browser console [{msg_type}]: {msg_text}")
                elif msg_type == "LOG" and any(
                    keyword in msg_text.lower()
                    for keyword in ["error", "fail", "exception"]
                ):
                    log_warning(f"Browser console [LOG]: {msg_text}")
                else:
                    log_debug(f"Browser console [{msg_type}]: {msg_text}")

            except Exception as e:
                log_debug(f"Console logging error: {e}")

        self.page.on("console", on_console)
        log_debug("Console logging attached")

    async def _attach_network_monitoring(self):
        """اتصال network monitoring"""

        def is_interesting_url(url: str) -> bool:
            """چک می‌کنه که URL جالب هست یا نه"""
            interesting_patterns = [
                "/concert/seat/",
                "IsValidSelectedSeats",
                "seatsPanel",
                "ajax",
                "/api/",
                "login",
                "auth",
            ]
            return any(pattern in url for pattern in interesting_patterns)

        def on_request(request):
            if is_interesting_url(request.url):
                log_debug(f"Network request: {request.method} {request.url}")

        async def on_response(response):
            if is_interesting_url(response.url):
                try:
                    status = response.status
                    url = response.url

                    if status >= 400:
                        log_warning(f"Network error [{status}]: {url}")
                    elif status >= 300:
                        log_debug(f"Network redirect [{status}]: {url}")
                    else:
                        log_debug(f"Network response [{status}]: {url}")

                except Exception as e:
                    log_debug(f"Response logging error: {e}")

        self.page.on("request", on_request)
        self.page.on("response", on_response)
        log_debug("Network monitoring attached")

    async def _attach_click_tracking(self):
        """اتصال click tracking"""

        # اول pylog function رو expose می‌کنیم
        async def pylog(data):
            try:
                if isinstance(data, dict):
                    event_type = data.get("type", "unknown")

                    if event_type == "user-click":
                        tag = data.get("tag", "")
                        text = data.get("text", "")[:50]  # محدود کردن طول متن
                        onclick = data.get("onclick", "")

                        if onclick:
                            log_info(
                                f"User clicked {tag}: '{text}' (onclick: {onclick[:30]}...)"
                            )
                        else:
                            log_debug(f"User clicked {tag}: '{text}'")
                    else:
                        log_debug(f"Browser event [{event_type}]: {data}")
                else:
                    log_debug(f"Browser event: {data}")

            except Exception as e:
                log_debug(f"Event logging error: {e}")

        await self.page.expose_function("pylog", pylog)

        # بعد JavaScript رو inject می‌کنیم
        click_tracking_js = """
(() => {
  // تابع برای ساخت CSS path
  function cssPath(el) {
    if (!el || el.nodeType !== 1) return "";
    const parts = [];
    let current = el;
    
    while (current && current.nodeType === 1 && parts.length < 5) {
      let selector = current.nodeName.toLowerCase();
      
      // اگه ID داره، اون رو استفاده می‌کنیم و تموم
      if (current.id) {
        selector += `#${current.id}`;
        parts.unshift(selector);
        break;
      }
      
      // اگه class داره، اضافه می‌کنیم
      if (current.classList && current.classList.length) {
        const classes = [...current.classList].slice(0, 2).join(".");
        selector += `.${classes}`;
      }
      
      // nth-of-type برای unique کردن
      let siblingIndex = 1;
      let sibling = current.previousElementSibling;
      while (sibling) {
        if (sibling.nodeName === current.nodeName) {
          siblingIndex++;
        }
        sibling = sibling.previousElementSibling;
      }
      selector += `:nth-of-type(${siblingIndex})`;
      
      parts.unshift(selector);
      current = current.parentElement;
    }
    
    return parts.join(" > ");
  }
  
  // listener برای click events
  document.addEventListener("click", (event) => {
    const target = event.target;
    
    // اطلاعات click رو جمع می‌کنیم
    const clickData = {
      type: "user-click",
      tag: target.tagName || "",
      cssPath: cssPath(target),
      text: (target.textContent || "").trim(),
      onclick: target.getAttribute ? (target.getAttribute("onclick") || "") : "",
      x: event.clientX,
      y: event.clientY,
      closestMapArea: !!(target.closest && target.closest("area"))
    };
    
    // به Python ارسال می‌کنیم
    if (window.pylog) {
      window.pylog(clickData);
    }
  }, true);
  
  console.log("Click tracking initialized");
})();
"""

        await self.page.add_init_script(click_tracking_js)
        log_debug("Click tracking attached")

    async def log_page_info(self):
        """لاگ کردن اطلاعات کلی صفحه"""
        if not self.enabled:
            return

        try:
            url = self.page.url
            title = await self.page.title()

            log_info(f"Page info - URL: {url}")
            log_debug(f"Page title: {title}")

        except Exception as e:
            log_debug(f"Failed to get page info: {e}")

    async def wait_and_log_network_idle(self, timeout: int = 5000):
        """انتظار برای network idle و لاگ کردن"""
        if not self.enabled:
            return

        try:
            log_debug("Waiting for network idle...")
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            log_debug("Network idle reached")
        except Exception as e:
            log_debug(f"Network idle timeout: {e}")

    def enable(self):
        """فعال کردن instrumentation"""
        self.enabled = True
        log_debug("Instrumentation enabled")

    def disable(self):
        """غیرفعال کردن instrumentation"""
        self.enabled = False
        log_debug("Instrumentation disabled")

    async def inject_custom_script(self, script: str, name: str = "custom"):
        """
        inject کردن JavaScript سفارشی

        Args:
            script: کد JavaScript
            name: نام script برای logging
        """
        if not self.enabled:
            return

        try:
            await self.page.add_init_script(script)
            log_debug(f"Custom script '{name}' injected")
        except Exception as e:
            log_error(f"Failed to inject script '{name}': {e}")


# تابع کمکی برای ایجاد InstrumentationManager
async def setup_instrumentation(
    page: Page, enabled: bool = True
) -> InstrumentationManager:
    """
    راه‌اندازی instrumentation برای صفحه

    Args:
        page: صفحه playwright
        enabled: فعال بودن instrumentation

    Returns:
        InstrumentationManager instance
    """
    manager = InstrumentationManager(page, enabled)
    await manager.attach_all()
    return manager


# تابع ساده برای attach کردن سریع (سازگاری با کد قدیمی)
async def attach_debug_instrumentation(page: Page, *, enable: bool = True):
    """
    تابع ساده برای سازگاری با کد قدیمی

    Args:
        page: صفحه playwright
        enable: فعال بودن debug
    """
    if not enable:
        return

    manager = InstrumentationManager(page, enabled=True)
    await manager.attach_all()
    return manager
