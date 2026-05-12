# Skill: LINE公式アカウント管理

ZoomIn 公式LINEアカウントの運用・管理を行うスキル。
在宅ワーカー（約20名）とのコミュニケーション基盤を整備・更新する。

## アカウント情報

- **チャンネルID:** 2009822793
- **アクセストークン:** `.env` の `LINE_CHANNEL_ACCESS_TOKEN`
- **チャンネルシークレット:** `.env` の `LINE_CHANNEL_SECRET`

---

## できること

### 1. リッチメニュー管理

#### 現在のリッチメニュー構成（6枠 + 追加4枠 = 最大10枠）

追加予定の4枠（URL遷移型）:

| メニュー名 | 遷移先URL |
|------------|-----------|
| 小遣い案件 | https://docs.google.com/document/d/1elK6pvXahbyUH6zDRKrVn-HNClJ0-zbstj8GIByKvcY/edit |
| お仕事一覧 | https://docs.google.com/document/d/1sbXSqDy6zTsh3Ujb88hKWKN9GF_ZboFonbG5bQSUx3U/edit |
| 最新情報   | https://docs.google.com/document/d/1VgGliv4y7gWTWgbAdBhw2LbycDtP9UZb8MFOJJ3WCu0/edit |
| スキルチェック | https://docs.google.com/document/d/1p013iaVVrChjp0Bq6yBQzzNYYqSEWNJ9LIcCcrCOfrQ/edit |

#### リッチメニュー作成の手順

```bash
# .envからトークンを読み込む
LINE_TOKEN=$(grep LINE_CHANNEL_ACCESS_TOKEN .env | cut -d '=' -f2)

# 1. リッチメニューを作成
curl -X POST https://api.line.me/v2/bot/richmenu \
  -H "Authorization: Bearer $LINE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<メニューJSON>'

# 2. 画像をアップロード
curl -X POST https://api-data.line.me/v2/bot/richmenu/{richMenuId}/content \
  -H "Authorization: Bearer $LINE_TOKEN" \
  -H "Content-Type: image/png" \
  --data-binary @<画像ファイル>

# 3. デフォルトメニューに設定（全ユーザーへ適用）
curl -X POST https://api.line.me/v2/bot/user/all/richmenu/{richMenuId} \
  -H "Authorization: Bearer $LINE_TOKEN"
```

#### URL遷移型メニューのJSONテンプレート

```json
{
  "size": { "width": 2500, "height": 843 },
  "selected": true,
  "name": "メニュー名",
  "chatBarText": "メニュー",
  "areas": [
    {
      "bounds": { "x": 0, "y": 0, "width": 833, "height": 843 },
      "action": { "type": "uri", "uri": "https://..." }
    }
  ]
}
```

---

### 2. メッセージ送信

#### ブロードキャスト（全員へ）

```bash
LINE_TOKEN=$(grep LINE_CHANNEL_ACCESS_TOKEN .env | cut -d '=' -f2)

curl -X POST https://api.line.me/v2/bot/message/broadcast \
  -H "Authorization: Bearer $LINE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"type": "text", "text": "メッセージ本文"}]
  }'
```

#### マルチキャスト（特定ユーザーへ）

```bash
curl -X POST https://api.line.me/v2/bot/message/multicast \
  -H "Authorization: Bearer $LINE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["Uxxxxxxxx", "Uxxxxxxxx"],
    "messages": [{"type": "text", "text": "メッセージ本文"}]
  }'
```

---

### 3. フォロワー確認

```bash
LINE_TOKEN=$(grep LINE_CHANNEL_ACCESS_TOKEN .env | cut -d '=' -f2)

# フォロワー数を確認
curl https://api.line.me/v2/bot/followers/count \
  -H "Authorization: Bearer $LINE_TOKEN"

# フォロワーのユーザーIDリストを取得
curl "https://api.line.me/v2/bot/followers/ids" \
  -H "Authorization: Bearer $LINE_TOKEN"
```

---

## Googleドライブ連携

公式ラインの各メニューページは以下のフォルダで管理:
**Googleドライブ > 株式会社Zoom In > 在宅ワーク > 公式ライン**

| ドキュメント | URL |
|-------------|-----|
| 小遣い案件 | https://docs.google.com/document/d/1elK6pvXahbyUH6zDRKrVn-HNClJ0-zbstj8GIByKvcY/edit |
| お仕事一覧 | https://docs.google.com/document/d/1sbXSqDy6zTsh3Ujb88hKWKN9GF_ZboFonbG5bQSUx3U/edit |
| 最新情報 | https://docs.google.com/document/d/1VgGliv4y7gWTWgbAdBhw2LbycDtP9UZb8MFOJJ3WCu0/edit |
| スキルチェック | https://docs.google.com/document/d/1p013iaVVrChjp0Bq6yBQzzNYYqSEWNJ9LIcCcrCOfrQ/edit |

---

## 注意事項

- リッチメニューを変更・公開する前に必ずズーミンに確認を取ること
- アクセストークンは `.env` で管理。git にはコミットしない
- メッセージ送信は取り消し不可。内容を確認してから実行
