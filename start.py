#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IranConcert Scanner - Starter
راه‌انداز نهایی پروژه بدون مشکل import

Author: dibbed
"""

import asyncio
import importlib.util
import os
import sys
from pathlib import Path


def load_module_from_path(module_name, file_path):
    """بارگذاری ماژول از مسیر مشخص"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

async def interactive_control(page):
    """کنترل تعاملی scanner"""
    # رنگ‌های ANSI
    class Colors:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        END = '\033[0m'
    
    def print_colored(text, color, end='\n'):
        print(f"{color}{text}{Colors.END}", end=end)
    
    def show_help():
        print_colored("\n" + "="*60, Colors.CYAN)
        print_colored("🎮 SCANNER CONTROL PANEL", Colors.BOLD + Colors.YELLOW)
        print_colored("="*60, Colors.CYAN)
        print_colored("Commands:", Colors.WHITE)
        print_colored("  [s] - 🛑 Stop Scanner", Colors.RED)
        print_colored("  [r] - ▶️  Restart Scanner", Colors.GREEN)
        print_colored("  [c] - 🧹 Clear Memory", Colors.BLUE)
        print_colored("  [h] - ❓ Show Help", Colors.PURPLE)
        print_colored("  [q] - 🚪 Quit Program", Colors.YELLOW)
        print_colored("="*60, Colors.CYAN)
        print_colored("Enter command: ", Colors.WHITE, end="")
    
    try:
        show_help()
        
        while True:
            try:
                print_colored("\n⌨️ Enter command: ", Colors.WHITE, end="")
                command = input().lower().strip()
                
                if command == 's' or command == 'stop':
                    print_colored("🛑 Stopping scanner...", Colors.RED)
                    await page.evaluate("__seatScannerStop()")
                    print_colored("✅ Scanner stopped!", Colors.GREEN)
                    
                elif command == 'r' or command == 'restart':
                    print_colored("▶️ Restarting scanner...", Colors.GREEN)
                    await page.evaluate("__seatScannerStart()")
                    print_colored("✅ Scanner restarted!", Colors.GREEN)
                    
                elif command == 'c' or command == 'clear':
                    print_colored("🧹 Clearing memory...", Colors.BLUE)
                    await page.evaluate("__clearSeatMemory()")
                    print_colored("✅ Memory cleared!", Colors.GREEN)
                    
                elif command == 'h' or command == 'help':
                    show_help()
                    
                elif command == 'q' or command == 'quit':
                    print_colored("🚪 Exiting program...", Colors.YELLOW)
                    raise KeyboardInterrupt
                    
                else:
                    print_colored(f"❌ Unknown command: {command}", Colors.RED)
                    print_colored("Type 'h' for help", Colors.PURPLE)
            
            except Exception as e:
                print_colored(f"❌ Error: {e}", Colors.RED)
                await asyncio.sleep(0.1)
                
    except KeyboardInterrupt:
        print_colored("\n\n👋 Goodbye!", Colors.YELLOW)
        raise


