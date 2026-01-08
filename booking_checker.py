import time
import random
import requests
from playwright.sync_api import sync_playwright
import os
from datetime import datetime

# ================= CONFIG =================
TARGET_URL = "https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/20260108"
TARGET_DATE_ID = "20260108"

CHECK_INTERVAL_MIN = 10
CHECK_INTERVAL_MAX = 15

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Date parts
dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY, DATE, MONTH = dt.strftime("%a"), dt.strftime("%d"), dt.strftime("%b")

# ==========================================

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("[*] Monitoring started")
        send_alert(f"🤖 Monitoring {DAY} {DATE} {MONTH}")

        try:
            while True:
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)

                date_divs = page.query_selector_all("div.sc-h5edv-0")
                matched = False

                for div in date_divs:
                    span_day = div.query_selector("span.sc-h5edv-1.lbMdAA")
                    span_date = div.query_selector("span.sc-h5edv-2.hdBsYM")
                    span_month = div.query_selector("span.sc-h5edv-3.WDdWY")

                    if not (span_day and span_date and span_month):
                        continue

                    if (
                        span_day.inner_text().strip() == DAY and
                        span_date.inner_text().strip() == DATE and
                        span_month.inner_text().strip() == MONTH
                    ):
                        matched = True
                        div_class = div.get_attribute("class") or ""

                        if "cmkkZb" in div_class:
                            print("[-] Date found but NOT active")
                            send_alert(
                                f"❌ DATE NOT ACTIVE YET\n"
                                f"{DAY} {DATE} {MONTH}"
                            )
                        else:
                            print("[!!!] DATE ACTIVE")
                            send_alert(
                                f"🚨 DATE ACTIVE – GO BOOK NOW!\n"
                                f"{DAY} {DATE} {MONTH}\n"
                                f"{page.url}"
                            )
                            return  # STOP SCRIPT AFTER SUCCESS
                        break

                if not matched:
                    print("[-] Date not visible yet")

                time.sleep(random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX))

        finally:
            browser.close()


if __name__ == "__main__":
    run()
