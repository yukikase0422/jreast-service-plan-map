# -*- coding: utf-8 -*-
"""2ページ目：運転計画の一覧と注記（2026年9月26日以降）。

  python scripts/render_list_20260926.py [出力先]

文中の「路線名＋区間」の背後に路線カラーの背景を敷き、文字色は背景とのコントラスト比が
高い方（黒／白）を採る。既定では
output/JR東日本_運転計画_2026-09-26_ストーリー用_2一覧.png を書き出す。
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontsel import F, FAMILY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'output')
if not os.path.isdir(os.path.join(ROOT, 'data')):
    OUTDIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-26_ストーリー用_2一覧.png')

W, H = 1080, 1920
SAFE_TOP, SAFE_BOT = 280, 1580
LM, RM = 44, 44

BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30); BLUE=(20,110,210); GREY=(110,110,110)
INK=(20,20,20)

# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる。
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
LC = {
 '内房線':hx('#00B2E5'), '外房線':hx('#DB4028'), '総武本線':hx('#FFC20D'), '成田線':hx('#00B261'),
 '鹿島線':hx('#C56E2E'), '東金線':hx('#F15A22'), '久留里線':hx('#00B5AD'), '京葉線':hx('#C9252F'),
}
NAMES = sorted(LC, key=len, reverse=True)

def rel_lum(c):
    def ch(v):
        v=v/255; return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*ch(c[0])+0.7152*ch(c[1])+0.0722*ch(c[2])
def text_on(c):
    # WCAG 2.1 のコントラスト比で、黒(#141414)と白のうち高い方を採る
    L=rel_lum(c); return (255,255,255) if 1.05/(L+0.05) > (L+0.05)/0.05 else INK

BODY = F('Medium', 26); HEAD = F('Bold', 31)
LH = 34

img = Image.new('RGB', (W,H), 'white'); d = ImageDraw.Draw(img)

def rich(x, y, text, font):
    """【…】で囲んだ範囲の背後に路線カラーを敷く。文字送りは囲みのない場合と同一。"""
    i = 0; last = GREY
    while i < len(text):
        if text[i] == '【':
            j = text.index('】', i); span = text[i+1:j]
            name = next((n for n in NAMES if span.startswith(n)), None)
            col = LC[name] if name else last; last = col
            bb = font.getbbox(span, anchor='lm')
            d.rounded_rectangle([x+bb[0]-4, y+bb[1]-3, x+bb[2]+4, y+bb[3]+3], radius=4, fill=col)
            d.text((x, y), span, font=font, fill=text_on(col), anchor='lm')
            x += font.getlength(span); i = j + 1
        else:
            j = text.find('【', i); j = len(text) if j < 0 else j
            seg = text[i:j]
            d.text((x, y), seg, font=font, fill=INK, anchor='lm')
            x += font.getlength(seg); i = j
    return x

SECTIONS = [
 (BLACK, '運転取りやめ（長期）', [
   '【内房線 姉ケ崎〜木更津】 復旧まで少なくとも3か月程度（9月23日起点）',
   '【総武本線 榎戸〜成東】 復旧まで1か月程度（9月23日起点）',
   '【久留里線 久留里〜上総亀山】 運転再開の見込みは立っていない',
 ]),
 (PURPLE, '運転取りやめ（10月初めの運転再開を目指す）', [
   '【久留里線 木更津〜久留里】 10月3日の運転再開を目指す',
   '【成田線 佐原〜銚子】 10月4日の運転再開を目指す',
 ]),
 (BLUE, '26日始発から運転再開', [
   '【内房線 木更津〜安房鴨川】 運転本数の割合は示されていない',
   '※発表文は、運転する線区でも列車本数を大幅に減らす予定としている',
 ]),
 (RED, '本数を減らして運転（バス等の代行輸送はなし）', [
   '【内房線 千葉〜姉ケ崎】 朝夕は通常の3割程度（時刻表は同社サイト）',
   '　※給電の制約による。通常の本数に戻るのは姉ケ崎〜木更津の復旧時の見込み',
   '【総武本線 千葉〜榎戸】 通常の6割程度',
   '【総武本線 成東〜銚子】 25日夜時点で通常の6割程度（計画に記載なし）',
   '【成田線 成田〜佐原】 通常の8割程度',
 ]),
 (GREY, '特急・快速', [
   '【内房線 さざなみ】 運転取りやめ（姉ケ崎〜木更津の復旧後に再開）',
   '【総武本線 しおさい】 4・6・11号のみ運転（全列車の再開は榎戸〜成東の復旧後）',
   '【内房線 快速「B.B.BASE館山」】 26日は上下とも全区間で運休',
 ]),
 (GREY, 'バス等による代行輸送（28日の開始を目指す）', [
   '【久留里線 木更津〜上総亀山】・【成田線 佐原〜銚子】',
   '【総武本線 榎戸〜成東】・【内房線 姉ケ崎〜木更津】',
   '時刻・本数は27日（日）夕方までに知らせたいとの説明。輸送力不足の可能性',
   '【内房線 長浦〜木更津】は鉄道による輸送も検討中（見通しは未定）',
 ]),
]
# (フォント, 行送り, 文言)。ストーリーの縮小表示でも読めるよう、注記も本文と同じ大きさにする
NOTES = [
 (BODY, 34, '再開日・復旧見込みは今後変わる可能性があります。最新情報は同社サイトで確認を'),
 (BODY, 34, '外房線・東金線・鹿島線・京葉線などは計画に記載がなく、25日夜は平常運転。'),
 (BODY, 34, '出典：JR東日本千葉事業本部「台風25号の影響による9月26日（土）以降の'),
 (BODY, 34, '　千葉県内各線区の運行計画について」（9月25日14時発表）、同社運行情報'),
 (BODY, 34, '　（25日21時30分時点）、同本部長の会見（25日）、Yahoo!路線情報。'),
]

d.text((W//2, 322), '9/26(土)以降 JR東日本 運転計画', font=F('DeBold',58), fill=INK, anchor='mm')
d.text((W//2, 375), '一覧と注記（千葉県内）　※地図は前ページ', font=F('Medium',30), fill=(60,60,60), anchor='mm')

y = 425
over = []
for color, head, lines in SECTIONS:
    a=Image.new('L',(120,60),0); ImageDraw.Draw(a).line([(24,30),(96,30)], fill=150, width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); img.paste(color,(LM-24,y-30,LM+96,y+30),a); d=ImageDraw.Draw(img)
    if color==GREY: d.line([(LM,y),(LM+72,y)], fill=GREY, width=6)
    else: d.line([(LM,y),(LM+72,y)], fill=color, width=14)
    d.text((LM+92, y), head, font=HEAD, fill=INK, anchor='lm')
    if LM+92+HEAD.getlength(head) > W-RM: over.append((int(LM+92+HEAD.getlength(head)), head[:12]))
    y += 42
    for t in lines:
        xe = rich(LM+24, y, t, BODY)
        if xe > W-RM: over.append((int(xe), t[:12]))
        y += LH
    y += 10

d.line([(LM, y), (W-RM, y)], fill=(180,180,180), width=2); y += 26
for font, lh, t in NOTES:
    xe = rich(LM, y, t, font)
    if xe > W-RM: over.append((int(xe), t[:12]))
    y += lh

print('last y', y, 'limit', SAFE_BOT, 'overflow', over)
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
print('font:', FAMILY)
img.save(out)
print('saved:', out)
