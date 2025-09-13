# -*- coding: utf-8 -*-
"""
IranConcert Scanner - Main Entry Point
اسکنر خودکار ایران کنسرت

این فایل نقطه ورود اصلی برنامه هست که تمام کامپوننت‌ها رو به هم وصل می‌کنه

Author: dibbed
GitHub: https://github.com/dibbed
"""

import asyncio
import sys
from pathlib import Path

# اضافه کردن src به path برای import ها
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from browser import BrowserManager, setup_instrumentation
from config import load_config
from scanner import AreaSelector, DateTimeHandler, JSInjector, SeatMapDetector
from utils import (
    log_critical,
    log_debug,
    log_error,
    log_info,
    log_warning,
    setup_logger,
)


class IranConcertScanner:
    """
    کلاس اصلی اسکنر ایران کنسرت

    این کلاس تمام مراحل اسکن رو مدیریت می‌کنه:
    از بارگذاری config تا اجرای نهایی
    """

    def __init__(self):
        """راه‌اندازی اولیه اسکنر"""
        self.config = None
        self.browser_manager = None
        self.page = None

        log_debug("IranConcertScanner initialized")

    async def run(self):
        """اجرای کامل فرآیند اسکن"""
        try:
            log_info("Starting IranConcert Scanner...")

            # مرحله 1: بارگذاری تنظیمات
            await self._load_configuration()

            # مرحله 2: راه‌اندازی browser
            await self._setup_browser()

            # مرحله 3: رفتن به صفحه
            await self._navigate_to_page()

            # مرحله 4: کلیک روی datetime
            await self._select_datetime()

            # مرحله 5: انتخاب section
            await self._select_section()

            # مرحله 6: تزریق و اجرای scanner
            await self._run_seat_scanner()

            # مرحله 7: انتظار برای کاربر
            await self._wait_for_user()

        except KeyboardInterrupt:
            log_info("Scanner stopped by user (Ctrl+C)")
        except Exception as e:
            log_critical(f"Scanner failed with error: {e}")
            raise
        finally:
            await self._cleanup()

    async def _load_configuration(self):
        """بارگذاری و تنظیم configuration"""
        log_info("Loading configuration...")

        try:
            self.config = load_config()

            # تنظیم logger بر اساس config
            setup_logger(
                log_file=self.config.log_file,
                console_level=self.config.log_level,
                file_level="DEBUG",
            )

            log_info("Configuration loaded successfully")
            log_debug(f"Target URL: {self.config.url}")
            log_debug(f"Target datetime: {self.config.datetime}")

        except Exception as e:
            log_error(f"Failed to load configuration: {e}")
            raise

    async def _setup_browser(self):
        """راه‌اندازی browser و instrumentation"""
        log_info("Setting up browser...")

        try:
            # ایجاد browser manager
            self.browser_manager = BrowserManager(self.config)
            await self.browser_manager.start()

            # دریافت page
            self.page = await self.browser_manager.get_page()

            # تنظیم instrumentation اگه debug فعال باشه
            if self.config.debug:
                await setup_instrumentation(self.page, enabled=True)
                log_debug("Debug instrumentation enabled")

            log_info("Browser setup completed")

        except Exception as e:
            log_error(f"Browser setup failed: {e}")
            raise

    async def _navigate_to_page(self):
        """رفتن به صفحه مورد نظر"""
        log_info(f"Navigating to: {self.config.url}")

        try:
            await self.browser_manager.navigate_to_url()
            log_info("Navigation completed successfully")

        except Exception as e:
            log_error(f"Navigation failed: {e}")
            raise

    async def _select_datetime(self):
        """انتخاب datetime مورد نظر"""
        log_info(f"Selecting datetime: {self.config.datetime}")

        try:
            datetime_handler = DateTimeHandler(self.page)

            # سعی می‌کنیم با retry کلیک کنیم
            success = await datetime_handler.click_datetime_with_retry(
                self.config.datetime, max_retries=3
            )

            if not success:
                raise Exception(f"Could not click datetime: {self.config.datetime}")

            log_info("Datetime selected successfully")

            # کمی صبر می‌کنیم تا صفحه بروزرسانی بشه
            timing = self.config.timing.after_datetime_click_ms
            await self.page.wait_for_timeout(timing)

            # کمی scroll می‌کنیم تا area ها نمایان بشن
            await self.page.mouse.wheel(0, 800)

        except Exception as e:
            log_error(f"Datetime selection failed: {e}")
            raise

    async def _select_section(self):
        """انتخاب section مناسب"""
        log_info("Selecting section...")

        try:
            area_selector = AreaSelector(self.page)

            # چک می‌کنیم که area داریم یا نه
            try:
                await self.page.wait_for_selector(
                    "map area", state="attached", timeout=6000
                )
                log_debug("Map areas detected, proceeding with section selection")

                # انتخاب بهترین area
                area_info = await area_selector.find_best_area(
                    self.config.section_preferences
                )

                if not area_info:
                    raise Exception("No suitable section found")

                # کلیک روی area
                success = await area_selector.click_area(area_info)

                if not success:
                    raise Exception("Failed to click on selected area")

                log_info(f"Section selected: {area_info.get('part_id', 'unknown')}")

            except Exception:
                # اگه area نداشتیم، ممکنه seat map مستقیم موجود باشه
                log_debug("No map areas found, checking for direct seat map")

                seat_detector = SeatMapDetector(self.page)
                if not await seat_detector.wait_for_seatmap(timeout_ms=6000):
                    raise Exception(
                        "Neither map areas nor seat container found"
                    ) from None

                log_info("Direct seat map detected, skipping section selection")

            # کمی صبر می‌کنیم تا section لود بشه
            timing = self.config.timing.post_section_action_ms
            await self.page.wait_for_timeout(timing)

        except Exception as e:
            log_error(f"Section selection failed: {e}")
            raise

    async def _run_seat_scanner(self):
        """تزریق و اجرای seat scanner"""
        log_info("Setting up seat scanner...")

        try:
            # اول مطمئن می‌شیم که seat map آماده هست
            seat_detector = SeatMapDetector(self.page)

            if not await seat_detector.wait_for_seatmap():
                # اگه هنوز آماده نبود، کمی صبر می‌کنیم
                log_debug("Seat map not ready, waiting for network idle...")

                try:
                    await self.page.wait_for_load_state("networkidle", timeout=8000)
                except:
                    pass

                # کمی بیشتر scroll می‌کنیم
                await self.page.mouse.wheel(0, 1200)

                # دوباره چک می‌کنیم
                if not await seat_detector.wait_for_seatmap(timeout_ms=15000):
                    raise Exception("Seat map still not detected after waiting")

            log_info("Seat map is ready, injecting scanner...")

            # تزریق JavaScript scanner
            js_injector = JSInjector(self.page)

            success = await js_injector.inject_scanner(self.config.seat_config)
            if not success:
                raise Exception("Failed to inject seat scanner")

            log_info("Seat scanner injected and started successfully!")

            # نمایش راهنما برای کاربر
            self._show_scanner_help()

        except Exception as e:
            log_error(f"Seat scanner setup failed: {e}")
            raise

    def _show_scanner_help(self):
        """نمایش راهنمای استفاده از scanner"""

        # رنگ‌های ANSI
        class Colors:
            GREEN = "\033[92m"
            YELLOW = "\033[93m"
            CYAN = "\033[96m"
            BOLD = "\033[1m"
            END = "\033[0m"

        print(f"\n{Colors.CYAN}{'=' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.GREEN}🎯 Seat Scanner is now running!{Colors.END}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.END}")
        print(
            f"{Colors.YELLOW}Interactive controls are available in terminal{Colors.END}"
        )
        print(f"{Colors.CYAN}{'=' * 60}{Colors.END}\n")

    async def _wait_for_user(self):
        """انتظار برای کاربر و کنترل scanner"""
        log_debug("Starting interactive control mode...")

        # رنگ‌های ANSI
        class Colors:
            RED = "\033[91m"
            GREEN = "\033[92m"
            YELLOW = "\033[93m"
            BLUE = "\033[94m"
            PURPLE = "\033[95m"
            CYAN = "\033[96m"
            WHITE = "\033[97m"
            BOLD = "\033[1m"
            END = "\033[0m"

        def print_colored(text, color):
            print(f"{color}{text}{Colors.END}")

        def show_help():
            print_colored("\n" + "=" * 60, Colors.CYAN)
            print_colored("🎮 SCANNER CONTROL PANEL", Colors.BOLD + Colors.YELLOW)
            print_colored("=" * 60, Colors.CYAN)
            print_colored("Commands:", Colors.WHITE)
            print_colored("  [s] - 🛑 Stop Scanner", Colors.RED)
            print_colored("  [r] - ▶️  Restart Scanner", Colors.GREEN)
            print_colored("  [c] - 🧹 Clear Memory", Colors.BLUE)
            print_colored("  [h] - ❓ Show Help", Colors.PURPLE)
            print_colored("  [q] - 🚪 Quit Program", Colors.YELLOW)
            print_colored("=" * 60, Colors.CYAN)
            print_colored("Enter command: ", Colors.WHITE, end="")

        try:
            show_help()

            while True:
                try:
                    # دریافت input به صورت non-blocking
                    import select
                    import sys
                    import termios
                    import tty

                    # تنظیم terminal برای خواندن کاراکتر واحد
                    old_settings = termios.tcgetattr(sys.stdin)
                    tty.setraw(sys.stdin.fileno())

                    # انتظار برای input
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        command = sys.stdin.read(1).lower()
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                        if command == "s":
                            print_colored("\n🛑 Stopping scanner...", Colors.RED)
                            await self.page.evaluate("__seatScannerStop()")
                            print_colored("✅ Scanner stopped!", Colors.GREEN)

                        elif command == "r":
                            print_colored("\n▶️ Restarting scanner...", Colors.GREEN)
                            await self.page.evaluate("__seatScannerStart()")
                            print_colored("✅ Scanner restarted!", Colors.GREEN)

                        elif command == "c":
                            print_colored("\n🧹 Clearing memory...", Colors.BLUE)
                            await self.page.evaluate("__clearSeatMemory()")
                            print_colored("✅ Memory cleared!", Colors.GREEN)

                        elif command == "h":
                            show_help()
                            continue

                        elif command == "q":
                            print_colored("\n🚪 Exiting program...", Colors.YELLOW)
                            raise KeyboardInterrupt

                        else:
                            print_colored(
                                f"\n❌ Unknown command: {command}", Colors.RED
                            )

                        print_colored(
                            "\nEnter command (h for help): ", Colors.WHITE, end=""
                        )
                    else:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        await asyncio.sleep(0.1)

                except (ImportError, OSError):
                    # Fallback برای سیستم‌هایی که termios ندارن (مثل Windows)
                    print_colored("\n⌨️ Enter command: ", Colors.WHITE, end="")
                    command = input().lower().strip()

                    if command == "s" or command == "stop":
                        print_colored("🛑 Stopping scanner...", Colors.RED)
                        await self.page.evaluate("__seatScannerStop()")
                        print_colored("✅ Scanner stopped!", Colors.GREEN)

                    elif command == "r" or command == "restart":
                        print_colored("▶️ Restarting scanner...", Colors.GREEN)
                        await self.page.evaluate("__seatScannerStart()")
                        print_colored("✅ Scanner restarted!", Colors.GREEN)

                    elif command == "c" or command == "clear":
                        print_colored("🧹 Clearing memory...", Colors.BLUE)
                        await self.page.evaluate("__clearSeatMemory()")
                        print_colored("✅ Memory cleared!", Colors.GREEN)

                    elif command == "h" or command == "help":
                        show_help()

                    elif command == "q" or command == "quit":
                        print_colored("🚪 Exiting program...", Colors.YELLOW)
                        raise KeyboardInterrupt from None

                    else:
                        print_colored(f"❌ Unknown command: {command}", Colors.RED)
                        print_colored("Type 'h' for help", Colors.PURPLE)

        except KeyboardInterrupt:
            print_colored("\n\n👋 Goodbye!", Colors.YELLOW)
            log_info("User requested exit")
            raise

    async def _cleanup(self):
        """تمیز کردن منابع"""
        log_debug("Cleaning up resources...")

        try:
            if self.browser_manager:
                await self.browser_manager.close()
                log_debug("Browser closed successfully")
        except Exception as e:
            log_warning(f"Error during cleanup: {e}")


async def main():
    """
    تابع اصلی برنامه

    این تابع scanner رو راه‌اندازی می‌کنه و اجرا می‌کنه
    """
    scanner = IranConcertScanner()
    await scanner.run()


def cli_main():
    """
    نقطه ورود CLI

    این تابع برای اجرای برنامه از command line استفاده می‌شه
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\033[93m👋 Goodbye!\033[0m")
    except Exception as e:
        print(f"\n\033[91m❌ Error: {e}\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
