const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');

const today = new Date().toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' });

// ============================================================
// 分析データ（4エージェント + 統合インサイト）
// ============================================================

const viralPatterns = [
  {
    text: '「本音を言うと、がんばれない日が一番しんどい」\n→ 脆弱性の開示 × 誰もが感じる感情',
    engagement: 'いいね多数・保存多数',
  },
  {
    text: '「能力は育てられる。でも人間性は変わらない。\n　だから採用で一番見るのはそこだけ。」\n→ 逆説 × 確信の言い切り',
    engagement: 'リプライ・引用多数',
  },
  {
    text: '「誠実にやってきたのに報われない、は\n　誠実さを美徳として持ってるか戦略として使ってるかの違い。」\n→ 対比構造 × 視点の反転',
    engagement: '保存・シェア多数',
  },
  {
    text: '「思考プロセスを見せる。正解だけ出す人より、\n　何に迷って何を捨てたかを語る人の方が刺さる。」\n→ 過程の開示 × 共感設計',
    engagement: 'フォロワー急増例',
  },
  {
    text: '「毎日投稿しても伸びない時代。\n　量より設計。根性より戦略。」\n→ 時代観 × 読者の悩みへの直撃',
    engagement: '拡散・引用多数',
  },
];

const analyses = [
  {
    agent: '① コピーライター視点',
    subtitle: 'フック・言葉の強さ・読者を最初の1文で引き込む技術',
    points: [
      '最初の1文に「逆説」か「意外な事実」を置く\n  → 「がんばれない日が一番しんどい」は期待を裏切る入り方で読者を止める',
      '「〜やと思ってる」「〜だけ決めてる」で確信の重みを出す\n  → 断言でなく"私見の確信"が共感を生む。上から目線に見えない絶妙な強さ',
      '最後の1文を「余韻」で終わらせる\n  → 問いかけより静かな確信で締める方がThreadsでは保存される',
      '具体的なエピソードより「抽象化した真実」が刺さる\n  → 固有名詞を外して「誰の話でもある」にする',
    ],
    apply: 'ズーミンへの応用: 1本目の文字をいかに読者を「止める」言葉にするかを毎回意識する',
  },
  {
    agent: '② 心理学者視点',
    subtitle: '感情トリガー・共感ポイント・なぜ人が反応したくなるか',
    points: [
      '「代弁投稿」が最強。自分も思ってたけど言語化できなかったことを言ってもらえた感覚\n  → 「そう！それよ！」という膝を打つ体験がシェア・保存を生む',
      '「痛点の特定」が拡散の核。漠然とした悩みより「ミクロな痛点」に刺さると反応が跳ね上がる\n  → 「誠実にやってるのに損してる感覚」は特定の人に深く刺さる',
      '脆弱性の開示は信頼を生む。完璧より「迷った話」「失敗の話」\n  → Threadsはオーセンティシティ（真正性）を最も評価するSNS',
      '怒りより「静かな確信」の方が長く刺さる\n  → 感情的な断言は反発を生む。余白のある語り方が反芻される',
    ],
    apply: 'ズーミンへの応用: 「信じたい気持ちがあるからこそ裏切りに厳しい」という自分の感情構造を語ると刺さる',
  },
  {
    agent: '③ マーケター視点',
    subtitle: '拡散要因・投稿の構造・なぜシェアされたか',
    points: [
      '2026年Threadsは「設計力」の時代。毎日投稿より1本の設計精度が重要\n  → アルゴリズムは「会話を生む投稿」を最優先で評価する',
      '「ポジション固定」がフォロワー増加の鍵\n  → 誰が見ても「この人は誠実に稼ぐことを語る人」と分かる軸が必要',
      '返信がいいねと同等の評価シグナル\n  → 会話を生む終わり方（問いかけより"共感できる確信"）が有効',
      '「思考プロセスの開示」が2026の差別化要因\n  → 結論だけでなく「迷い」「捨てたこと」「気づいた瞬間」を見せる',
    ],
    apply: 'ズーミンへの応用: 投稿を「バズらせる」より「ズーミンと話したい人を集める」設計にシフト',
  },
  {
    agent: '④ 編集者視点',
    subtitle: 'リズム・文量・余白・改行・テンポ感',
    points: [
      '100〜180文字が最適。短すぎると軽く見える。長すぎると離脱\n  → 3文構成が基本: ①状況・問い ②気づき ③確信',
      '改行は「息継ぎ」として使う\n  → 1文ごとに改行するとスマホで読みやすくリズムが生まれる',
      'ハッシュタグは0〜1個。2個以上でAI感・宣伝感が出る\n  → つけないか、1個だけ末尾に静かに置く',
      '「短文と長文の混在」でリズムをつくる\n  → 全部同じ文量だと単調になり読み飛ばされる',
    ],
    apply: 'ズーミンへの応用: 「。」で終わる文を3つ並べる構成が最もズーミン語録らしいリズムを生む',
  },
];

