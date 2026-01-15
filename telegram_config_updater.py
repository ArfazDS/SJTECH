import os
import json
import sys
import requests

CONFIG_FILE = "config.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_message():
    """Fetches the latest message from the Telegram Bot API."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID env vars")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data.get("ok"):
            print("Error connecting to Telegram:", data)
            return None

        # Look through messages in reverse to find the newest command
        results = data.get("result", [])
        for update in reversed(results):
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = str(message.get("chat", {}).get("id"))

            # Check if it's the correct chat and a valid command
            if chat_id == TELEGRAM_CHAT_ID and text.startswith("/update"):
                return text
                
    except Exception as e:
        print(f"Failed to fetch updates: {e}")
        
    return None

def send_telegram_response(message_text):
    """Sends a message back to the Telegram chat."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown" # Allows us to use bolding and code blocks
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send Telegram response: {e}")

def parse_update_command(text):
    parts = text.split()
    
    # Message format: /update 20260116 10 23 English The Housemaid
    if parts[0] != "/update" or len(parts) < 6:
        raise ValueError("Invalid command format")

    return {
        "TARGET_DATE_ID": parts[1],
        "Str_Time": parts[2],      
        "End_Time": parts[3],      
        "LANGUAGE": parts[4],      
        "MOVIE_NAME": " ".join(parts[5:]) 
    }

if __name__ == "__main__":
    print("Checking for Telegram messages...")
    
    telegram_message = get_latest_message()

    if not telegram_message:
        print("No new /update commands found.")
        sys.exit(0)

    print(f"Processing command: {telegram_message}")

    try:
        values = parse_update_command(telegram_message)
        
        # Load existing config or create empty dict
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        else:
            config = {}

        # Check if update is needed
        # (We check specific fields to avoid unnecessary writes/notifications)
        if (config.get("MOVIE_NAME") != values["MOVIE_NAME"] or 
            config.get("LANGUAGE") != values["LANGUAGE"] or
            config.get("TARGET_DATE_ID") != values["TARGET_DATE_ID"]):
            
            config.update(values)
            
            # Write to file
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            
            print("config.json updated successfully")

            # --- NEW: Send Confirmation to Telegram ---
            formatted_json = json.dumps(config, indent=2)
            response_msg = (
                f"✅ *Movie Details Updated!*\n\n"
                f"🎬 *Movie:* {config.get('MOVIE_NAME')}\n"
                f"🗣 *Language:* {config.get('LANGUAGE')}\n"
                f"📅 *Date:* {config.get('TARGET_DATE_ID')}\n"
                f"⏰ *Time Slot:* {config.get('Str_Time')}:00 - {config.get('End_Time')}:00"
            )
            send_telegram_response(response_msg)
            # ------------------------------------------

        else:
            print("Config is already up to date.")
            # Optional: Uncomment below if you want a message even when no changes occur
            # send_telegram_response("ℹ️ Config is already up to date.")

    except Exception as e:
        error_msg = f"❌ Error processing update: {str(e)}"
        print(error_msg)
        # Optional: Send error to Telegram so you know it failed
        # send_telegram_response(error_msg)
        sys.exit(1)
