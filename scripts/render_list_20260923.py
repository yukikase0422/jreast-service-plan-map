# -*- coding: utf-8 -*-
"""2ページ目：運転計画の一覧と注記（2026年9月23日）。

  python scripts/render_list_20260923.py [出力先]

文中の「路線名＋区間」の背後に路線カラーの背景を敷き、文字色は背景とのコントラスト比が
高い方（黒／白）を採る。既定では
output/JR東日本_運転計画_2026-09-23_ストーリー用_2一覧.png を書き出す。
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontsel import F, FAMILY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'output')
if not os.path.isdir(os.path.join(ROOT, 'data')):
    OUTDIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-23_ストーリー用_2一覧.png')

W, H = 1080, 1920
SAFE_TOP, SAFE_BOT = 280, 1580
LM, RM = 44, 44

BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30); GREY=(110,110,110)
INK=(20,20,20)

# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる。
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
LC = {
 '内房線':hx('#00B2E5'), '外房線':hx('#DB4028'), '総武本線':hx('#FFC20D'), '成田線':hx('#00B261'),
 '鹿島線':hx('#C56E2E'), '東金線':hx('#F15A22'), '久留里線':hx('#00B5AD'),
 '総武快速線':hx('#0067C0'), '京葉線':hx('#C9252F'), '常磐線快速電車':hx('#00B261'),
 '成田エクスプレス':hx('#0067C0'),
}
NAMES = sorted(LC, key=len, reverse=True)

def rel_lum(c):
    def ch(v):
        v=v/255; return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*ch(c[0])+0.7152*ch(c[1])+0.0722*ch(c[2])
def text_on(c):
    # WCAG 2.1 のコントラスト比で、黒(#141414)と白のうち高い方を採る
    L=rel_lum(c); return (255,255,255) if 1.05/(L+0.05) > (L+0.05)/0.05 else INK

BODY = F('Medium', 26); HEAD = F('Bold', 31); SMALL = F('Regular', 24)
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
 (BLACK, '23日 終日運転取りやめ（24日以降も当面取りやめ見込み）', [
   '【内房線 姉ケ崎〜木更津】・【総武本線 佐倉〜成東】・【成田線 佐原〜銚子】',
   '【久留里線 木更津〜上総亀山（全線）】　※被害が甚大なため',
 ]),
 (PURPLE, '23日 終日運転取りやめ（一部を除き再開見通しは今後発表）', [
   '【内房線 木更津〜安房鴨川】・【外房線 誉田〜安房鴨川】・【成田線 新木〜木下】',
   '【外房線 千葉〜誉田】（復旧作業が難航し、24日始発からの再開見込み）',
 ]),
 (RED, '23日始発から運転再開・本数を減らして運転', [
   '【内房線 千葉〜姉ケ崎】・【総武本線 千葉〜佐倉】・【総武本線 成東〜銚子】',
   '【成田線 佐倉〜成田〜成田空港】・【成田線 成田〜佐原】',
   '【成田線 成田〜木下】・【成田線 新木〜我孫子】',
   '【鹿島線 佐原〜鹿島神宮】・【東金線 大網〜成東（全線）】',
 ]),
 (GREY, '特急（23日）', [
   '終日運転取りやめ：【内房線 さざなみ】・【外房線 わかしお】・【総武本線 しおさい】',
   '【成田エクスプレス】は平常どおり運転の予定',
 ]),
 (GREY, '主な被害箇所（JR東日本発表の参考情報）', [
   '【総武本線 物井〜佐倉】 線路冠水　【内房線 大貫〜佐貫町】 土砂流入',
   '【成田線 香取〜水郷】 土砂流入　【久留里線 祇園〜上総清川】 土砂流入',
 ]),
 (GREY, '9月22日の状況（18時31分現在）', [
   '千葉県内の上記各線は終日運転見合わせ中（振替輸送あり）。',
   '【京葉線】 新習志野〜蘇我の下り一部列車が運休。',
   '【常磐線快速電車】 の成田線への直通運転は本日中止。',
 ]),
]
NOTES = [
 '運転見合わせ区間にバス代行輸送はありません。',
 '運転再開の見通しは、分かり次第JR東日本から改めて発表されます。',
 '上記以外の線区（東京都内・茨城県内など）は千葉事業本部の発表の対象外で、',
 '　JR東日本 運行情報にも23日の計画の掲載はありません（22日18時54分現在）。',
 '出典：JR東日本千葉事業本部「台風25号の影響による9月23日（水・祝）の',
 '　列車の運行について」（9月22日17時40分発表）ほかJR東日本 運行情報。',
 '　最新情報は同社サイトで要確認。',
]

d.text((W//2, 322), '9/23(水・祝) JR東日本 運転計画', font=F('DeBold',58), fill=INK, anchor='mm')
d.text((W//2, 375), '一覧と注記（千葉県内）　※地図は前ページ', font=F('Medium',30), fill=(60,60,60), anchor='mm')

y = 425
over = []
for color, head, lines in SECTIONS:
    a=Image.new('L',(120,60),0); ImageDraw.Draw(a).line([(24,30),(96,30)], fill=150, width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); img.paste(color,(LM-24,y-30,LM+96,y+30),a); d=ImageDraw.Draw(img)
    if color==GREY: d.line([(LM,y),(LM+72,y)], fill=GREY, width=6)
    else: d.line([(LM,y),(LM+72,y)], fill=color, width=14)
    d.text((LM+92, y), head, font=HEAD, fill=INK, anchor='lm')
    y += 42
    for t in lines:
        xe = rich(LM+24, y, t, BODY)
        if xe > W-RM: over.append((int(xe), t[:12]))
        y += LH
    y += 12

d.line([(LM, y), (W-RM, y)], fill=(180,180,180), width=2); y += 26
for t in NOTES:
    xe = rich(LM, y, t, SMALL)
    if xe > W-RM: over.append((int(xe), t[:12]))
    y += 32

print('last y', y, 'limit', SAFE_BOT, 'overflow', over)
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
print('font:', FAMILY)
img.save(out)
print('saved:', out)
