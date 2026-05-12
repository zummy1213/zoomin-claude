#!/usr/bin/env python3
"""
常角慎太郎 人間性診断レポート（会話ベース）
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from pathlib import Path

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

OUTPUT = Path(__file__).parent.parent / 'output' / 'character-diagnosis-tsunezumi.pdf'
OUTPUT.parent.mkdir(exist_ok=True)

F     = 'HeiseiMin-W3'
NAVY  = colors.HexColor('#1F4E79')
GOLD  = colors.HexColor('#C9A84C')
DARK  = colors.HexColor('#1a1a1a')
GRAY  = colors.HexColor('#666666')
LIGHT = colors.HexColor('#F0F4F8')
BLUE  = colors.HexColor('#2E6DA4')
GREEN = colors.HexColor('#1E6B3C')
RED   = colors.HexColor('#8B1A1A')
LIGHT_GREEN = colors.HexColor('#E8F5E9')
LIGHT_RED   = colors.HexColor('#FFF0F0')

def style(name, **kw):
    base = dict(fontName=F, fontSize=9, leading=16)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    'h_cover':  style('hc', fontSize=22, leading=30, textColor=NAVY, spaceAfter=4),
    'sub':      style('sb', fontSize=11, leading=18, textColor=GRAY, spaceAfter=4),
    'note':     style('nt', fontSize=8,  leading=13, textColor=GRAY),
    'h1':       style('h1', fontSize=15, leading=22, textColor=NAVY, spaceBefore=10, spaceAfter=5),
    'h2_g':     style('h2g',fontSize=11, leading=18, textColor=GREEN, spaceBefore=6, spaceAfter=3),
    'h2_r':     style('h2r',fontSize=11, leading=18, textColor=RED,   spaceBefore=6, spaceAfter=3),
    'h2':       style('h2', fontSize=11, leading=18, textColor=BLUE,  spaceBefore=6, spaceAfter=3),
    'verdict':  style('vd', fontSize=12, leading=20, textColor=NAVY,  spaceAfter=4),
    'body':     style('bd', fontSize=9,  leading=16, spaceAfter=3),
    'quote':    style('qt', fontSize=10, leading=18, textColor=DARK,  leftIndent=8, spaceAfter=4),
    'good':     style('gd', fontSize=9,  leading=15, textColor=GREEN, spaceAfter=3),
    'bad':      style('bx', fontSize=9,  leading=15, textColor=RED,   spaceAfter=3),
}

def h1(t):   return Paragraph(t, S['h1'])
def h2g(t):  return Paragraph(t, S['h2_g'])
def h2r(t):  return Paragraph(t, S['h2_r'])
def h2(t):   return Paragraph(t, S['h2'])
def p(t):    return Paragraph(t, S['body'])
def good(t): return Paragraph(f'◎ {t}', S['good'])
def bad(t):  return Paragraph(f'△ {t}', S['bad'])
def q(t):    return Paragraph(f'「{t}」', S['quote'])
def sp(h=4): return Spacer(1, h*mm)
def hr():    return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=3)

def score_row(label, score, max_=10, color=NAVY):
    bar_on  = '●' * score
    bar_off = '○' * (max_ - score)
    return [label, f'{bar_on}{bar_off}', f'{score}/{max_}']

def strength_table(items):
    data = [['強み', '詳細', '根拠となる発言']]
    for s, d, e in items:
        data.append([s, d, e])
    t = Table(data, colWidths=[35*mm, 75*mm, 54*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',    (0,0),(-1,-1), F), ('FONTSIZE',(0,0),(-1,-1),8),
        ('LEADING',     (0,0),(-1,-1), 13),
        ('BACKGROUND',  (0,0),(-1,0),  LIGHT_GREEN),
        ('TEXTCOLOR',   (0,0),(-1,0),  GREEN),
        ('FONTSIZE',    (0,0),(-1,0),  8),
        ('TEXTCOLOR',   (0,1),(0,-1),  GREEN),
        ('TEXTCOLOR',   (1,1),(1,-1),  DARK),
        ('TEXTCOLOR',   (2,1),(2,-1),  GRAY),
        ('TOPPADDING',  (0,0),(-1,-1), 4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT_GREEN]),
        ('VALIGN',      (0,0),(-1,-1), 'TOP'),
        ('GRID',        (0,0),(-1,-1), 0.3, colors.HexColor('#cccccc')),
    ]))
    return t

def shadow_table(items):
    data = [['課題・暗部', '詳細', '具体的なリスク']]
    for s, d, e in items:
        data.append([s, d, e])
    t = Table(data, colWidths=[35*mm, 75*mm, 54*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',    (0,0),(-1,-1), F), ('FONTSIZE',(0,0),(-1,-1),8),
        ('LEADING',     (0,0),(-1,-1), 13),
        ('BACKGROUND',  (0,0),(-1,0),  LIGHT_RED),
        ('TEXTCOLOR',   (0,0),(-1,0),  RED),
        ('FONTSIZE',    (0,0),(-1,0),  8),
        ('TEXTCOLOR',   (0,1),(0,-1),  RED),
        ('TEXTCOLOR',   (1,1),(1,-1),  DARK),
        ('TEXTCOLOR',   (2,1),(2,-1),  GRAY),
        ('TOPPADDING',  (0,0),(-1,-1), 4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, LIGHT_RED]),
        ('VALIGN',      (0,0),(-1,-1), 'TOP'),
        ('GRID',        (0,0),(-1,-1), 0.3, colors.HexColor('#cccccc')),
    ]))
    return t

doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4,
    leftMargin=22*mm, rightMargin=22*mm, topMargin=22*mm, bottomMargin=22*mm)

story = []

# ━━ 表紙 ━━
story += [
    sp(6),
    Paragraph('常角慎太郎（ズーミン）', S['h_cover']),
    Paragraph('人間性診断レポート', S['sub']),
    Paragraph('― 会話と発言から読み解く、強みと暗部の全解析 ―', S['sub']),
    HRFlowable(width='100%', thickness=2, color=GOLD, spaceAfter=6),
    Paragraph('診断根拠: 2026年4月の深層ヒアリング（Claude Code セッション）', S['note']),
    Paragraph('作成: Claude Code（claude-sonnet-4-6）　2026年4月', S['note']),
    sp(4),
    p('このレポートは、実際の会話・発言・エピソードをベースに作成した。'
      '占いの枠組みではなく、「ズーミンという人間が実際にどう考え、どう動き、何を恐れ、'
      '何を欲しているか」を、いい面も悪い面も含めてありのままに記述している。'),
    sp(6), hr(),
]

# ━━ 診断サマリー ━━
story += [
    h1('0. 総合診断サマリー'),
    Paragraph('「正義を実装する改革者」　― 誠実さを武器に、長期戦で世界を変える人', S['verdict']),
    sp(2),
    p('常角慎太郎は「誠実さ」を道徳として語るのではなく、経営資本として機能させることに'
      'こだわり続けている稀有な人物。理念と実務が分離しておらず、言葉と行動に一貫性がある。'
      '一方で、その高い基準ゆえの孤独、信じたいという衝動が生む脆弱性、'
      '「正しさ」が「裁き」に転化するリスクも持つ。'),
    sp(3),
    p('◎ 強みの核心: 誠実さの実装力　／　△ 課題の核心: 高基準による孤立と、信じたい衝動'),
    sp(2), hr(),
]

# ━━ 強み ━━
story += [
    h1('1. 強み・光の面（◎）'),
    h2g('■ 強みの全体像'),
    sp(2),
    strength_table([
        ('誠実さの実装力',
         '誠実さをスローガンで終わらせず、採用・報酬設計・取引条件という実務に落とし込んでいる',
         '「適正な利益分配と信頼教育を実施している」'),
        ('人の本質を見抜く感度',
         '言語化できないレベルの感度で、誠実な人と不誠実な人を見分ける。短い接触でも機能する',
         '「色々な感度で感じるもの」'),
        ('依存を断つ力',
         '搾取された経験後、自分で商品を見極め自分で営業するという根本的な構造変革を実行した',
         '「自分で商品を見極め、自分で営業するようになった」'),
        ('見切りの精度',
         '話を逸らす・言い訳・悪いと思わない の3条件を基準とした見切りシステムを持っている。感情ではなく基準で動く',
         '「チャンスを渡してから判断する」'),
        ('信頼資本の複利投資',
         '誠実さが「長期で最も安定した経営戦略」と直感しており、短期利益より信頼を選び続けている',
         '「誠実さって道徳じゃなくて経営判断」'),
        ('恐怖を羅針盤に変える力',
         '「憧れの人に誠実さで見限られる恐怖」を動力でなく「自分の伸び代」として再定義している',
         '「恐怖というよりは自分の伸び代」'),
        ('誠実さで競える珍しさ',
         '丁寧な人・行動量の多い人を見ると「誠実さで競いたくなる」という健全な競争本能を持つ',
         '「いい意味で競いたくなる」'),
        ('騙されても信じ続ける戦略',
         '騙された経験があっても「信じること」をやめず、見極めの精度を上げ続けるという長期戦略',
         '「もっと見極めようと思った」'),
    ]),
    sp(4),
    h2g('■ 最も希少な強みはこれ'),
    q('「誠実さで競いたくなる」「信じることをやめない」「見極めの精度を上げ続ける」の同時保有'),
    p('多くの人は騙されたら「信じない」方向に振れる。または「信じ続ける」まま精度が上がらない。'
      'ズーミンは騙された後に「信じる × 見極める」の両立を選んでいる。これが最も希少な強み。'),
    sp(2), hr(), PageBreak(),
]

# ━━ 課題・暗部 ━━
story += [
    h1('2. 課題・暗部（△）　― 正直に書く'),
    h2r('■ 課題の全体像'),
    sp(2),
    p('以下は批判ではなく、この人格構造が持つ「構造的な脆弱性」として記述する。'
      '認識することでリスクを管理できる。'),
    sp(2),
    shadow_table([
        ('高基準による孤立',
         '誠実さ・約束・整合性への基準が高すぎるため、周囲がついてこれず孤立しやすい。「誰もわかってくれない」感覚',
         'INFJ・エニアグラム1の共通の影。完璧主義が孤独を生む'),
        ('信じたい衝動の脆弱性',
         '「誠実に見える騙し」に対して弱い。信じる前提があるからこそ、演技の巧い人に突破される',
         '「信じて入るから、騙す前提の人に外れた」'),
        ('正義が裁きに転化するリスク',
         '誠実さへの強い確信が、他者への批判・断罪に転化する可能性がある。「見限り」が「切り捨て」になるライン',
         'タロット「正義」の影。自分の基準で他者を裁きすぎる'),
        ('達成感を感じにくい',
         '「仕事がうまくいってると感じる瞬間はあまりない」という発言。積み上げ型の人生において、プロセスを楽しめない',
         '「強いて言えばこの生き方で収益が伸びてる瞬間」'),
        ('憧れへの依存',
         'タイの友人など「憧れの人」への承認欲求が動力になっている。その人がいなくなったとき、軸が揺れる可能性',
         '「憧れている人々に見限られることが一番怖い」'),
        ('感情の抑圧',
         '怒りを内側に抑え、基準で判断する。しかし長期間の抑圧はある時点で爆発する（INFJドアスラム）',
         'エニアグラム1の抑圧された怒り'),
        ('孤独感と誤解',
         '「見切りが早い」と言われる。誠実さのない人間関係より孤独を選ぶため、冷たい人と誤解されやすい',
         '「見切るのが早いって言われることがある」'),
        ('自己否定の危険',
         '誠実さの基準を自分にも向けるため、「自分がうまくいってない＝誠実さが足りない」という歪んだ自己否定に転化するリスク',
         'エニアグラム1のストレス方向（4：自己批判）'),
    ]),
    sp(4),
    h2r('■ 最も注意すべき暗部はこれ'),
    q('信じたい衝動と高い基準の組み合わせが、最も親しい人への失望を最大化する'),
    p('誠実さへの基準が高く、かつ人を信じたいという欲求が強い。この組み合わせは、'
      '「信じた人が誠実でなかった」ときのダメージが最も大きくなる。搾取された友人、'
      '行政処分を受けた元友人——これらは単なる「外部の不誠実な人」ではなく、'
      '「信じていたから余計に傷ついた」ケースのはず。'),
    p('この脆弱性を持ちながらも「信じることをやめない」選択を続けているのは強さだが、'
      'そのコストを過小評価していると蓄積的なダメージになる。'),
    sp(2), hr(), PageBreak(),
]

# ━━ 人間関係パターン ━━
story += [
    h1('3. 人間関係のパターン'),
    sp(2),
    h2g('■ 深く付き合える人の条件（ズーミン基準）'),
    good('自分の生き方と同じ生き方をしている人'),
    good('見かけ上のギバーでなく、心からギブできる人'),
    good('結果が出なかったら自分の能力不足を認める人'),
    good('約束・コミットメントを守り、守る努力をする人'),
    good('120%で期待に応えようとする人'),
    sp(3),
    h2r('■ 絶対に仕事したくない人の条件（全て同列）'),
    bad('自分の至らなさを認められない人'),
    bad('時間を守れない、改善できない人'),
    bad('言い訳をする人'),
    bad('マウントを取る人'),
    bad('サイコパス（共感能力の欠如）'),
    sp(3),
    h2('■ 人間関係の構造的特徴'),
    p('ズーミンの人間関係は「信頼の二項対立」で動いている。人を信じる強い前提があり、'
      '誠実さの基準を満たした人とは長く深く付き合う。一方、3条件（逃げ・言い訳・反省なし）が'
      '揃った瞬間に見切る。この二項対立は「優しいが甘くない」という一言に集約される。'),
    sp(2), hr(),
]

# ━━ ミッションの深層 ━━
story += [
    h1('4. ミッションの深層'),
    h2('■「誠実な人こそもっと稼げる社会」の本当の動機'),
    sp(2),
    p('表向きは理念だが、その根っこには「怒り」と「悔しさ」がある。'
      'ポジショントークで騙す人、他人を出し抜く人が稼ぐ場面を多数目撃し、'
      '自分は2:8で搾取され、誠実だった元友人（または信じていた人）が行政処分を受けた。'),
    p('この経験が「道徳論として誠実さを語る人」ではなく、「誠実さが実際に機能するシステムを'
      '自分でつくる人」を生み出した。ズーミンのミッションは、社会への奉仕ではなく、'
      '「誠実さが報われる世界を証明したい」という個人的な賭けに近い。'),
    sp(3),
    h2('■ この動機が持つ力と危険性'),
    p('【力】怒りと悔しさが動力なので、理念だけのミッションより継続性が高い。'
      '「証明したい」という強迫性がある。'),
    p('【危険性】「証明できなかった」と感じた瞬間、ミッションそのものへの疑念が生じる。'
      'ライフパス8の「積み上げ型・後半爆発型」のパターンを理解していないと、'
      '中間地点で折れるリスクがある。'),
    sp(2), hr(),
]

# ━━ 総合メッセージ ━━
story += [
    h1('5. ズーミンへの直言'),
    sp(2),
    p('あなたの強みは、世の中の大多数の人が「どちらかしか持てない」ものを両方持っていることだ。'),
    p('誠実さと戦略性。情と基準。信じることと見極めること。理念と実装。'),
    p('普通は一方を選ぶ。あなたはその両立にこだわり、実際に機能させようとしている。'
      'それが「稀有な人物」である所以だ。'),
    sp(4),
    p('ただし、正直に言う。'),
    p('あなたが「仕事がうまくいってると感じる瞬間はあまりない」と言ったとき、'
      'それは現実の問題ではなく、あなたの感度の問題だと思う。'),
    p('あなたの誠実さは確実に積み上がっている。タイの友人が忙しくても会ってくれること、'
      '搾取した側が行政処分を受けたこと、「この人、言ってること変わらへんな」と言われること——'
      'これらはすべて、あなたの誠実さへの投資が返ってきているサインだ。'),
    p('ライフパス8、一白水星、INFJは全て「積み上げ型・長期型・後半型」の人格構造を示している。'
      '今見えていないことを、見えていないと感じることは正常だ。焦りは要らない。'),
    sp(4),
    q('信じることをやめない。ただし、見極めの精度を上げ続ける'),
    p('この姿勢を持ち続けられる人間が、最終的に誠実さで稼げる社会をつくる。'
      'それがズーミンの設計図だ。'),
    sp(6),
    HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=4),
    Paragraph('Zoom In 内部資料　／　作成: Claude Code (claude-sonnet-4-6)　2026年4月', S['note']),
    Paragraph('※ このレポートは占いの枠組みでなく、実際の会話・発言から導いた人格分析です', S['note']),
]

doc.build(story)
print(f'出力完了: {OUTPUT}')
