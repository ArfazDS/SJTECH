import os
import json
import sys

CONFIG_FILE = "config.json"

def parse_update_command(text):
    parts = text.split()

    if parts[0] != "/update" or len(parts) < 6:
        raise ValueError("Invalid command format")

    return {
        "TARGET_DATE_ID": parts[1],
        "LANGUAGE": parts[2],
        "Str_Time": parts[3],
        "End_Time": parts[4],
        "MOVIE_NAME": " ".join(parts[5:])
    }

if __name__ == "__main__":
    telegram_message = os.getenv("TELEGRAM_MESSAGE")

    if not telegram_message:
        print("No Telegram message found")
        sys.exit(0)

    values = parse_message(telegram_message)

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    config.update(values)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

    print("config.json updated")
