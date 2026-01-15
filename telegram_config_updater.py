import os
import json
import sys
import requests

CONFIG_FILE = "config.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_latest_message():
    """Fetches the latest message from the Telegram Bot API."""
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

def parse_update_command(text):
    parts = text.split()
    
    # Message format: /update 20260116 10 23 English The Housemaid
    if parts[0] != "/update" or len(parts) < 6:
        raise ValueError("Invalid command format")

    return {
        "TARGET_DATE_ID": parts[1],
        "Str_Time": parts[2],      # 10
        "End_Time": parts[3],      # 23
        "LANGUAGE": parts[4],      # English
        "MOVIE_NAME": " ".join(parts[5:]) # The Housemaid
    }

if __name__ == "__main__":
    print("Checking for Telegram messages...")
    
    # 1. Get the real message from Telegram
    telegram_message = get_latest_message()

    if not telegram_message:
        print("No new /update commands found.")
        sys.exit(0)

    print(f"Processing command: {telegram_message}")

    # 2. Parse and Update
    try:
        values = parse_update_command(telegram_message)
        
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Check if update is actually needed to avoid empty commits
        if config["MOVIE_NAME"] != values["MOVIE_NAME"] or config["LANGUAGE"] != values["LANGUAGE"]:
            config.update(values)
            
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            
            print("config.json updated successfully")
        else:
            print("Config is already up to date.")

    except Exception as e:
        print(f"Error parsing command: {e}")
        sys.exit(1)
