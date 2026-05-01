"""Start Cloudflare tunnel and send the generated URL to Telegram."""

import subprocess
import re
import urllib.request
import urllib.parse
import json
import os
import sys

from decouple import config

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config("TELEGRAM_CHAT_ID")
CLOUDFLARED_PATH = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
LOCAL_URL = "http://localhost:8000"


def send_telegram(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Telegram] Failed to send: {e}")
        return False


def main():
    print("Starting Cloudflare Tunnel...")
    print(f"Local server: {LOCAL_URL}\n")

    process = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "--url", LOCAL_URL],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    url_sent = False
    tunnel_url_pattern = re.compile(r"(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)")

    try:
        for line in process.stdout:
            print(line, end="")

            if not url_sent:
                match = tunnel_url_pattern.search(line)
                if match:
                    tunnel_url = match.group(1)
                    print(f"\n{'='*50}")
                    print(f"  Tunnel URL: {tunnel_url}")
                    print(f"{'='*50}\n")

                    message = (
                        f"🌐 <b>Learn Vocabulary Server</b>\n\n"
                        f"Tunnel is ready!\n"
                        f"<code>{tunnel_url}</code>"
                    )
                    if send_telegram(message):
                        print("[Telegram] URL sent successfully!")
                    else:
                        print("[Telegram] Failed to send URL.")
                    url_sent = True

        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down tunnel...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
