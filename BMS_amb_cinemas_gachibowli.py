import requests
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# ================= CONFIG =================
TARGET_DATE_ID = "20260109"
TARGET_URL = f"https://in.bookmyshow.com/cinemas/hyderabad/amb-cinemas-gachibowli/buytickets/AMBH/{TARGET_DATE_ID}"
Movie_Name = "The Raja Saab"
Language = "Hindi"

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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        print("[*] Navigating...")
        page.goto(TARGET_URL)
        page.wait_for_timeout(10000)
        curr = page.url
        print("[*] Final URL:", curr)
        
        language_found = False
        movie_cards = page.locator(
            "div.ReactVirtualized__Grid__innerScrollContainer > div"
        )
        count = movie_cards.count()

        for i in range(count):
            card = movie_cards.nth(i)
            card_text = (card.inner_text()).lower()

            if Movie_Name.lower() in card_text:
                movie_found = True

                # Look for language ONLY inside this movie card
                if Language.lower() in card_text:
                    language_found = True

                break  # stop once movie is found

        if TARGET_DATE_ID in curr and movie_found and language_found:
            send_alert(
                f"🚨 DATE OPEN & {Movie_Name} ({Language}) AVAILABLE – GO BOOK NOW!\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{curr}"
            )

        elif TARGET_DATE_ID in curr and movie_found and not language_found:
            send_alert(
                f"⚠️ DATE OPEN & {Movie_Name} FOUND, but ({Language}) NOT AVAILABLE\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{curr}"
            )

        elif TARGET_DATE_ID in curr and not movie_found:
            send_alert(
                f"🚨 DATE OPEN, but {Movie_Name} NOT LISTED YET\n"
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