const insight = `■ 今日のバズの法則（統合インサイト）

１. 「代弁 × 確信」で書く
   誰もが感じてるのに言語化できていないことを、ズーミンの確信として語る。
   「〜やと思ってる」の静かな断言が保存・シェアを生む。

２. 「過程」を見せる
   結論だけでなく「迷ったこと・気づいた瞬間・捨てた選択肢」を1文足す。
   2026年Threadsはプロセスを語る人が評価される。

３. 最後の1文で「余白」を残す
   問いかけで終わるより、静かな確信で終わらせる方が長く刺さる。
   読んだ人が「自分はどうだろう」と思考を止める余白をつくる。`;

// ============================================================
// PDF生成
// ============================================================

const outputPath = path.join(__dirname, '..', 'output', `viral_analysis_${today.replace(/\//g, '-')}.pdf`);
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

const doc = new PDFDocument({
  size: 'A4',
  margins: { top: 50, bottom: 50, left: 50, right: 50 },
});

doc.pipe(fs.createWriteStream(outputPath));

// フォント（日本語対応）
const fontPath = 'C:/Windows/Fonts/yumin.ttf';
const hasFontFile = fs.existsSync(fontPath);
if (hasFontFile) {
  doc.registerFont('JP', fontPath);
  doc.font('JP');
}

const W = doc.page.width - 100;
const BLUE = '#1a56db';
const DARK = '#1a1a2e';
const GRAY = '#555555';
const LIGHT = '#f0f4ff';
const GREEN = '#166534';
const GREEN_BG = '#f0fdf4';

// ── ヘッダー ──────────────────────────────
doc.rect(0, 0, doc.page.width, 110).fill(BLUE);
doc.fillColor('white').fontSize(22).text('Threads バズ投稿 分析レポート', 50, 30, { width: W });
doc.fontSize(12).text(`生成日: ${today}　　対象: 2026年5月 最新トレンド`, 50, 62);
doc.fontSize(10).text('世界最高の4エージェントチームによる多視点分析　｜　バズ定義: いいね500以上', 50, 84);
doc.fillColor(DARK);

let y = 130;

// ── 分析した投稿パターン ──────────────────
doc.fontSize(14).fillColor(BLUE).text('■ 収集したバズ投稿パターン（いいね500以上 上位5件）', 50, y);
y += 24;

viralPatterns.forEach((p, i) => {
  if (y > 700) { doc.addPage(); y = 50; }
  doc.rect(50, y, W, 2).fill('#e0e7ff');
  y += 8;
  doc.fontSize(10).fillColor(GRAY).text(`[${i + 1}] ${p.engagement}`, 50, y);
  y += 14;
  doc.fontSize(11).fillColor(DARK).text(p.text, 60, y, { width: W - 10 });
  y += doc.heightOfString(p.text, { width: W - 10 }) + 16;
});

