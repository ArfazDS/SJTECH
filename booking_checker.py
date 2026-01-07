import time
import random
import requests
import os
import re
from playwright.sync_api import sync_playwright
from datetime import datetime

# ================= CONFIG =================

TARGET_DATE_ID = "20260108"  # YYYYMMDD
TARGET_URL = f"https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/{TARGET_DATE_ID}"

CHECK_INTERVAL_MIN = 30
CHECK_INTERVAL_MAX = 60

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ==========================================

dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
FORMATTED_DATE = dt.strftime("%a %d %b %Y")

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        timeout=10
    )
    print("Telegram:", response.text)

def main():
    print("[*] BookMyShow Date Monitor Started")
    print("[*] Target URL:", TARGET_URL)

    send_telegram(f"🤖 Monitoring started for {FORMATTED_DATE}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        try:
            while True:
                try:
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)

                    final_url = page.url
                    match = re.search(r"(\d{8})$", final_url)

                    # ---------- Redirect check ----------
                    if not match or match.group(1) != TARGET_DATE_ID:
                        print("[-] Redirected → date not open")

                    else:
                        # ---------- Showtime detection ----------
                        showtimes = page.query_selector_all(
                            "a[data-id='showtime'], button[data-testid='showtime']"
                        )

                        if showtimes:
                            send_telegram(
                                f"🚨 BOOKINGS OPEN!\n\n"
                                f"Date: {FORMATTED_DATE}\n"
                                f"Link: {final_url}"
                            )
                            break
                        else:
                            print("[-] Date visible but no shows yet")

                except Exception as e:
                    print("[!] Error:", e)

                sleep_time = random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Stopped by user")

        finally:
            browser.close()

if __name__ == "__main__":
    main()