def main():
    """اجرای اسکنر"""
    # رنگ‌های ANSI
    class Colors:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        END = '\033[0m'
    
    print(f"{Colors.BOLD}{Colors.CYAN}🚀 Starting IranConcert Scanner...{Colors.END}")
    
    # تنظیم مسیرها
    project_root = Path(__file__).parent
    
    # تغییر working directory
    os.chdir(project_root)
    
    try:
        # بارگذاری config
        config_module = load_module_from_path("config", project_root / "config.py")
        CONFIG = config_module.CONFIG
        
        print(f"{Colors.GREEN}✅ Config loaded: {Colors.YELLOW}{CONFIG['url'][:50]}...{Colors.END}")
        
        # اجرای اسکنر با playwright
        async def run_scanner():
            from playwright.async_api import async_playwright

            # رنگ‌های ANSI
            class Colors:
                RED = '\033[91m'
                GREEN = '\033[92m'
                YELLOW = '\033[93m'
                BLUE = '\033[94m'
                PURPLE = '\033[95m'
                CYAN = '\033[96m'
                WHITE = '\033[97m'
                BOLD = '\033[1m'
                END = '\033[0m'
            
            print(f"{Colors.BLUE}🌐 Starting browser...{Colors.END}")
            
            # تنظیمات از config
            url = CONFIG["url"]
            target_dt = CONFIG["datetime"]
            headful = CONFIG.get("headful", True)
            cookies = CONFIG.get("cookies", [])
            seat_config = CONFIG.get("seat_config", {})
            debug = CONFIG.get("debug", True)
            use_persistent = CONFIG.get("use_persistent", True)
            user_agent = CONFIG.get("user_agent")
            timing = CONFIG.get("timing", {})
            
            def _t(key: str, default: int) -> int:
                """دریافت timing value"""
                return timing.get(key, default)
            
            async with async_playwright() as pw:
                context = None
                browser = None
                
                try:
                    # راه‌اندازی browser
                    if use_persistent:
                        # انتخاب user agent
                        selected_user_agent = user_agent or (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/140.0.0.0 Safari/537.36"
                        )
                        
                        if user_agent:
                            print(f"{Colors.PURPLE}🔧 Using custom user agent: {Colors.WHITE}{user_agent[:50]}...{Colors.END}")
                        else:
                            print(f"{Colors.CYAN}🔄 Using default Chrome user agent{Colors.END}")
                        
                        context = await pw.chromium.launch_persistent_context(
                            user_data_dir="/tmp/iranconcert",
                            headless=not headful,
                            locale="fa-IR",
                            user_agent=selected_user_agent,
                        )
                    else:
                        # انتخاب user agent
                        selected_user_agent = user_agent or (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/140.0.0.0 Safari/537.36"
                        )
                        
                        if user_agent:
                            print(f"{Colors.PURPLE}🔧 Using custom user agent: {Colors.WHITE}{user_agent[:50]}...{Colors.END}")
                        else:
                            print(f"{Colors.CYAN}🔄 Using default Chrome user agent{Colors.END}")
                        
                        browser = await pw.chromium.launch(headless=not headful)
                        context = await browser.new_context(
                            locale="fa-IR",
                            user_agent=selected_user_agent,
                        )
                    
                    # تنظیم کوکی‌ها
                    if cookies:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.hostname or "www.iranconcert.com"
                        
                        for c in cookies:
                            c.setdefault("domain", domain)
                            c.setdefault("path", "/")
                            if "secure" not in c:
                                c["secure"] = True
                            if "sameSite" not in c:
                                c["sameSite"] = "Lax"
                        await context.add_cookies(cookies)
                    
                    # دریافت page
                    page = context.pages[0] if context.pages else await context.new_page()
                    
                    # debug instrumentation
                    if debug:
                        def _on_console(msg):
                            try:
                                if msg.type == "log":
                                    print(f"{Colors.GREEN}[PAGE.LOG] {msg.text}{Colors.END}")
                                elif msg.type == "error":
                                    print(f"{Colors.RED}[PAGE.ERROR] {msg.text}{Colors.END}")
                                elif msg.type == "warning":
                                    print(f"{Colors.YELLOW}[PAGE.WARNING] {msg.text}{Colors.END}")
                                else:
                                    print(f"{Colors.CYAN}[PAGE.{msg.type.upper()}] {msg.text}{Colors.END}")
                            except Exception as e:
                                print(f"{Colors.RED}[PAGE.CONSOLE_ERR] {e}{Colors.END}")
                        page.on("console", _on_console)
                    
                    print(f"{Colors.BLUE}🌐 Navigating to: {Colors.WHITE}{url}{Colors.END}")
                    await page.goto(url, wait_until="domcontentloaded")
                    
                    # کلیک datetime
                    print(f"{Colors.PURPLE}📅 Selecting datetime: {Colors.YELLOW}{target_dt}{Colors.END}")
                    selector = f'time.btn-day[datetime="{target_dt}"]'
                    locator = page.locator(selector)
                    
                    try:
                        await locator.first.wait_for(state="visible", timeout=15000)
                        clickable = locator.first.locator(
                            "xpath=ancestor-or-self::*[self::button or @role='button' or self::a][1]"
                        )
                        if await clickable.count():
                            await clickable.first.click()
                        else:
                            await locator.first.click()
                        print(f"{Colors.GREEN}✅ Clicked on datetime: {Colors.YELLOW}{target_dt}{Colors.END}")
                    except Exception as e:
                        print(f"{Colors.RED}❌ Failed to click datetime: {e}{Colors.END}")
                        return
                    
                    # صبر و scroll
                    await page.wait_for_timeout(_t("after_datetime_click_ms", 900))
                    await page.mouse.wheel(0, 800)
                    
                    # انتخاب section
                    print(f"{Colors.PURPLE}🎯 Selecting section...{Colors.END}")
                    
                    try:
                        await page.wait_for_selector("map area", state="attached", timeout=6000)
                        print(f"{Colors.CYAN}Map areas detected, selecting section...{Colors.END}")
                        
                        # پیدا کردن بزرگ‌ترین area
                        js_code = """
(() => {
  function areaVal(coordsStr) {
    if (!coordsStr) return 0;
    const nums = coordsStr.split(",").map(s => parseFloat(s.trim())).filter(n => !Number.isNaN(n));
    const pts = [];
    for (let i = 0; i + 1 < nums.length; i += 2) pts.push([nums[i], nums[i+1]]);
    if (pts.length < 3) return 0;
    let twiceArea = 0;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [x0, y0] = pts[j]; const [x1, y1] = pts[i];
      twiceArea += (x0 * y1) - (x1 * y0);
    }
    return Math.abs(twiceArea) / 2;
  }
  const areas = Array.from(document.querySelectorAll("map area"));
  const cands = areas.map(el => {
    const oc = (el.getAttribute("onclick") || "");
    const hasAjax = oc.includes("ajax(");
    const hasErr = oc.includes("toastr.error");
    const coords = el.getAttribute("coords") || "";
    const area = areaVal(coords);
    return { el, hasAjax, hasErr, area, oc };
  }).filter(x => x.hasAjax && !x.hasErr && x.area > 0);

  if (!cands.length) return null;
  cands.sort((a, b) => b.area - a.area);
  cands[0].el.setAttribute("data-autopick", "1");
  return cands[0].oc || null;
})();
"""
                        onclick = await page.evaluate(js_code)
                        
                        if onclick:
                            # کلیک روی area
                            await page.eval_on_selector(
                                "map area[data-autopick='1']",
                                "el => el.click()"
                            )
                            print(f"{Colors.GREEN}✅ Section selected{Colors.END}")
                        else:
                            print(f"{Colors.RED}❌ No suitable section found{Colors.END}")
                            return
                            
                    except Exception:
                        print(f"{Colors.YELLOW}No map areas, checking for direct seat map...{Colors.END}")
                        
                        # چک seat map مستقیم
                        seat_selectors = [".seatRow", ".seat-row", "#seatmap", ".seat-map"]
                        found = False
                        for sel in seat_selectors:
                            try:
                                await page.wait_for_selector(sel, state="visible", timeout=3000)
                                print(f"{Colors.GREEN}✅ Direct seat map found: {Colors.CYAN}{sel}{Colors.END}")
                                found = True
                                break
                            except:
                                continue
                        
                        if not found:
                            print(f"{Colors.RED}❌ No seat map found{Colors.END}")
                            return
                    
                    # صبر برای seat map
                    await page.wait_for_timeout(_t("post_section_action_ms", 1300))
                    
                    # تزریق JavaScript
                    print(f"{Colors.PURPLE}💉 Injecting seat scanner...{Colors.END}")
                    
                    js_file = project_root / "assets" / "seat_scanner.js"
                    if not js_file.exists():
                        print(f"{Colors.RED}❌ seat_scanner.js not found{Colors.END}")
                        return
                    
                    with open(js_file, "r", encoding="utf-8") as f:
                        js_code = f.read()
                    
                    import json
                    config_json = json.dumps(seat_config, ensure_ascii=False)
                    full_js = js_code.replace("__CONFIG__", config_json)
                    
                    await page.evaluate(full_js)
                    
                    # رنگ‌های ANSI
                    class Colors:
                        GREEN = '\033[92m'
                        YELLOW = '\033[93m'
                        CYAN = '\033[96m'
                        BOLD = '\033[1m'
                        END = '\033[0m'
                    
                    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
                    print(f"{Colors.BOLD}{Colors.GREEN}🎯 Seat Scanner is now running!{Colors.END}")
                    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
                    print(f"{Colors.YELLOW}Interactive controls are available in terminal{Colors.END}")
                    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")
                    
                    # کنترل رنگی
                    await interactive_control(page)
                        
                finally:
                    try:
                        if browser:
                            await browser.close()
                        elif context:
                            await context.close()
                    except Exception as e:
                        print(f"⚠️ Cleanup warning: {e}")
        
        # اجرا
        asyncio.run(run_scanner())
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.END}")
    except ImportError as e:
        print(f"{Colors.RED}❌ Import Error: {e}{Colors.END}")
        print(f"\n{Colors.CYAN}💡 Install dependencies:{Colors.END}")
        print(f"{Colors.WHITE}pip install -r requirements.txt{Colors.END}")
        print(f"{Colors.WHITE}python -m playwright install{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
