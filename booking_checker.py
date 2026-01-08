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

        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)

        inactive_divs = page.query_selector_all("div.sc-h5edv-0.cmkkZb")

        date_still_inactive = False

        for div in inactive_divs:
            text = div.inner_text()

            if DAY in text and DATE in text and MONTH in text:
                date_still_inactive = True
                break

        if date_still_inactive:
            print("[-] Date NOT active yet")
            send_alert(
                f"❌ DATE NOT ACTIVE YET\n"
                f"{DAY} {DATE} {MONTH}"
            )
        else:
            print("[!!!] DATE OPEN")
            send_alert(
                f"🚨 DATE OPEN – GO BOOK NOW!\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{page.url}"
            )

        browser.close()


if __name__ == "__main__":
    run()
