# Mac セットアップ手順：Claude Code + VS Code

新しいMac（Mac Mini等）にこのシステムを移植する際の手順書。

---

## 1. 必須ソフトウェアのインストール

### Homebrew（パッケージ管理）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Node.js
```bash
brew install node
```

### Python ライブラリ
```bash
pip3 install anthropic requests jpholiday reportlab
```

---

## 2. Claude Code のインストール

```bash
npm install -g @anthropic-ai/claude-code
```

インストール確認:
```bash
claude --version
```

---

## 3. VS Code のインストール

1. https://code.visualstudio.com からダウンロード・インストール
2. VS Code を開いて以下の拡張機能をインストール:
   - **Claude Code**（Anthropic公式）
   - **Remote - SSH**（外部PCからアクセスする場合）

### VS Code に Claude Code を紐付け
VS Code のターミナルで:
```bash
claude
```
初回起動時にAnthropicアカウントでログインする。

---

## 4. このシステムの移植

### GitHubからcloneする場合
```bash
cd ~/Desktop
git clone https://github.com/YOUR_REPO/claude-code-demo "claude code demo"
cd "claude code demo"
```

### 手動コピーの場合
旧MacからUSBまたはAirdropで `claude code demo` フォルダをそのまま `~/Desktop/` にコピー。

---

## 5. `.env` ファイルの設定

`.env` はgit管理外のため手動で作成または旧Macからコピー。

```bash
cd ~/Desktop/claude\ code\ demo
nano .env
```

以下を入力:
```
ANTHROPIC_API_KEY=sk-ant-...
THREADS_ACCESS_TOKEN=THAA...
THREADS_USER_ID=36002571529341655
PERPLEXITY_API_KEY=your_key_here
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...
```

---

## 6. launchd 自動投稿の登録

```bash
cp ~/Desktop/claude\ code\ demo/launchd/com.zoomin.threads-post.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.zoomin.threads-post.plist
```

登録確認:
```bash
launchctl list | grep zoomin
```

---

## 7. Tailscale のセットアップ（外部アクセス用）

1. https://tailscale.com からダウンロード・インストール
2. 同じアカウントで両方のMacにログイン
3. Mac MiniのTailscale IPを確認:
   ```bash
   tailscale ip
   ```

### リモートログインを有効化（Mac Mini側）
システム設定 → 一般 → 共有 → **リモートログイン** をオン

---

## 8. VS Code Remote SSH の設定（外出先のMacから接続）

1. VS Code で `Cmd+Shift+P` → 「Remote-SSH: Connect to Host」
2. `ssh ユーザー名@Mac-MiniのTailscaleIP` を入力
3. 接続後、`~/Desktop/claude code demo` を開く

---

## 9. 動作確認

```bash
cd ~/Desktop/claude\ code\ demo

# Threads投稿テスト（課金約0.2円）
python3 scripts/post_threads.py

# ログ確認
tail -f scripts/threads-post.log
```

---

## トラブルシューティング

| エラー | 対処 |
|--------|------|
| `ModuleNotFoundError: anthropic` | `pip3 install anthropic` |
| `THREADS_ACCESS_TOKEN が未設定` | `.env` を確認 |
| `launchctl load failed` | すでに登録済みの可能性。`launchctl list | grep zoomin` で確認 |
| SSH接続できない | Mac MiniのリモートログインがオンかTailscaleが起動しているか確認 |
