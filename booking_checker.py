import requests
from playwright.sync_api import sync_playwright
import os
from datetime import datetime

# ================= CONFIG =================
TARGET_URL = "https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/20260108"
TARGET_DATE_ID = "20260108"

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Date parts
dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY = dt.strftime("%a")
DATE = dt.strftime("%d")
MONTH = dt.strftime("%b")

# =========================================

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = context.new_page()

        print("[*] Checking date status")

        page.goto(TARGET_URL)
        page.wait_for_timeout(15000)

        # --- DATE VISIBILITY CHECK ---
        print("\n=== DATE CELLS FOUND ===\n")

        date_divs = await page.query_selector_all("div.sc-h5edv-0")

        for i, div in enumerate(date_divs, 1):
            div_class = await div.get_attribute("class") or ""

            span_day = await div.query_selector("span.sc-h5edv-1")
            span_date = await div.query_selector("span.sc-h5edv-2")
            span_month = await div.query_selector("span.sc-h5edv-3")

            day = (await span_day.inner_text()).strip() if span_day else "N/A"
            date = (await span_date.inner_text()).strip() if span_date else "N/A"
            month = (await span_month.inner_text()).strip() if span_month else "N/A"

            status = "INACTIVE" if "cmkkZb" in div_class else "ACTIVE"
        
        # --- DECISION ---
        if status=="ACTIVE":
            send_alert(
                f"🚨 DATE OPEN – GO BOOK NOW!\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{page.url}"
            )
        
        # elif inactive_found:
        #     send_alert(
        #         f"❌ DATE NOT ACTIVE YET\n"
        #         f"{DAY} {DATE} {MONTH}"
        #     )
        
        else:
            send_alert(
                f"⚠️ DATE NOT VISIBLE YET (Likely redirected)\n"
                f"{DAY} {DATE} {MONTH}"
            )


        browser.close()


if __name__ == "__main__":
    run()
