import requests
import base64
import json
import os

# ---------------- CONFIG ----------------
GITHUB_TOKEN = os.getenv("GIT_TOKEN_CUSTOM")
REPO_OWNER = "ArfazDS"
REPO_NAME = "SJTECH"
FILE_PATH = "config.json"
BRANCH = "main"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
# ---------------------------------------


def get_config_file():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()

    content = base64.b64decode(data["content"]).decode()
    return json.loads(content), data["sha"]


def update_config_file(new_config, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    encoded = base64.b64encode(
        json.dumps(new_config, indent=2).encode()
    ).decode()

    payload = {
        "message": "Update config via Telegram",
        "content": encoded,
        "sha": sha,
        "branch": BRANCH,
    }

    r = requests.put(url, headers=headers, json=payload)
    r.raise_for_status()


def send_telegram(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
    )


def handle_update(chat_id, text):
    # Parse key=value pairs
    updates = {}
    for part in text.replace("/update", "").strip().split():
        if "=" in part:
            k, v = part.split("=", 1)
            updates[k] = v

    if not updates:
        send_telegram(chat_id, "❌ No valid updates found.")
        return

    config, sha = get_config_file()

    config.update(updates)
    update_config_file(config, sha)

    send_telegram(
        chat_id,
        "✅ config.json updated successfully\n\n"
        + "\n".join(f"{k} = {v}" for k, v in updates.items()),
    )


def poll_telegram():
    offset = 0
    while True:
        r = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"offset": offset + 1, "timeout": 60},
        )
        data = r.json()

        for result in data.get("result", []):
            offset = result["update_id"]
            msg = result.get("message", {})
            text = msg.get("text", "")
            chat_id = msg["chat"]["id"]

            if text.startswith("/update"):
                handle_update(chat_id, text)


if __name__ == "__main__":
    poll_telegram()
