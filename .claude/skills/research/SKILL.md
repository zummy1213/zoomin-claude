# Skill: Research

Web検索を使って、ズーミンのビジネス文脈を踏まえたリサーチを行うスキル。

現在は Claude Code の組み込み WebSearch ツールを使用。
Perplexity API キーが `.env` に設定されたら、より高精度な検索に切り替える。

## いつ使うか

市場調査、競合調査、新規ビジネスのアイデア探索、業界トレンド把握などを依頼されたとき。

## 実行手順

### Step 1: ビジネス文脈を読み込む

以下のファイルを読み込み、Zoom In の事業文脈を把握する。

- `context/me.md` — ズーミンのプロフィールとミッション
- `context/work.md` — 事業内容・収益源・使用ツール
- `context/current-priorities.md` — 現在の優先事項

### Step 2: 検索を実行する

**現在（WebSearch モード）**

Claude Code の組み込み WebSearch ツールを使い、調査トピックについて複数の角度から検索する。

検索クエリの例（トピックが「タイ仮設トイレ市場」の場合）:
- `タイ 仮設トイレ 市場規模 2024`
- `Thailand portable toilet rental market`
- `タイ 建設現場 トイレ 需要`

必要に応じて WebFetch でページの詳細を取得する。

**将来（Perplexity API モード）**

`.env` の `PERPLEXITY_API_KEY` が設定済みの場合はこちらを使う:

```bash
PERPLEXITY_API_KEY=$(grep PERPLEXITY_API_KEY .env | cut -d '=' -f2)

SYSTEM_PROMPT="（Step 3 で組み立てた内容）"
USER_QUERY="（ユーザーの調査テーマ）"

PAYLOAD=$(jq -n \
  --arg system "$SYSTEM_PROMPT" \
  --arg user "$USER_QUERY" \
  '{
    model: "sonar-pro",
    messages: [
      {role: "system", content: $system},
      {role: "user", content: $user}
    ]
  }')

curl -s https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
```

### Step 3: 結果をまとめる

収集した情報を以下の形式でユーザーに提示する:

---

## 調査結果: （トピック名）

### サマリー
（箇条書きで主要な発見事項）

### Zoom In への示唆
（ズーミンの事業・優先事項に照らした考察とアクション候補）

### 情報源
（参照したURLや記事名）

---

## Perplexity API への切り替え方

1. https://www.perplexity.ai/settings/api で API キーを取得
2. `.env` の `PERPLEXITY_API_KEY=your_api_key_here` を実際のキーに書き換える
3. `brew install jq` を実行（未インストールの場合）
4. 次回のリサーチから自動的に Perplexity モードで動作する
