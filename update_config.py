import os
import json
import base64
import requests

# ========== ENV ==========
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_CUSTOM")
REPO_OWNER = "ArfazDS"
REPO_NAME = "SJTECH"
FILE_PATH = "config.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_BASE = "https://api.github.com"


# ========== TELEGRAM ==========
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
        timeout=10
    )


# ========== GET FILE ==========
def get_config_file():
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


# ========== UPDATE FILE ==========
def update_config(new_values):
    file_data = get_config_file()

    decoded = base64.b64decode(file_data["content"]).decode()
    config = json.loads(decoded)

    config.update(new_values)

    new_content = base64.b64encode(
        json.dumps(config, indent=2).encode()
    ).decode()

    payload = {
        "message": "Update config.json via Telegram bot",
        "content": new_content,
        "sha": file_data["sha"]
    }

    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    r = requests.put(url, headers=headers, json=payload)
    r.raise_for_status()


# ========== MAIN ==========
if __name__ == "__main__":
    try:
        update_config({
            "TARGET_DATE_ID": "20260116",
            "MOVIE_NAME": "The Housemaid",
            "LANGUAGE": "English"
        })

        send_telegram("✅ config.json updated successfully")

    except Exception as e:
        send_telegram(f"❌ Failed to update config.json\n{e}")
        raise
