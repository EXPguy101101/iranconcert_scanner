/****************************************
 * seat_scanner.js
 * منطق اسکن/کلیک صندلی‌ها + سابمیت خودکار
 * پیکربندی از بیرون تزریق می‌شود: const CONFIG = __CONFIG__;
 * 
 * Author: dibbed
 * GitHub: https://github.com/dibbed
 ****************************************/

(function () {
    // ⚠️ کانفیگ از بیرون تزریق می‌شود (پایتون)
    const CONFIG = __CONFIG__;

    const MARK_ATTR = "data-autoClicked";
    let intervalId = null;
    let submitted = false;

    // حافظهٔ گروه‌هایی که قبلاً انتخاب شده‌اند (برای جلوگیری از کلیک تکراری بین چرخه‌ها)
    const clickedGroupsMemory = new Set();

    // --- کمک‌ها ---
    const toAsciiDigits = (s) =>
        String(s)
            .replace(/[۰-۹]/g, d => "۰۱۲۳۴۵۶۷۸۹".indexOf(d))
            .replace(/[٠-٩]/g, d => "٠١٢٣٤٥٦٧٨٩".indexOf(d));

    const toInt = (v) => {
        if (v == null) return NaN;
        const m = toAsciiDigits(String(v)).match(/-?\d+/);
        return m ? parseInt(m[0], 10) : NaN;
    };

    function inSeatRange(num) {
        if (isNaN(num)) return false;
        const fromOk = CONFIG.SEAT_FROM == null || num >= CONFIG.SEAT_FROM;
        const toOk = CONFIG.SEAT_TO == null || num <= CONFIG.SEAT_TO;
        return fromOk && toOk;
    }

    function getRowNumber(rowEl) {
        const idNum = toInt(rowEl.id || "");
        if (!isNaN(idNum)) return idNum;
        const hdr = rowEl.querySelector(".seatRowHeader");
        if (hdr) {
            const n = toInt(hdr.textContent);
            if (!isNaN(n)) return n;
        }
        return null;
    }

    // فقط chairActive و کلیک‌نشده و فعال
    function isAvailable(seat) {
        if (!seat.classList.contains("chairActive")) return false;
        if (seat.getAttribute(MARK_ATTR) === "1") return false;
        if (seat.hasAttribute("disabled") || seat.getAttribute("aria-disabled") === "true") return false;
        return true;
    }

    function getSeatNumber(seat) {
        // اولویت با attributeهایی مثل n یا data-n
        const nAttr = seat.getAttribute("n") ?? seat.getAttribute("data-n");
        const byAttr = toInt(nAttr);
        if (!isNaN(byAttr)) return byAttr;
        // بعد متن
        return toInt(seat.textContent);
    }

    function startsAfterAisle(seat) {
        const comp = getComputedStyle(seat);
        const ml = comp.marginLeft || seat.style.marginLeft || seat.style["Margin-Left"];
        const px = parseFloat(ml);
        return !isNaN(px) && px > CONFIG.AISLE_MARGIN_PX;
    }

    function getRowSeats(rowEl) {
        // فقط عناصر صندلی (هر چی کلاسش شامل "chair" هست) و نه header
        return [...rowEl.querySelectorAll('[class*="chair"]')].filter(el => !el.classList.contains("seatRowHeader"));
    }

    // تقسیم ردیف به «سگمنت»‌ها: بخش‌هایی بین راهروها
    function splitIntoSegments(seats) {
        const segs = [];
        let cur = [];
        for (const s of seats) {
            if (startsAfterAisle(s)) {
                if (cur.length) segs.push(cur);
                cur = [];
            }
            cur.push(s);
        }
        if (cur.length) segs.push(cur);
        return segs;
    }

    // پیدا کردن گروه‌های دقیقاً چسبیده و متوالی داخل یک سگمنت
    function findGroupsInSegment(seg, size, rowNumber) {
        const out = [];
        // از روی indexهای پشت‌سرهمِ خودِ سگمنت می‌بریم (strict adjacency)
        let i = 0;
        while (i + size <= seg.length) {
            const windowSeats = seg.slice(i, i + size);

            // همه داخل بازه و قابل خرید باشند
            const nums = windowSeats.map(getSeatNumber);
            const allInRange = nums.every(n => inSeatRange(n));
            const allAvail = windowSeats.every(isAvailable);

            // شماره‌ها دقیقاً متوالی: n, n+1, n+2, ...
            let numbersConsecutive = true;
            for (let k = 1; k < nums.length; k++) {
                if (isNaN(nums[k - 1]) || isNaN(nums[k]) || nums[k] !== nums[k - 1] + 1) {
                    numbersConsecutive = false; break;
                }
            }

            if (allInRange && allAvail && numbersConsecutive) {
                const key = `${rowNumber}:${nums.join(",")}`;
                if (!clickedGroupsMemory.has(key)) {
                    out.push({ group: windowSeats, key, nums });
                    // اگر نخواهیم هم‌پوشانی، از بعدِ این گروه می‌پریم
                    if (CONFIG.AVOID_OVERLAP_IN_SCAN) {
                        i += size;
                        continue;
                    }
                }
            }

            // در حالت عادی یک قدم جلو می‌رویم (برای امکان هم‌پوشانی)
            i += 1;
        }
        return out;
    }

    function findConsecutiveGroupsInRow(rowEl, size, rowNumber) {
        const seats = getRowSeats(rowEl);
        const segments = splitIntoSegments(seats);
        const results = [];
        for (const seg of segments) {
            const found = findGroupsInSegment(seg, size, rowNumber);
            for (const f of found) results.push(f);
        }
        return results;
    }

    function clickGroup(group, rowNum, key, nums) {
        group.forEach(seat => {
            seat.setAttribute(MARK_ATTR, "1");
            seat.click();
            try {
                seat.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
            } catch (e) { }
        });
        clickedGroupsMemory.add(key);
        console.log(`✅ Row ${rowNum} — Seats ${nums.join(", ")} (consecutive & adjacent)`);
    }

    // پیدا کردن و کلیک روی دکمه «ثبت سفارش»
    function findSubmitButton() {
        if (CONFIG.SUBMIT_SELECTOR) {
            const el = document.querySelector(CONFIG.SUBMIT_SELECTOR);
            if (el) return el;
        }
        const byOnclick = document.querySelector('button[onclick*="IsValidSelectedSeats"]');
        if (byOnclick) return byOnclick;
        const byText = [...document.querySelectorAll("button, .btn, [role=button]")]
            .find(b => (b.textContent || "").trim().includes("ثبت سفارش"));
        return byText || null;
    }

    function submitAndStop() {
        if (submitted) return;
        submitted = true;
        const btn = findSubmitButton();
        if (!btn) {
            console.warn("⚠️ Submit button not found. Scanner stopped, but not submitted.");
            __seatScannerStop(true);
            return;
        }
        setTimeout(() => {
            try {
                btn.click();
                btn.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
                console.log("🛒 Submit button clicked successfully.");
            } catch (e) {
                console.warn("⚠️ Error clicking submit button:", e);
            } finally {
                __seatScannerStop(true);
            }
        }, CONFIG.BEFORE_SUBMIT_DELAY_MS);
    }

    function scanOnce() {
        if (submitted) return;

        const rows = [...document.querySelectorAll(".seatRow")];
        const rowMap = new Map(rows.map(r => [getRowNumber(r), r]));

        const from = Math.max(1, CONFIG.ROW_FROM);
        const to = Math.min(36, CONFIG.ROW_TO);

        let clickedGroups = 0;

        for (let r = from; r <= to; r++) {
            const rowEl = rowMap.get(r);
            if (!rowEl) continue;

            const groups = findConsecutiveGroupsInRow(rowEl, CONFIG.GROUP_SIZE, r);
            for (const { group, key, nums } of groups) {
                clickGroup(group, r, key, nums);
                clickedGroups++;
                if (clickedGroups >= CONFIG.GROUPS_TO_CLICK) {
                    if (CONFIG.AUTO_SUBMIT) submitAndStop();
                    return;
                }
            }
        }

        if (clickedGroups === 0) {
            console.log(`⏳ No consecutive groups found (rows ${from}..${to} | seats ${CONFIG.SEAT_FROM ?? "-"}..${CONFIG.SEAT_TO ?? "-"})`);
        }
    }

    // کنترل‌ها
    window.__seatScannerStop = function (loud = false) {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
        if (loud) console.log("⏹️ Scanner/automation completely stopped.");
    };

    window.__seatScannerStart = function () {
        if (submitted) {
            console.log("⚠️ Already submitted; restart is not logical.");
            return;
        }
        if (intervalId) {
            console.log("Scanner is already active.");
            return;
        }
        scanOnce();
        intervalId = setInterval(scanOnce, CONFIG.SCAN_INTERVAL_MS);
        console.log("▶️ Scanner started. To stop: __seatScannerStop()");
    };

    window.__clearSeatMemory = function () {
        clickedGroupsMemory.clear();
        console.log("🧹 Selected groups memory cleared.");
    };

    // شروع خودکار
    window.__seatScannerStart();
})();