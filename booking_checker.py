import asyncio
import requests
import os
from datetime import datetime
from playwright.async_api import async_playwright

# ================= CONFIG =================
TARGET_DATE_ID = "20260108"
TARGET_URL = f"https://in.bookmyshow.com/cinemas/hyderabad/aparna-cinemas-nallagandla/buytickets/AACN/{TARGET_DATE_ID}"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")
DAY = dt.strftime("%a")
DATE = dt.strftime("%d")
MONTH = dt.strftime("%b")

print("TARGET:", DAY, DATE, MONTH)

async def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("Telegram response:", r.text)


async def run():
    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=False)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        await page.goto(TARGET_URL)
        await page.wait_for_timeout(15000)

        curr = page.url

        if TARGET_DATE_ID in curr:
            print("alert sent")
            dt = datetime.strptime(TARGET_DATE_ID, "%Y%m%d")

            DAY = dt.strftime("%a")   
            DATE = dt.strftime("%d")   
            MONTH = dt.strftime("%b") 
            
            await send_alert(f"🚨 DATE OPEN – for {DAY} {DATE} {MONTH}\n"
            f"GO BOOK NOW! : {curr}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
