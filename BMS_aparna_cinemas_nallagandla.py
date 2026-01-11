import requests
import time as time_module
from datetime import datetime, time
from playwright.sync_api import sync_playwright
import re

# ================= CONFIG =================
TARGET_DATE_ID = "20260111"
# -------- PRE-FLIGHT DATE CHECK --------
target_date = datetime.strptime(TARGET_DATE_ID, "%Y%m%d").date()
today = date.today()

if target_date < today:
    print(
        f"[SKIPPED] Target date {target_date} has already passed. "
        f"Today is {today}. Exiting."
    )
    exit(0)

TARGET_URL = f"https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/{TARGET_DATE_ID}"
Movie_Name = "The Housemaid"
Language = "English"
SEAT_TYPE = "GOLD"

TELEGRAM_TOKEN = "8263034254:AAFUuLLB6a5XqG9R7PZVZkH1vNQQivfhn6U"
TELEGRAM_CHAT_ID = "684803039"
dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY = dt.strftime("%a")
DATE = dt.strftime("%d")
MONTH = dt.strftime("%b")
START_TIME = time(11, 0)   # 11:00 AM
END_TIME = time(16, 0)     # 4:00 PM
# =========================================

def send_alert(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram disabled]")
        print(msg)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("Telegram response:", r.text)

def parse_time(t):
    match = re.search(r"\b\d{1,2}:\d{2}\s?(AM|PM)\b", t)
    if not match:
        return None
    return datetime.strptime(match.group(), "%I:%M %p").time()

def run():
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
        print("[*] Navigating...")
        page.goto(TARGET_URL)
        page.wait_for_timeout(10000)
        curr = page.url
        print("[*] Final URL:", curr)
        movie_found = False
        language_found = False
        valid_timings = []

        # MAIN CONTAINER
        container = page.locator(
            "div.ReactVirtualized__Grid__innerScrollContainer"
        )
        # MOVIE CARDS
        movie_cards = container.locator("div.sc-1412vr2-0.knoRMk")
        count = movie_cards.count()
        for i in range(count):
            card = movie_cards.nth(i)
            # ---- MOVIE NAME + LANGUAGE ----
            info_div = card.locator("div.sc-1412vr2-1.kgIDke")
            info_text = info_div.inner_text()
            info_text = info_text.lower()
            if Movie_Name.lower() in info_text:
                movie_found = True
                if Language.lower() in info_text:
                    language_found = True
                else:
                    break
                # ---- SHOW TIMINGS ----
                timings_container = card.locator(
                    "div.sc-19dkgz1-0.cVUDLk"
                )
                shows = timings_container.locator(
                    "div.sc-1skzbbo-0.eBWTPs"
                )
                final_timings = []

                for j in range(shows.count()):
                    show = shows.nth(j)

                    # Skip unavailable timings
                    if show.locator("div.sc-yr56qh-0.dSFYKI").count() > 0:
                        continue

                    show_time_text = show.inner_text().strip()
                    show_time = parse_time(show_time_text)
                    if not show_time:
                        continue

                    if not (START_TIME <= show_time <= END_TIME):
                        continue

                    print(f"[+] Checking seats for {show_time_text}")

                    # --- CLICK SHOW TIME ---
                    show.click()
                    page.wait_for_timeout(7000)

                    # --- CHECK SEAT TYPE ---
                    seat_items = page.locator("li.sc-1atac75-2.LTrUk")
                    seat_count = seat_items.count()

                    seat_available = False

                    for k in range(seat_count):
                        seat = seat_items.nth(k)
                        seat_text = seat.inner_text().upper()

                        if SEAT_TYPE.upper() in seat_text:
                            if "SOLD OUT" not in seat_text:
                                seat_available = True
                            break

                    # --- GO BACK ---
                    page.go_back()
                    page.wait_for_timeout(5000)

                    if seat_available:
                        final_timings.append(show_time.strftime("%I:%M %p"))
                        print(f"    ✓ {SEAT_TYPE} available")
                    else:
                        print(f"    ✗ {SEAT_TYPE} sold out")

                break  # stop after matching movie

        # ---- ALERT LOGIC ----
        if (
            TARGET_DATE_ID in curr
            and movie_found
            and language_found
            and final_timings
        ):
            timings_str = ", ".join(final_timings)
            send_alert(
                f"🚨 DATE OPEN – SEATS AVAILABLE!\n"
                f"{Movie_Name} ({Language})\n"
                f"{DAY} {DATE} {MONTH}\n"
                f"{SEAT_TYPE} Timings: {timings_str}\n"
                f"{curr}"
            )

        browser.close()

if __name__ == "__main__":
    run()
