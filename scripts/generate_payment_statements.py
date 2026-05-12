#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
毎月10日に前月分の支払明細書・紹介料明細書を自動生成する。
対象: ZoomIn個別 / 畑野まなか一括 / 株式会社ハイブレス一括 / 紹介料
"""
import os, sys, math, datetime, json, io, zipfile, xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import jpholiday
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
F = 'HeiseiKakuGo-W5'

CREDS_FILE  = Path.home() / '.claude' / 'gdrive-credentials.json'
TOKEN_FILE  = Path.home() / '.claude' / 'gdrive-token.json'
BASE_DIR    = Path(__file__).parent.parent
OUTPUT_BASE = BASE_DIR / 'output'
SPREADSHEET_NAME = '在宅ワーク業務委託費管理表'

COMPANY = ['株式会社Zoom In', '〒541-0056', '大阪市中央区久太郎町1-6-27', 'ルクレ堺筋本町レジデンス402']

# グループ → 支払先
GROUP_PAYEE = {
    '畑野さん': '畑野まなか',
    '前原さん': '株式会社ハイブレス',
}

# スプレッドシート上の紹介者名 → 正式名
REFERRER_NAMES = {
    'まき': 'カワシマ マキコ',
}

# ── 日付計算 ─────────────────────────────────────────────
def target_month(today=None):
    d = today or datetime.date.today()
    prev = d.replace(day=1) - datetime.timedelta(days=1)
    return prev.year, prev.month

def issuer_date(year, month):
    if month == 12: return datetime.date(year+1, 1, 20)
    return datetime.date(year, month+1, 20)

def payment_date(year, month):
    if month == 12: ny, nm = year+1, 1
    else: ny, nm = year, month+1
    d = datetime.date(ny, nm, 25)
    while d.weekday() >= 5 or jpholiday.is_holiday(d):
        d += datetime.timedelta(days=1)
    return d

# ── Google Drive ─────────────────────────────────────────
def get_drive_service():
    token_data = json.load(open(TOKEN_FILE))
    creds_data = json.load(open(CREDS_FILE))['installed']
    creds = Credentials(
        token=token_data.get('access_token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=creds_data['token_uri'],
        client_id=creds_data['client_id'],
        client_secret=creds_data['client_secret'],
        scopes=['https://www.googleapis.com/auth/drive.readonly'],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as f:
            json.dump(json.loads(creds.to_json()), f)
    return build('drive', 'v3', credentials=creds)

def download_spreadsheet(service):
    results = service.files().list(
        q=f"name contains '{SPREADSHEET_NAME}' and trashed=false",
        fields='files(id, name)'
    ).execute()
    files = results.get('files', [])
    if not files:
        raise FileNotFoundError(f'{SPREADSHEET_NAME} がGoogleドライブに見つかりません')
    file_id = files[0]['id']
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, service.files().get_media(fileId=file_id))
    done = False
    while not done: _, done = downloader.next_chunk()
    buf.seek(0)
    return buf

# ── xlsx解析 ─────────────────────────────────────────────
def parse_month_sheet(buf, year, month):
    """指定月のシートからワーカーデータと紹介料データを抽出"""
    month_str = f'{year}{month:02d}月'
    workers   = []   # 支払明細用
    referrals = defaultdict(list)  # 紹介料用 {referrer: [(worker, hours, rate, fee)]}

    with zipfile.ZipFile(buf) as z:
        # 共有文字列
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.parse(z.open('xl/sharedStrings.xml'))
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            for si in tree.getroot().iter(f'{ns}si'):
                strings.append(''.join(x.text or '' for x in si.iter(f'{ns}t')))

        # シートファイルを特定
        wb = ET.parse(z.open('xl/workbook.xml'))
        rels = ET.parse(z.open('xl/_rels/workbook.xml.rels'))
        rel_map = {r.get('Id'): r.get('Target') for r in rels.getroot()}
        ns2 = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
        sheet_file = None
        for s in wb.getroot().iter(f'{ns2}sheet'):
            if s.get('name') == month_str:
                rid = s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                sheet_file = 'xl/' + rel_map[rid]
                break
        if not sheet_file:
            raise ValueError(f'シート {month_str} が見つかりません')

        tree = ET.parse(z.open(sheet_file))
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

        def cv(c):
            t = c.get('t', '')
            v = c.find(f'{ns}v')
            if v is None: return ''
            return strings[int(v.text)] if t == 's' else v.text

        def fv(s):
            try: return float(s) if s else 0.0
            except (ValueError, TypeError): return 0.0

        rows = list(tree.getroot().iter(f'{ns}row'))
        # 久保のような同名2行をまとめるための一時辞書
        zoomin_map = {}

        for row in rows[2:]:  # ヘッダー2行スキップ
            cells = list(row.iter(f'{ns}c'))
            if len(cells) < 4: continue
            vals = [cv(c) for c in cells]

            group = vals[1].strip() if len(vals) > 1 else ''
            name  = vals[2].strip() if len(vals) > 2 else ''
            if not name or name in ('その他',): continue

            hours      = fv(vals[4])  if len(vals) > 4  else 0
            reward_inc = fv(vals[7])  if len(vals) > 7  else 0
            i1_inc     = fv(vals[8])  if len(vals) > 8  else 0
            i2_inc     = fv(vals[9])  if len(vals) > 9  else 0
            transport  = fv(vals[11]) if len(vals) > 11 else 0
            pc_inc     = abs(fv(vals[12])) if len(vals) > 12 else 0
            advance    = abs(fv(vals[13])) if len(vals) > 13 else 0
            ref1       = vals[16].strip() if len(vals) > 16 else ''
            rate1      = fv(vals[17])     if len(vals) > 17 else 0
            fee1       = fv(vals[18])     if len(vals) > 18 else 0
            ref2       = vals[19].strip() if len(vals) > 19 else ''
            rate2      = fv(vals[20])     if len(vals) > 20 else 0
            fee2       = fv(vals[21])     if len(vals) > 21 else 0

            # ── 支払明細データ ─────────────────────────────
            if group == 'ZoomIn':
                if hours > 0:
                    key = name
                    if key in zoomin_map:
                        # 同名2行目 → サブ区分として追加
                        zoomin_map[key]['sub'].append(dict(
                            hours=hours, reward_inc=reward_inc,
                        ))
                    else:
                        zoomin_map[key] = dict(
                            name=name, group=group,
                            hours=hours, reward_inc=reward_inc,
                            i1_inc=i1_inc, i2_inc=i2_inc,
                            transport=transport, pc_inc=pc_inc,
                            advance_inc=advance, sub=[],
                        )

            elif group in GROUP_PAYEE:
                if hours > 0:
                    workers.append(dict(
                        name=name, group=group,
                        payee=GROUP_PAYEE[group],
                        hours=hours, reward_inc=reward_inc,
                        i1_inc=i1_inc, i2_inc=i2_inc,
                        transport=transport, pc_inc=pc_inc,
                        advance_inc=advance,
                    ))

            # ── 紹介料データ（グループ有効・稼働あり行のみ）──────────
            if group and hours > 0:
                if ref1 and fee1 > 0:
                    r1 = REFERRER_NAMES.get(ref1, ref1)
                    referrals[r1].append((name, hours, int(rate1), int(fee1)))
                if ref2 and fee2 > 0:
                    r2 = REFERRER_NAMES.get(ref2, ref2)
                    referrals[r2].append((name, hours, int(rate2), int(fee2)))

        # ZoomIn をリストに変換
        for w in zoomin_map.values():
            workers.insert(0, w)

    return workers, referrals

# ── PDF共通部品 ──────────────────────────────────────────
fl = math.floor
def fmt(n): return '0' if n == 0 else f'{int(n):,}'
def neg(n): return '0' if n == 0 else f'({int(n):,})'

def p(text, size=10, align=0, color=colors.black):
    return Paragraph(text, ParagraphStyle('', fontName=F, fontSize=size,
                                          leading=size*1.3, alignment=align, textColor=color))

def cs(*cmds):
    base = [('FONTNAME',(0,0),(-1,-1),F),
            ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]
    return TableStyle(base + list(cmds))

def section_bar(title, W):
    t = Table([[title]], colWidths=[W])
    t.setStyle(cs(('FONTSIZE',(0,0),(-1,-1),10),
                  ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#333333')),
                  ('TEXTCOLOR',(0,0),(-1,-1),colors.white)))
    return t

def highlight_table(rows, col_widths):
    sty = [('FONTNAME',(0,0),(-1,-1),F),('FONTSIZE',(0,0),(-1,-1),9),
           ('ALIGN',(1,0),(1,-1),'RIGHT'),
           ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#bbbbbb')),
           ('INNERGRID',(0,0),(-1,-1),0.5,colors.HexColor('#dddddd')),
           ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
           ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]
    for i, row in enumerate(rows):
        if len(row) > 2 and row[2]:
            sty += [('BACKGROUND',(0,i),(-1,i),colors.HexColor('#fff8cc')),
                    ('FONTSIZE',(0,i),(-1,i),10)]
    t = Table([[r[0], r[1]] for r in rows], colWidths=col_widths)
    t.setStyle(TableStyle(sty))
    return t

def doc_header(story, title, issuer, payment, info_rows, W):
    hdr = Table([[p(title, 15),
                  p('<br/>'.join(COMPANY), 7, align=2, color=colors.HexColor('#555555'))]],
                colWidths=[90*mm, 90*mm])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(hdr)
    story.append(Spacer(1, 3*mm))
    story.append(p(f'発行日: {issuer.strftime("%Y/%m/%d")}　　支払日: {payment.strftime("%Y/%m/%d")}', 8))
    story.append(Spacer(1, 3*mm))
    info = Table(info_rows, colWidths=[28*mm, 152*mm])
    info.setStyle(cs(('FONTSIZE',(0,0),(-1,-1),10),
                     ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eeeeee')),
                     ('BOX',(0,0),(-1,-1),0.5,colors.grey),
                     ('INNERGRID',(0,0),(-1,-1),0.5,colors.grey)))
    story.append(info)
    story.append(Spacer(1, 4*mm))

# ── 支払明細書（ZoomIn個別）────────────────────────────────
def make_zoomin_pdf(w, month_str, issuer, payment, out_dir):
    name        = w['name']
    reward_inc  = w['reward_inc']
    i1_inc      = w.get('i1_inc', 0)
    i2_inc      = w.get('i2_inc', 0)
    i2_count    = int(i2_inc / 100) if i2_inc > 0 else 0
    transport   = w.get('transport', 0)
    pc_inc      = w.get('pc_inc', 0)
    advance_inc = w.get('advance_inc', 0)
    subs        = w.get('sub', [])

    W = 170*mm
    doc = SimpleDocTemplate(str(out_dir / f'{month_str}_{name}_支払明細書.pdf'),
                            pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []
    doc_header(story, '支払明細書', issuer, payment,
               [['氏名', name], ['対象月', month_str + '月'], ['紹介G', 'ZoomIn']], W)

    story.append(section_bar('支給内訳', W))

    if not subs:
        # 通常1行
        reward_ex = fl(reward_inc / 1.1)
        i1_ex = fl(i1_inc / 1.1); i2_ex = fl(i2_inc / 1.1)
        pc_ex = fl(pc_inc / 1.1)
        total_inc = reward_inc + i1_inc + i2_inc + transport - pc_inc
        payout    = total_inc - 550 - advance_inc
        taxable   = total_inc - transport
        detail = [
            ('報酬（税抜）',           fmt(reward_ex),   False),
            ('稼働時間数',             str(w['hours']),  False),
            ('インセンティブ（税抜）',  fmt(i1_ex),       False),
            ('インセンティブ2（税抜）', fmt(i2_ex),       False),
            ('インセンティブ2件数',     str(i2_count),    False),
            ('交通費（非課税）',        fmt(transport),   False),
            ('PCレンタル（税抜）',      neg(pc_ex),       False),
            ('総計（税込）',            fmt(total_inc),   True),
            ('サポート料（税込）',      '(550)',          False),
            ('先払（税込）',            fmt(advance_inc), False),
            ('支給合計（税込）',        fmt(payout),      True),
        ]
    else:
        # 複数行（久保タイプ）
        total_inc = reward_inc
        all_rows = [(w['hours'], reward_inc)]
        for s in subs:
            total_inc += s['reward_inc']
            all_rows.append((s['hours'], s['reward_inc']))
        total_inc -= pc_inc
        payout  = total_inc - 550 - advance_inc
        taxable = total_inc - transport
        detail = []
        for i, (h, r) in enumerate(all_rows, 1):
            hourly = round(r / h) if h else 0
            detail.append((f'報酬{"①②③"[i-1]}（税抜）[時給{hourly:,}×{h}h]',
                           fmt(fl(r / 1.1)), False))
        pc_ex = fl(pc_inc / 1.1)
        detail += [
            ('交通費（非課税）',   fmt(transport),   False),
            ('PCレンタル（税抜）', neg(pc_ex),       False),
            ('総計（税込）',       fmt(total_inc),   True),
            ('サポート料（税込）', '(550)',          False),
            ('先払（税込）',       fmt(advance_inc), False),
            ('支給合計（税込）',   fmt(payout),      True),
        ]
        i2_inc = 0  # サブ行はインセン未対応（必要なら拡張）

    story.append(highlight_table(detail, [110*mm, 60*mm]))
    story.append(Spacer(1, 4*mm))

    tax_ex  = fl(taxable / 1.1)
    tax_amt = taxable - tax_ex
    story.append(section_bar(f'税額内訳　{fmt(taxable)}', W))
    story.append(highlight_table([
        ('課税対象額（税込）', fmt(taxable), False),
        ('税抜金額',           fmt(tax_ex),  False),
        ('消費税',             fmt(tax_amt), False),
    ], [110*mm, 60*mm]))
    story.append(Spacer(1, 4*mm))

    notes = []
    if i1_inc > 0: notes.append(f'インセン1 {fmt(i1_inc)}円')
    if i2_inc > 0: notes.append(f'インセン2 {fmt(i2_inc)}円（{i2_count}件）')
    if pc_inc > 0: notes.append(f'PCレンタル -{fmt(pc_inc)}円')
    if advance_inc > 0: notes.append(f'先払 -{fmt(advance_inc)}円')
    story.append(section_bar('備考', W))
    note_t = Table([[' / '.join(notes) or '　']], colWidths=[W])
    note_t.setStyle(cs(('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#bbbbbb'))))
    story.append(note_t)
    story.append(Spacer(1, 3*mm))
    story.append(p('※ 明細欄の課税項目は税抜表示です。交通費は非課税、サポート料と先払は総計（税込）算出後に控除しています。',
                   7, color=colors.HexColor('#888888')))
    doc.build(story)
    return payout

# ── 支払明細書（グループ一括）────────────────────────────
def worker_block(w, W):
    reward_inc  = w['reward_inc']
    pc_inc      = w.get('pc_inc', 0)
    advance_inc = w.get('advance_inc', 0)
    i1_inc      = w.get('i1_inc', 0)
    transport   = w.get('transport', 0)
    reward_ex   = fl(reward_inc / 1.1)
    i1_ex       = fl(i1_inc / 1.1)
    pc_ex       = fl(pc_inc / 1.1)
    total_inc   = reward_inc + i1_inc + transport - pc_inc
    subtotal    = total_inc - advance_inc

    rows = [[p(f'【{w["name"]}】  稼働{w["hours"]}h', 9, color=colors.HexColor('#222222')), '']]
    rows.append(['報酬（税抜）', fmt(reward_ex)])
    if i1_inc: rows.append(['インセンティブ（税抜）', fmt(i1_ex)])
    if transport: rows.append(['交通費（非課税）', fmt(transport)])
    if pc_inc:  rows.append(['PCレンタル（税抜）', neg(pc_ex)])
    if advance_inc: rows.append(['先払（税込）', fmt(advance_inc)])
    rows.append(['小計（税込）', fmt(subtotal)])

    n = len(rows)
    sty = [('FONTNAME',(0,0),(-1,-1),F),('FONTSIZE',(0,0),(-1,-1),8),
           ('ALIGN',(1,0),(1,-1),'RIGHT'),
           ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),
           ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#eeeeee')),
           ('SPAN',(0,0),(1,0)),
           ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ebebeb')),
           ('BACKGROUND',(0,n-1),(-1,n-1),colors.HexColor('#fff8cc')),
           ('FONTSIZE',(0,n-1),(-1,n-1),9),
           ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
           ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]
    t = Table(rows, colWidths=[110*mm, 60*mm])
    t.setStyle(TableStyle(sty))
    return t, subtotal, transport

def make_group_pdf(payee, group_name, workers_data, month_str, issuer, payment, out_dir):
    W = 170*mm
    doc = SimpleDocTemplate(str(out_dir / f'{month_str}_{payee}_支払明細書.pdf'),
                            pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []
    doc_header(story, '支払明細書', issuer, payment,
               [['支払先', payee], ['対象月', month_str + '月'], ['紹介G', group_name]], W)

    story.append(section_bar('各ワーカー明細', W))
    story.append(Spacer(1, 1.5*mm))

    grand_subtotal = 0
    grand_transport = 0
    for w in workers_data:
        tbl, subtotal, transport = worker_block(w, W)
        story.append(tbl)
        story.append(Spacer(1, 1.5*mm))
        grand_subtotal  += subtotal
        grand_transport += transport

    payout  = grand_subtotal - 550
    taxable = grand_subtotal - grand_transport
    tax_ex  = fl(taxable / 1.1)
    tax_amt = taxable - tax_ex

    story.append(Spacer(1, 2*mm))
    story.append(section_bar('合計', W))
    summary = [
        ('総計（税込）合計',   fmt(grand_subtotal), True),
        ('サポート料（税込）', '(550)',             False),
        ('支給合計（税込）',   fmt(payout),         True),
        ('課税対象額（税込）', fmt(taxable),        False),
        ('税抜金額',           fmt(tax_ex),         False),
        ('消費税',             fmt(tax_amt),        False),
    ]
    story.append(highlight_table(summary, [110*mm, 60*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(p('※ 課税項目は税抜表示。交通費は非課税、サポート料は一括550円（税込）控除。',
                   7, color=colors.HexColor('#888888')))
    doc.build(story)
    return payout

# ── 紹介料明細書 ─────────────────────────────────────────
def make_referral_pdf(referrer, items, month_str, issuer, payment, out_dir):
    W = 170*mm
    total   = sum(fee for _, _, _, fee in items)
    tax_ex  = fl(total / 1.1)
    tax_amt = total - tax_ex

    doc = SimpleDocTemplate(str(out_dir / f'{month_str}_{referrer}_紹介料明細書.pdf'),
                            pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []
    doc_header(story, '紹介料明細書', issuer, payment,
               [['宛名', referrer], ['対象月', month_str + '月']], W)

    story.append(section_bar('紹介料明細', W))
    hdr_row = [p('ワーカー',9,color=colors.white), p('稼働時間',9,1,color=colors.white),
               p('単価',9,2,color=colors.white), p('紹介料',9,2,color=colors.white)]
    detail_rows = [hdr_row] + [[name, f'{hours}h', f'¥{rate:,}', fmt(fee)]
                                for name, hours, rate, fee in items]
    sty = [('FONTNAME',(0,0),(-1,-1),F),('FONTSIZE',(0,0),(-1,-1),9),
           ('ALIGN',(1,0),(3,-1),'RIGHT'),('ALIGN',(1,0),(1,-1),'CENTER'),
           ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#bbbbbb')),
           ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#dddddd')),
           ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#333333')),
           ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
           ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]
    t = Table(detail_rows, colWidths=[85*mm, 25*mm, 25*mm, 35*mm])
    t.setStyle(TableStyle(sty))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    story.append(section_bar('合計・税額内訳', W))
    story.append(highlight_table([
        ('紹介料合計（税込）', fmt(total),   True),
        ('税抜金額',           fmt(tax_ex),  False),
        ('消費税',             fmt(tax_amt), False),
    ], [110*mm, 60*mm]))
    story.append(Spacer(1, 3*mm))
    story.append(p('※ 紹介料は税込金額で表示しています。', 7, color=colors.HexColor('#888888')))
    doc.build(story)
    return total

# ── メイン ───────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--year',    type=int)
    parser.add_argument('--month',   type=int)
    parser.add_argument('--issuer',  type=str)
    parser.add_argument('--payment', type=str)
    args = parser.parse_args()

    if args.year and args.month:
        year, month = args.year, args.month
    else:
        today = datetime.date.today()
        year, month = target_month(today)

    month_str = f'{year}{month:02d}'
    issuer  = datetime.date.fromisoformat(args.issuer)  if args.issuer  else issuer_date(year, month)
    payment = datetime.date.fromisoformat(args.payment) if args.payment else payment_date(year, month)

    print(f'対象月: {month_str}月　発行日: {issuer}　支払日: {payment}')

    service = get_drive_service()
    buf = download_spreadsheet(service)
    print(f'ファイル取得完了')

    workers, referrals = parse_month_sheet(buf, year, month)

    out_dir = OUTPUT_BASE / f'{month_str}_支払明細書'
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── ZoomIn 個別
    zoomin  = [w for w in workers if w['group'] == 'ZoomIn']
    skipped = []
    total_zoomin = 0
    for w in zoomin:
        payout = make_zoomin_pdf(w, month_str, issuer, payment, out_dir)
        total_zoomin += payout
        print(f'  ZoomIn: {w["name"]}  {payout:,}円')

    # ── グループ一括（畑野・前原）
    group_totals = {}
    for payee in set(GROUP_PAYEE.values()):
        group_workers = [w for w in workers if w.get('payee') == payee]
        if not group_workers:
            continue
        group_name = group_workers[0]['group']
        payout = make_group_pdf(payee, group_name, group_workers, month_str, issuer, payment, out_dir)
        group_totals[payee] = payout
        print(f'  {payee}: {payout:,}円 ({len(group_workers)}名)')

    # ── 紹介料
    total_referral = 0
    for referrer, items in sorted(referrals.items()):
        total = make_referral_pdf(referrer, items, month_str, issuer, payment, out_dir)
        total_referral += total
        print(f'  紹介料 {referrer}: {total:,}円 ({len(items)}件)')

    print(f'\n完了')
    print(f'  ZoomIn支給合計: {total_zoomin:,}円')
    for payee, amt in group_totals.items():
        print(f'  {payee}: {amt:,}円')
    print(f'  紹介料合計: {total_referral:,}円')
    print(f'保存先: {out_dir}')

if __name__ == '__main__':
    main()
