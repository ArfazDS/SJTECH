import os
import json
import sys

CONFIG_FILE = "config.json"

def parse_message(text):
    # Expected: /update YYYYMMDD Language Movie Name
    parts = text.split()
    if parts[0] != "/update" or len(parts) < 4:
        raise ValueError("Invalid command")

    return {
        "TARGET_DATE_ID": parts[1],
        "LANGUAGE": parts[2],
        "MOVIE_NAME": " ".join(parts[3:])
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
