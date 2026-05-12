#!/usr/bin/env python3
"""
VS Code + Claude Code セットアップマニュアルをPDFで生成する。
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from pathlib import Path

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

OUTPUT = Path(__file__).parent.parent / 'output' / 'vscode-claude-code-setup.pdf'
OUTPUT.parent.mkdir(exist_ok=True)

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=20*mm, rightMargin=20*mm,
    topMargin=20*mm, bottomMargin=20*mm
)

F = 'HeiseiMin-W3'

styles = {
    'title':   ParagraphStyle('title',   fontName=F, fontSize=20, leading=28, spaceAfter=6, textColor=colors.HexColor('#1a1a1a')),
    'sub':     ParagraphStyle('sub',     fontName=F, fontSize=11, leading=16, spaceAfter=12, textColor=colors.HexColor('#555555')),
    'h1':      ParagraphStyle('h1',      fontName=F, fontSize=14, leading=20, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor('#0066cc')),
    'h2':      ParagraphStyle('h2',      fontName=F, fontSize=11, leading=16, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor('#333333')),
    'body':    ParagraphStyle('body',    fontName=F, fontSize=9,  leading=15, spaceAfter=4),
    'code':    ParagraphStyle('code',    fontName='Courier', fontSize=8, leading=13, spaceAfter=6,
                               backColor=colors.HexColor('#f5f5f5'), leftIndent=8, rightIndent=8,
                               borderPadding=(4,4,4,4)),
    'note':    ParagraphStyle('note',    fontName=F, fontSize=8,  leading=13, textColor=colors.HexColor('#888888'), spaceAfter=4),
}

def h(level, text): return Paragraph(text, styles[f'h{level}'])
def p(text):        return Paragraph(text, styles['body'])
def code(text):     return Preformatted(text, styles['code'])
def sp(h=4):        return Spacer(1, h*mm)
def hr():           return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#dddddd'), spaceAfter=4)
def note(text):     return Paragraph(f'※ {text}', styles['note'])

story = [
    Paragraph('VS Code + Claude Code', styles['title']),
    Paragraph('セットアップマニュアル　— Zoom In 内部用', styles['sub']),
    Paragraph('作成日: 2026年4月　／　対象機種: Mac（Apple Silicon）', styles['note']),
    hr(), sp(4),

    h(1, '1. 確認済み動作環境'),
    p('以下のバージョンで動作確認済み。'),
    sp(2),
    code(
        '  OS          : macOS (Apple Silicon)\n'
        '  Node.js     : v22.22.2  （nvm v0.39.7 で管理）\n'
        '  Claude Code : 2.1.112\n'
        '  Python      : 3.9.6\n'
        '  VS Code     : 1.96.0\n'
        '  npm         : 10.9.7'
    ),
    sp(4),

    h(1, '2. nvm（Node バージョン管理）のインストール'),
    p('Node.js を nvm で管理する。ターミナルで以下を実行。'),
    sp(2),
    code(
        '  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash\n\n'
        '  # シェルを再起動後、Node をインストール\n'
        '  nvm install 22\n'
        '  nvm use 22\n\n'
        '  # 確認\n'
        '  node --version   # → v22.x.x\n'
        '  npm --version    # → 10.x.x'
    ),
    sp(4),

    h(1, '3. Claude Code のインストール'),
    sp(2),
    code(
        '  npm install -g @anthropic-ai/claude-code\n\n'
        '  # 確認\n'
        '  claude --version   # → 2.1.112 (Claude Code)'
    ),
    sp(2),
    p('初回起動時に Anthropic アカウントへのログインが求められる。'),
    code('  claude'),
    sp(4),

    h(1, '4. VS Code のインストールと拡張機能'),
    h(2, '4-1. VS Code 本体'),
    p('https://code.visualstudio.com からダウンロードしてインストール。'),
    sp(2),

    h(2, '4-2. 必須拡張機能'),
    p('VS Code の拡張機能パネル（Cmd+Shift+X）から検索してインストール。'),
    sp(2),
    code(
        '  Claude Code       （Anthropic 公式）\n'
        '  Remote - SSH      （外部Macからアクセスする場合）'
    ),
    sp(2),
    note('Claude Code 拡張はVS Code起動時に自動でAnthropicアカウントと連携する。'),
    sp(4),

    h(1, '5. Python ライブラリのインストール'),
    sp(2),
    code(
        '  pip3 install anthropic      # Claude API\n'
        '  pip3 install requests       # HTTP通信\n'
        '  pip3 install reportlab      # PDF生成\n'
        '  pip3 install jpholiday      # 祝日判定'
    ),
    sp(4),

    h(1, '6. プロジェクトのセットアップ'),
    h(2, '6-1. フォルダの配置'),
    p('「claude code demo」フォルダを ~/Desktop/ に配置する。'),
    code('  ~/Desktop/claude code demo/'),
    sp(2),

    h(2, '6-2. .env ファイルの作成'),
    p('.env はgit管理外のため手動で作成。フォルダ直下に配置。'),
    code(
        '  ANTHROPIC_API_KEY=sk-ant-...\n'
        '  THREADS_ACCESS_TOKEN=THAA...\n'
        '  THREADS_USER_ID=36002571529341655\n'
        '  PERPLEXITY_API_KEY=（未設定の場合は your_api_key_here）\n'
        '  LINE_CHANNEL_ACCESS_TOKEN=...\n'
        '  LINE_CHANNEL_SECRET=...'
    ),
    sp(4),

    h(1, '7. Threads 自動投稿の有効化（launchd）'),
    sp(2),
    code(
        '  # plist を LaunchAgents にコピー\n'
        '  cp ~/Library/LaunchAgents/com.zoomin.threads-post.plist \\\n'
        '     ~/Library/LaunchAgents/\n\n'
        '  # 登録\n'
        '  launchctl load ~/Library/LaunchAgents/com.zoomin.threads-post.plist\n\n'
        '  # 確認\n'
        '  launchctl list | grep zoomin'
    ),
    note('毎日 6:00 / 12:00 / 18:00 に自動投稿される。'),
    sp(4),

    h(1, '8. 外部Macからのリモートアクセス（Tailscale + VS Code Remote SSH）'),
    h(2, '8-1. Tailscale のインストール'),
    p('https://tailscale.com から両方のMacにインストール。同じアカウントでログイン。'),
    sp(2),
    code(
        '  # Mac Mini 側でIPを確認\n'
        '  tailscale ip   # → 100.x.x.x'
    ),
    sp(2),

    h(2, '8-2. リモートログインを有効化（Mac Mini側）'),
    p('システム設定 → 一般 → 共有 → リモートログイン をオン'),
    sp(2),

    h(2, '8-3. VS Code から接続（外出先のMac側）'),
    code(
        '  # Cmd+Shift+P → Remote-SSH: Connect to Host\n'
        '  ssh ユーザー名@100.x.x.x\n\n'
        '  # 接続後、フォルダを開く\n'
        '  ~/Desktop/claude code demo'
    ),
    sp(4),

    h(1, '9. 動作確認'),
    code(
        '  cd ~/Desktop/claude\\ code\\ demo\n\n'
        '  # Threads投稿テスト（Claude API課金 約0.2円）\n'
        '  python3 scripts/post_threads.py\n\n'
        '  # ログ確認\n'
        '  tail -f scripts/threads-post.log'
    ),
    sp(6),

    hr(),
    Paragraph('Zoom In 内部資料　／　作成: Claude Code (claude-sonnet-4-6)', styles['note']),
]

doc.build(story)
print(f'出力完了: {OUTPUT}')
