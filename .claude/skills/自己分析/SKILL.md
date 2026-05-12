# Skill: 常角慎太郎 自己分析

ズーミンの人物像・パーソナリティ・価値観を深掘りし、Threads投稿ストックや自己理解に活用するスキル。

## 使い方

「自己分析して」「質問して」「俺という人間を診断して」などで起動。

## 動作モード

### 1. 質問モード（デフォルト）
ズーミンの人格・経験・価値観を深掘りする質問を1問ずつ行う。
回答は以下のいずれかで処理：
- **「投稿」** → 即Threads投稿
- **「ストック」** → リモートエージェントのエピソードストックに追加
- **「続ける」** → 次の質問へ

### 2. 診断モード
「診断して」と言われたら、収集した情報をもとにPDFレポートを生成。

## 蓄積済みデータ

- `context/me.md` に人物像・価値観を記録
- `memory/user_character.md` に深い人格情報を記録
- リモートエージェント（Threads自動投稿）のエピソードストックに蓄積

## 参照先

- `/Users/tsunezumi/.claude/projects/-Users-tsunezumi-Desktop-claude-code-demo/memory/user_character.md`
- `context/me.md`
- `scripts/generate_character_diagnosis.py` — 人間性診断PDF生成
- `scripts/generate_divination_report.py` — 占い診断PDF生成
- `scripts/generate_personality_report.py` — 総合診断PDF生成

## 出力先

- PDF: `output/character-diagnosis-tsunezumi.pdf`
- PDF: `output/divination-report-tsunezumi.pdf`
- Threads投稿ストック: リモートトリガー更新
