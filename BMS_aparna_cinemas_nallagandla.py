import requests
import time as time_module
from datetime import datetime, time, date
from playwright.sync_api import sync_playwright
import os
import json
import random
from PIL import Image
import time as time_module
import io
import math
import re

# ================= CONFIG =================
with open("config.json", "r") as f:
    config = json.load(f)

TARGET_DATE_ID = config["TARGET_DATE_ID"]
Movie_Name = config["MOVIE_NAME"]
Language = config["LANGUAGE"]

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
SEAT_TYPE = "GOLD"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY = dt.strftime("%a")
DATE = dt.strftime("%d")
MONTH = dt.strftime("%b")
START_TIME = time(10, 0)   # 11:00 AM
END_TIME = time(16, 0)     # 4:00 PM
SEATS_TO_SELECT = 1
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

def is_recliner_available(r, g, b):
    # (Same logic as before)
    bright_enough = g > 130
    not_yellow_or_white = g > (r + 40)
    not_blue = g > (b + 30)
    return bright_enough and not_yellow_or_white and not_blue

def find_recliner_seats(screenshot_bytes, max_seats):
    # (Same logic as before)
    image = Image.open(io.BytesIO(screenshot_bytes))
    pixels = image.load()
    width, height = image.size
    found_seats = []
    scan_height_limit = int(height * 0.25)
    step = 10
    
    print(f"Scanning top {scan_height_limit}px...")
    for y in range(20, scan_height_limit, step):
        if len(found_seats) >= max_seats: break
        for x in range(20, width - 20, step):
            if len(found_seats) >= max_seats: break
            r, g, b = pixels[x, y][:3]
            if is_recliner_available(r, g, b):
                too_close = False
                for fx, fy in found_seats:
                    if math.hypot(x - fx, y - fy) < 40:
                        too_close = True; break
                if not too_close:
                    found_seats.append((x + 10, y + 10))
    return found_seats, width, height

def run():
    with sync_playwright() as p:
        # browser = p.chromium.launch(headless=True)
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ), viewport={"width": 1280, "height": 800}
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
                    if page.get_by_text("Continue").is_visible():
                        page.get_by_text("Continue").click()
                    page.wait_for_timeout(5000)

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
                                page.get_by_role("slider").fill("1")
                                page.get_by_label("Select Seats").click()
                                page.wait_for_timeout(5000)
                        
                                # --- CANVAS LOGIC ---
                                canvas_selector = ".konvajs-content canvas"
                                print("Waiting for seat map canvas...")
                        
                                try:
                                    page.wait_for_selector(canvas_selector, state="visible", timeout=20000)
                                    page.evaluate("window.scrollTo(0, 0)")
                                    time_module.sleep(3) 
                                except:
                                    print("Canvas not found or blocked.")
                                    browser.close()
                                    return
                        
                                canvas_el = page.locator(canvas_selector).first
                                canvas_box = canvas_el.bounding_box()
                        
                                if not canvas_box:
                                    print("Canvas box missing.")
                                    browser.close()
                                    return
                        
                                print("Taking canvas screenshot...")
                                png_bytes = canvas_el.screenshot()
                        
                                targets, img_w, img_h = find_recliner_seats(png_bytes, SEATS_TO_SELECT)
                        
                                if not targets:
                                    print("No available Recliner seats found.")
                                else:
                                    print(f"Found {len(targets)} Recliner seats. Clicking...")
                                    scale_x = canvas_box["width"] / img_w
                                    scale_y = canvas_box["height"] / img_h
                        
                                    for i, (tx, ty) in enumerate(targets):
                                        abs_x = canvas_box["x"] + (tx * scale_x)
                                        abs_y = canvas_box["y"] + (ty * scale_y)
                                        
                                        # Add tiny random jitter to click to look human
                                        jitter_x = random.randint(-2, 2)
                                        jitter_y = random.randint(-2, 2)
                        
                                        print(f"Clicking Recliner {i+1}...")
                                        page.mouse.move(abs_x + jitter_x, abs_y + jitter_y, steps=5)
                                        page.mouse.click(abs_x + jitter_x, abs_y + jitter_y)
                                        time_module.sleep(random.uniform(0.3, 0.7)) 
                        
                                    # --- PAY BUTTON ---
                                    time_module.sleep(1)
                                    
                                    page.get_by_label("Pay ₹").click()
                                    print("Clicked Pay Button")
                                    page.get_by_text("Accept").click()
                                    print("Clicked Accept Button")
                                    page.wait_for_timeout(3000)
                                    try:
                                        page.get_by_text("Skip").click()
                                    except:
                                        print("Could not click Skip")
                                            
                                    page.wait_for_timeout(3000)
                                    try:
                                        page.get_by_placeholder("eg: abc@gmail.com").fill("khan@gmail.com")
                                    except:
                                        print("Could not enter mail ID")
                                    try:
                                        page.get_by_placeholder("eg: 91480XXXXX").click()
                                    except:
                                        print("Could not click Phone number field")
                                    try:
                                        page.get_by_placeholder("eg: 91480XXXXX").fill("9876543210")
                                    except:
                                        print("Could not enter Phone number")
                                    try:
                                        page.get_by_label("Submit").click()
                                    except:
                                        print("Could not click Submit")
                                    page.wait_for_timeout(5000)
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
