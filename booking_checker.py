import time
import random
import requests
from playwright.sync_api import sync_playwright
import os
import re
from datetime import datetime

# --- CONFIGURATION ---
# The date you WANT (e.g., 09 Jan 2026)
TARGET_URL = "https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/20260108"

# The Date part of the URL to strictly verify (e.g. "20260109")
TARGET_DATE_ID = "20260108"
dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
# formatted_date = dt.strftime("%a %d %b")

dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
date_parts = [
    dt.strftime("%a"),  # Fri
    dt.strftime("%d"),  # 09
    dt.strftime("%b"),  # Jan
]

# Telegram Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

print("TOKEN LENGTH:", len(TELEGRAM_TOKEN))
print("TOKEN START:", TELEGRAM_TOKEN[:10])
print("TOKEN END:", TELEGRAM_TOKEN[-5:])


def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("Telegram response:", r.text)


def run():
    with sync_playwright() as p:
        # headless=True is faster. Set to False if you want to watch it.
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"[*] Redirect Monitor Started.")
        print(f"[*] Target: {TARGET_URL}")
        send_alert(f"🤖 Monitoring URL for {TARGET_DATE_ID}. Waiting for redirect to stop...")

        try:
            while True:
                try:
                    # 1. Navigate to the TARGET (Jan 09)
                    # wait_until="domcontentloaded" ensures we wait for the redirect to finish
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
                    
                    # 2. Get the Final URL after loading
                    final_url = page.url
                    # --- DATE CELL DETECTION LOGIC ---

                    date_found_and_active = False
                    
                    # Select all date containers
                    date_divs = page.query_selector_all("div.sc-h5edv-0")
                    
                    for div in date_divs:
                        div_class = div.get_attribute("class") or ""
                    
                        # Skip inactive dates
                        if "cmkkZb" in div_class:
                            continue
                    
                        # Find required spans inside this div
                        span_day = div.query_selector("span.sc-h5edv-1.lbMdAA")
                        span_date = div.query_selector("span.sc-h5edv-2.hdBsYM")
                        span_month = div.query_selector("span.sc-h5edv-3.WDdWY")
                    
                        if not (span_day and span_date and span_month):
                            continue
                    
                        day_text = span_day.inner_text().strip()
                        date_text = span_date.inner_text().strip()
                        month_text = span_month.inner_text().strip()
                    
                        if (
                            day_text == date_parts[0]
                            and date_text == date_parts[1]
                            and month_text == date_parts[2]
                        ):
                            date_found_and_active = True
                            break
                    if date_found_and_active:
                        send_alert(
                            f"🚨 DATE ACTIVE!\n"
                            f"{date_parts[0]} {date_parts[1]} {date_parts[2]}\n"
                            f"Link: {page.url}"
                        )
                        break
                    else:
                        print("[-] Date not active yet")
                        send_alert(
                            f"🚨 DATE NOT ACTIVE!\n"
                            f"{date_parts[0]} {date_parts[1]} {date_parts[2]}\n")



                except Exception as e:
                    print(f"[!] Error checking: {e}")

                # Random wait (20-40s) to avoid IP ban
                sleep_time = random.randint(20, 40)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
