#!/usr/bin/env python3
"""
Threads APIのアクセストークンを取得するワンタイムスクリプト。
リダイレクト先のURLバーから認可コードを手動でコピーして貼る方式。

事前準備:
  Meta for Developers → Threads API → Settings の
  "コールバックURLをリダイレクト" に下記を追加して保存:
    https://www.facebook.com
"""

import urllib.parse
import requests
import sys
from pathlib import Path

APP_ID       = input("App ID を入力 (886961687735504): ").strip() or "886961687735504"
APP_SECRET   = input("App Secret を入力: ").strip()
REDIRECT_URI = "https://www.facebook.com"

AUTH_URL = (
    f"https://threads.net/oauth/authorize"
    f"?client_id={APP_ID}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
    f"&scope=threads_basic,threads_content_publish"
    f"&response_type=code"
)

print("\n━━━ Step 1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("下記URLをブラウザで開いてください (Threads アカウントでログイン):")
print()
print(AUTH_URL)
print()
print("━━━ Step 2 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("認証後、facebook.com にリダイレクトされます。")
print("URLバーに ?code=XXXXXXX#_ が付いているので、")
print("そのコード部分 (= 以降、#_ 以前) をコピーしてください。")
print()

auth_code = input("コードを貼り付け: ").strip().split("#")[0].strip()

# 短期トークン取得
print("\nトークン取得中...")
r = requests.post(
    "https://graph.threads.net/oauth/access_token",
    data={
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
)
data = r.json()
if "access_token" not in data:
    print(f"エラー: {data}")
    sys.exit(1)

short_token = data["access_token"]
user_id     = data.get("user_id", "")
print(f"短期トークン取得 ✓ (user_id={user_id})")

# 長期トークンに交換
r2 = requests.get(
    "https://graph.threads.net/access_token",
    params={
        "grant_type": "th_exchange_token",
        "client_secret": APP_SECRET,
        "access_token": short_token,
    }
)
data2 = r2.json()
if "access_token" not in data2:
    print(f"長期トークン取得エラー: {data2}")
    sys.exit(1)

long_token = data2["access_token"]
expires    = data2.get("expires_in", "?")
print(f"長期トークン取得 ✓ (有効期限: {int(expires)//86400 if isinstance(expires, int) else expires} 日)")

# .env に書き込む
env_file = Path(__file__).parent.parent / ".env"
lines = env_file.read_text().splitlines() if env_file.exists() else []

def upsert(lines, key, value):
    for i, l in enumerate(lines):
        if l.startswith(key + "="):
            lines[i] = f"{key}={value}"
            return lines
    lines.append(f"{key}={value}")
    return lines

lines = upsert(lines, "THREADS_ACCESS_TOKEN", long_token)
lines = upsert(lines, "THREADS_USER_ID", str(user_id))
env_file.write_text("\n".join(lines) + "\n")

print(f"\n.env に保存しました ✓")
print(f"  THREADS_USER_ID      = {user_id}")
print(f"  THREADS_ACCESS_TOKEN = {long_token[:20]}...")
print()
print("自動投稿を有効化:")
print("  launchctl load ~/Library/LaunchAgents/com.zoomin.threads-post.plist")
