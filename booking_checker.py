import requests
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# ================= CONFIG =================
TARGET_DATE_ID = "20260109"
TARGET_URL = f"https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/{TARGET_DATE_ID}"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY = dt.strftime("%a")
DATE = dt.strftime("%d")
MONTH = dt.strftime("%b")
print("TARGET:", DAY, DATE, MONTH)

# =========================================

def send_alert(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram disabled]")
        print(msg)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("Telegram response:", r.text)

def run():
    with sync_playwright() as p:
        # browser = p.chromium.launch(
        #     headless=True,  # MUST be true on GitHub
        #     args=[
        #         "--no-sandbox",
        #         "--disable-dev-shm-usage",
        #         "--disable-gpu",
        #         "--disable-blink-features=AutomationControlled",
        #     ],
        # )
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # context = browser.new_context(
        #     user_agent=(
        #         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        #         "AppleWebKit/537.36 (KHTML, like Gecko) "
        #         "Chrome/120.0.0.0 Safari/537.36"
        #     )
        # )
        page = context.new_page()
        print("[*] Navigating...")
        page.goto(TARGET_URL)
        page.wait_for_timeout(10000)
        curr = page.url
        print("[*] Final URL:", curr)
        
        if TARGET_DATE_ID in curr:
            send_alert(
                f"🚨 DATE OPEN – GO BOOK NOW!\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{curr}"
            )
        else:
            send_alert(
                f"❌ DATE NOT OPEN YET\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"Redirected to: {curr}"
            )
        
        browser.close()

if __name__ == "__main__":
    run()