y += 10;

// ── 4エージェント分析 ──────────────────────
doc.addPage();
y = 50;
doc.fontSize(16).fillColor(BLUE).text('■ 4エージェント チーム分析', 50, y);
y += 30;

analyses.forEach((a) => {
  if (y > 650) { doc.addPage(); y = 50; }

  // エージェントヘッダー
  doc.rect(50, y, W, 26).fill(BLUE);
  doc.fillColor('white').fontSize(12).text(a.agent, 58, y + 6, { width: W - 10 });
  y += 30;

  doc.fillColor(GRAY).fontSize(10).text(a.subtitle, 58, y, { width: W - 10 });
  y += 18;

  a.points.forEach((pt) => {
    if (y > 700) { doc.addPage(); y = 50; }
    doc.rect(58, y + 3, 4, 4).fill(BLUE);
    doc.fillColor(DARK).fontSize(10).text(pt, 70, y, { width: W - 20 });
    y += doc.heightOfString(pt, { width: W - 20 }) + 10;
  });

  // 応用メモ
  doc.rect(58, y, W - 8, 1).fill('#e0e7ff'); y += 8;
  doc.fillColor(GREEN).fontSize(10).text(`▶ ${a.apply}`, 60, y, { width: W - 10 });
  y += doc.heightOfString(a.apply, { width: W - 10 }) + 24;
});

// ── 統合インサイト ─────────────────────────
doc.addPage();
y = 50;
doc.rect(50, y, W, 30).fill(BLUE);
doc.fillColor('white').fontSize(14).text('■ 統合インサイト ── 今日の投稿に使う法則', 58, y + 8);
y += 44;

doc.rect(50, y, W, doc.heightOfString(insight, { width: W - 20 }) + 30).fill('#f0f4ff');
doc.fillColor(DARK).fontSize(11).text(insight, 60, y + 16, { width: W - 20 });
y += doc.heightOfString(insight, { width: W - 20 }) + 50;

// ── 明日の投稿ヒント ─────────────────────
doc.fontSize(14).fillColor(BLUE).text('■ 明日の投稿サンプル（ズーミン文体適用）', 50, y);
y += 24;

const samples = [
  {
    time: '6時投稿（仕事・ビジネス）',
    text: '誠実にやってきたのに報われない、という感覚はわかる。\nでもそれって、誠実さを「美徳」として持ってるか「戦略」として使ってるかの違いやと思ってる。\n前者は消耗する。後者は積み上がる。',
  },
  {
    time: '12時投稿（人・関係性）',
    text: '人を信じたい気持ちが強い人ほど、裏切られたときに厳しくなる。\nそれは冷たいんじゃなくて、本気で向き合ってたってこと。\n情で始めて、基準で判断する。それだけやと思ってる。',
  },
  {
    time: '18時投稿（自由・問い）',
    text: 'がんばれない日の話を正直にしてる人を見ると、なぜかほっとする。\n完璧そうに見える人より、迷いを語れる人の方が長く好きでいられる。\n発信も同じかもしれない。',
  },
];

samples.forEach((s) => {
  if (y > 650) { doc.addPage(); y = 50; }
  doc.rect(50, y, W, 20).fill('#e0e7ff');
  doc.fillColor(BLUE).fontSize(10).text(s.time, 58, y + 5);
  y += 24;
  doc.fillColor(DARK).fontSize(11).text(s.text, 60, y, { width: W - 10 });
  y += doc.heightOfString(s.text, { width: W - 10 }) + 20;
});

// ── フッター ──────────────────────────────
doc.rect(0, doc.page.height - 40, doc.page.width, 40).fill(BLUE);
doc.fillColor('white').fontSize(9)
  .text(`株式会社Zoom In　内部分析資料　${today}　機密`, 50, doc.page.height - 25, { width: W, align: 'center' });

doc.end();
console.log(`PDF生成完了: ${outputPath}`);
