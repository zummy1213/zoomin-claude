#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
env = {}
for line in (BASE_DIR / '.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

token = env['THREADS_ACCESS_TOKEN']
user_id = env['THREADS_USER_ID']

print("=== キーワード検索テスト ===")
res = requests.get(
    'https://graph.threads.net/v1.0/threads/keywordsearch',
    params={'q': '誠実', 'fields': 'id,text,like_count,replies_count,timestamp', 'access_token': token},
    timeout=10
)
print('Status:', res.status_code)
data = res.json()
print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])

print("\n=== 自分の投稿取得テスト ===")
res2 = requests.get(
    f'https://graph.threads.net/v1.0/{user_id}/threads',
    params={'fields': 'id,text,like_count,replies_count,timestamp', 'access_token': token, 'limit': 5},
    timeout=10
)
print('Status:', res2.status_code)
data2 = res2.json()
print(json.dumps(data2, ensure_ascii=False, indent=2)[:3000])
