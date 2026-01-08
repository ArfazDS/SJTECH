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
# =========================================


# def send_alert(msg):
#     if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
#         print("\n[ALERT MESSAGE]\n", msg)
#         return

#     url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#     requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


async def send_alert(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    print("Telegram response:", r.text)


async def run():
    async with async_playwright() as p:
        # browser = await p.chromium.launch(headless=True)
        # page = await browser.new_page()

        # print("[*] Opening page...")
        # await page.goto(TARGET_URL, timeout=15000)
        # await page.wait_for_timeout(5000)

        # print("\n=== DATE CELLS FOUND ===\n")

        # date_divs = await page.query_selector_all("div.sc-h5edv-0")

        # target_status = None

        # for i, div in enumerate(date_divs, 1):
        #     div_class = await div.get_attribute("class") or ""

        #     span_day = await div.query_selector("span.sc-h5edv-1")
        #     span_date = await div.query_selector("span.sc-h5edv-2")
        #     span_month = await div.query_selector("span.sc-h5edv-3")

        #     day = (await span_day.inner_text()).strip() if span_day else ""
        #     date = (await span_date.inner_text()).strip() if span_date else ""
        #     month = (await span_month.inner_text()).strip() if span_month else ""

        #     status = "INACTIVE" if "cmkkZb" in div_class else "ACTIVE"

        #     print(f"{i}. {day} {date} {month} → {status}")

        #     if (
        #         day == TARGET_DAY
        #         and date == TARGET_DATE
        #         and month == TARGET_MONTH
        #     ):
        #         target_status = status

        # print("\n=== RESULT ===")

        # if target_status == "ACTIVE":
        #     send_alert(
        #         f"🚨 DATE OPEN – GO BOOK NOW!\n"
        #         f"{TARGET_DAY} {TARGET_DATE} {TARGET_MONTH}\n"
        #         f"{page.url}"
        #     )
        # else:
        #     send_alert(
        #         f"⚠️ BOOKING NOT ACTIVE YET\n"
        #         f"{TARGET_DAY} {TARGET_DATE} {TARGET_MONTH}"
        #     )

        # await browser.close()
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

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
