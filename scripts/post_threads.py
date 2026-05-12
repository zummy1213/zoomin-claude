#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毎朝6時にThreadsへ3本投稿する。
実行前に .env に THREADS_ACCESS_TOKEN と THREADS_USER_ID を設定すること。
"""
import os, sys, json, datetime, requests
from pathlib import Path
from anthropic import Anthropic

BASE_DIR = Path(__file__).parent.parent

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

def load_context():
    ctx = {}
    for name in ('me', 'work', 'current-priorities'):
        f = BASE_DIR / 'context' / f'{name}.md'
        if f.exists():
            ctx[name] = f.read_text(encoding='utf-8')
    return ctx


def load_daily_insight() -> str:
    insight_file = Path(__file__).parent / 'daily_insight.md'
    if insight_file.exists():
        return insight_file.read_text(encoding='utf-8')
    return ''

THEMES = {
    6:  '仕事・ビジネス系の気づき（今日の仕事への向き合い方、誠実に稼ぐことへの想い）',
    12: '人・関係性・生き方系（人との関わり、チームへの想い、働くことの意味）',
    18: '自由（日常の小さな発見・問い・独り言・夜の振り返り）',
}

def generate_post(context: dict, hour: int) -> str:
    client = Anthropic()
    ctx_text = '\n\n'.join(f'## {k}\n{v}' for k, v in context.items())
    theme = THEMES.get(hour, THEMES[18])

    insight = load_daily_insight()
    insight_section = f'\n## 今日のバズの法則（参考にして取り入れる）\n{insight}\n' if insight else ''

    prompt = f"""あなたはズーミン（常角慎太郎）本人として、Threadsに投稿する文章を1本書きます。

## ズーミンのプロフィールと文脈
{ctx_text}
{insight_section}
## 投稿ルール
- 文体: 完全に一人称の口語。「なんか」「まじで」「ほんまに」などの自然な口語OK
- 文量: 80〜180文字。短文と長文を意図的に混ぜてリズムをつくる
- テーマ: {theme}
- NGワード: キラキラ起業家感、意識高い系フレーズ、マウント、「〜しましょう」「〜です/ます調まとめ」
- ハッシュタグ: なしか1個まで（つけすぎはAI感が出る）

## 文体の核心：常角語録スタイル
- 「名言」を1〜2文で切り出す感覚。短く鋭く、余韻を残す
- 「〜やと思ってる」「〜が全部やと思う」「〜だけ決めてる」など確信の言い方
- 逆説・対比を使う（「能力は育つ。でも人間性は変わらない」「情で始めて、基準で判断する」）
- 最後の1文で視点をぐっと絞る。余白で終わらせる
- 3文構成が多い：①状況・問い ②気づき ③確信

## ズーミンの核心にある確信（これを投稿の軸にする）
- 言ってることとやってることが違う人を、能力不足より嫌う
- 誠実さは道徳じゃなく長期で最も安定した経営戦略
- 30過ぎて人間性が変わった人を見たことがない
- 嘘つきは直らない。直そうとするより関わらない選択が正しい
- 怒りは気分じゃなく、筋が通っていないことへの反応
- 情で始めて、基準で判断する
- 真面目な人が損する構造を許したくない
- 理想を実務に落とし込めないなら理念じゃなくスローガン

## バズらせるための必須要素（どれか1つ以上入れる）
- 近くにいる人との会話から気づいたこと（名前は出さない）
- 読んだ人が「わかる」と膝を打つ感情・違和感
- 逆説・意外な視点（「〜なのに〜」「普通は〜だけど」）
- 余白で終わる最終文（問いかけより「〜やと思ってる」で静かに締める）

## AI文章に見えないための禁止パターン
- 同じ文末の繰り返し
- 箇条書き・まとめ風の構成
- 「〜することが大切です」「〜を意識しましょう」系
- 在宅ワーカーとの日常会話エピソード（外注先のため接点は業務のみ）

投稿文のテキストだけを返してください（前置き・説明・カギ括弧不要）。"""

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=512,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return message.content[0].text.strip()

def post_to_threads(user_id: str, token: str, text: str) -> dict:
    # Step 1: メディアコンテナ作成
    container = requests.post(
        f'https://graph.threads.net/v1.0/{user_id}/threads',
        params={'media_type': 'TEXT', 'text': text, 'access_token': token}
    ).json()
    if 'id' not in container:
        return {'error': container}

    # Step 2: 投稿公開
    result = requests.post(
        f'https://graph.threads.net/v1.0/{user_id}/threads_publish',
        params={'creation_id': container['id'], 'access_token': token}
    ).json()
    return result

def main():
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    log_file = Path(__file__).parent / 'threads-post.log'

    env = load_env()
    token   = env.get('THREADS_ACCESS_TOKEN', '')
    user_id = env.get('THREADS_USER_ID', '')

    if not token or token == 'your_token_here':
        msg = f'[{now}] ERROR: THREADS_ACCESS_TOKEN が未設定\n'
        print(msg, file=sys.stderr)
        log_file.open('a', encoding='utf-8').write(msg)
        sys.exit(1)

    hour = datetime.datetime.now().hour
    context = load_context()
    text = generate_post(context, hour)

    result = post_to_threads(user_id, token, text)
    status = 'OK' if 'id' in result else f'ERROR: {result}'

    log_entry = f'[{now}] {status}\n{text}\n\n'
    log_file.open('a', encoding='utf-8').write(log_entry)
    sys.stdout.reconfigure(encoding='utf-8')
    print(f'{status}: {text[:60]}...')
    print('完了')

if __name__ == '__main__':
    main()
