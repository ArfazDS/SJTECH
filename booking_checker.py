import time
import random
import requests
from playwright.sync_api import sync_playwright
import os
import re

# --- CONFIGURATION ---
# The date you WANT (e.g., 09 Jan 2026)
TARGET_URL = "https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/20260109"

# The Date part of the URL to strictly verify (e.g. "20260109")
TARGET_DATE_ID = "20260109"

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
                    page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
                    
                    # 2. Get the Final URL after loading
                    final_url = page.url
                    m = re.search(r"(\d{8})$", final_url)
                    date_str = m.group(1)
                    
                    # 3. Compare: Did we stay on the Target, or did we get bounced?
                    if TARGET_DATE_ID in date_str:
                        # --- SUCCESS: WE STAYED ON JAN 09 ---
                        print(f"[!!!] SUCCESS!")
                        send_alert(f"🚨 DATE OPENED! \nLink: {final_url}")
                        
                        # # Double check content just in case
                        # content = page.content().lower()
                        # if "no shows available" not in content:
                        #     send_alert(f"🚨 DATE OPENED! \nLink: {final_url}")
                        #     break # Stop and exit
                        # else:
                        #     print("[-] URL is correct, but page says 'No Shows'. Keeping watch...")
                    
                    else:
                        # --- FAIL: WE WERE REDIRECTED (likely to Jan 08) ---
                        # Extract the date we were sent to, just for logging
                        redirected_date = final_url.split('/')[-1] if '/' in final_url else "Unknown"
                        print(f"[-] Redirected to {redirected_date}. Target {TARGET_DATE_ID} is still closed.")
                        send_alert("Date not available yet")

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
