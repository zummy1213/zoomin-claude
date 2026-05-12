#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毎朝5時に実行。Threads APIでバズ投稿を検索し、
Claude多視点チームで分析して daily_insight.md に保存する。
"""
import os, json, datetime, requests
from pathlib import Path
from anthropic import Anthropic

BASE_DIR = Path(__file__).parent.parent
INSIGHT_FILE = Path(__file__).parent / 'daily_insight.md'
LOG_FILE = Path(__file__).parent / 'analyze.log'

KEYWORDS = ['誠実', '在宅ワーク', '働き方', '稼ぐ', '仕事', '起業', '副業']

AGENTS = [
    {
        'name': 'コピーライター',
        'focus': 'フック・言葉の強さ・最初の1文で引き込む技術・言い回しの妙',
    },
    {
        'name': '心理学者',
        'focus': '感情トリガー・共感ポイント・なぜ人が反応したくなるか・自己開示の効果',
    },
    {
        'name': 'マーケター',
        'focus': '拡散要因・ターゲット設定・投稿の構造・なぜシェアされたか',
    },
    {
        'name': '編集者',
        'focus': 'リズム・文量・余白・改行・読みやすさ・テンポ感',
    },
]


def load_env():
    env = {}
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    os.environ.update(env)
    return env


def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    entry = f'[{now}] {msg}\n'
    LOG_FILE.open('a', encoding='utf-8').write(entry)
    print(entry.strip())


def fetch_viral_posts(token: str, user_id: str) -> list[dict]:
    """Threads APIキーワード検索でバズ投稿を取得する。"""
    posts = []
    for keyword in KEYWORDS:
        try:
            res = requests.get(
                'https://graph.threads.net/v1.0/threads/keywordsearch',
                params={
                    'q': keyword,
                    'fields': 'id,text,like_count,replies_count,timestamp',
                    'access_token': token,
                },
                timeout=10,
            )
            data = res.json()
            if 'data' in data:
                posts.extend(data['data'])
        except Exception as e:
            log(f'検索エラー ({keyword}): {e}')

    VIRAL_THRESHOLD = 500  # バズの定義: いいね500以上

    # いいね500以上のみ絞り込み → エンゲージメント順にソート
    viral = [p for p in posts if p.get('like_count', 0) >= VIRAL_THRESHOLD]
    viral.sort(key=lambda p: p.get('like_count', 0) + p.get('replies_count', 0), reverse=True)

    # 重複除去・上位10件
    seen = set()
    unique = []
    for p in viral:
        if p['id'] not in seen and p.get('text'):
            seen.add(p['id'])
            unique.append(p)
        if len(unique) >= 10:
            break

    # 500以上が0件の場合はフォールバック（上位10件を返す）
    if not unique:
        log('いいね500以上の投稿が見つからなかった。上位10件にフォールバック。')
        posts.sort(key=lambda p: p.get('like_count', 0), reverse=True)
        for p in posts:
            if p['id'] not in seen and p.get('text'):
                seen.add(p['id'])
                unique.append(p)
            if len(unique) >= 10:
                break

    return unique


def analyze_with_agent(client: Anthropic, posts_text: str, agent: dict) -> str:
    """1エージェントの視点で投稿を分析する。"""
    prompt = f"""あなたは世界最高レベルの{agent['name']}です。

以下はThreadsでバズった投稿の一覧です。

{posts_text}

## あなたの分析視点
{agent['focus']}

この視点から、「なぜこれらの投稿はバズったのか」を分析し、
**ズーミン（誠実に稼ぐことをテーマに発信する経営者）が今日の投稿に活かせる具体的な法則を3点**挙げてください。

箇条書きで、各30文字以内で端的に。"""

    res = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return res.content[0].text.strip()


def synthesize(client: Anthropic, analyses: list[dict], posts_text: str) -> str:
    """4エージェントの分析を統合して今日のインサイトを生成する。"""
    analyses_text = '\n\n'.join(
        f'### {a["name"]}の視点\n{a["result"]}' for a in analyses
    )

    prompt = f"""以下は4人の専門家がThreadsのバズ投稿を分析した結果です。

{analyses_text}

## 元の投稿
{posts_text}

これらを統合して、**ズーミン（常角慎太郎）が今日のThreads投稿に即使える「今日のバズの法則」**を
3行以内でまとめてください。

ズーミンの文体（一人称口語・短文・逆説・余韻で終わる）に合わせた具体的なアドバイスで。"""

    res = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return res.content[0].text.strip()


def main():
    env = load_env()
    token = env.get('THREADS_ACCESS_TOKEN', '')
    user_id = env.get('THREADS_USER_ID', '')

    if not token or token == 'your_token_here':
        log('ERROR: THREADS_ACCESS_TOKEN が未設定')
        return

    log('バズ投稿の収集を開始')
    posts = fetch_viral_posts(token, user_id)

    if not posts:
        log('投稿が取得できなかった。インサイト生成をスキップ。')
        return

    log(f'{len(posts)}件の投稿を取得')

    posts_text = '\n\n---\n\n'.join(
        f'【いいね{p.get("like_count", 0)} リプライ{p.get("replies_count", 0)}】\n{p["text"]}'
        for p in posts
    )

    client = Anthropic()
    analyses = []
    for agent in AGENTS:
        log(f'{agent["name"]}が分析中...')
        result = analyze_with_agent(client, posts_text, agent)
        analyses.append({'name': agent['name'], 'result': result})

    log('インサイトを統合中...')
    insight = synthesize(client, analyses, posts_text)

    today = datetime.date.today().isoformat()
    content = f'# 今日のバズの法則 ({today})\n\n{insight}\n\n## 分析した投稿数\n{len(posts)}件\n'
    INSIGHT_FILE.write_text(content, encoding='utf-8')
    log(f'インサイトを保存: {INSIGHT_FILE}')
    print(insight)


if __name__ == '__main__':
    main()
