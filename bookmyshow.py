import asyncio
import os
import smtplib
from email.message import EmailMessage
from playwright.async_api import async_playwright\

def send_email_alert(EMAIL_USER, EMAIL_PASS):

    if not EMAIL_USER or not EMAIL_PASS:
        print("Missing email credentials.")
        return

    msg = EmailMessage()
    msg['Subject'] = "🎟️ BookMyShow Alert: Dates Active!"
    msg['From'] = EMAIL_USER
    msg['To'] = 'ak.sjtech@gmail.com'  # Change to your email

    msg.set_content("Required dates are now active on BookMyShow!")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        print("✅ Email alert sent.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


async def bookmyshow(url,EMAIL_USER, EMAIL_PASS):
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url)
            await page.wait_for_timeout(3000)

            div_selector = 'div.sc-h5edv-0.HzoHP'
            await page.wait_for_selector(div_selector)

            spans = await page.query_selector_all(f'{div_selector} > span.sc-h5edv-1.lbMdAA')
            span_texts = [await span.inner_text() for span in spans]

            required_texts = ['TUE', 'WED']
            if span_texts[:2] == required_texts:
                print("✅ Activated.")
                send_email_alert(EMAIL_USER, EMAIL_PASS)
            else:
                print("❌ Still not active.")
                print("Found spans:", span_texts)

            await context.close()
            await browser.close()
    except Exception as e:
        print(f"Error processing {url} : {e}")

async def main():
    EMAIL_USER="arfazkhank@gmail.com"
    EMAIL_PASS="xkuz iysd imzc mabk"

    url = "https://in.bookmyshow.com/cinemas/hyderabad/pvr-nexus-mall-kukatpally-hyderabad/buytickets/PVFS/20250710"
    await bookmyshow(url,EMAIL_USER, EMAIL_PASS)

if __name__ == "__main__":
    asyncio.run(main())
