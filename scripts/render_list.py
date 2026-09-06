# -*- coding: utf-8 -*-
"""2ページ目：運転計画の一覧と注記。

  python scripts/render_list.py [出力先]

文中の「路線名＋区間」の背後に路線カラーの背景を敷き、文字色は背景とのコントラスト比が
高い方（黒／白）を採る。既定では
output/JR東日本_運転計画_2026-09-07_ストーリー用_2一覧.png を書き出す。
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontsel import F, FAMILY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'output')
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-07_ストーリー用_2一覧.png')

W, H = 1080, 1920
SAFE_TOP, SAFE_BOT = 280, 1580
LM, RM = 44, 44

BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30); YELLOW=(255,200,0); GREY=(110,110,110)
INK=(20,20,20)

# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる。
# 水郡線・水戸線は同表に色の記載がなく灰色とした。宇都宮線・高崎線（JU）は東海道線（JT）と同じオレンジ。
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
LC = {
 '内房線':hx('#00B2E5'), '外房線':hx('#DB4028'), '総武本線':hx('#FFC20D'), '成田線':hx('#00B261'),
 '鹿島線':hx('#C56E2E'), '東金線':hx('#F15A22'), '久留里線':hx('#00B5AD'),
 '湘南新宿ライン':hx('#E31F26'), '相鉄線直通':hx('#00AC9A'), '上野東京ライン':hx('#91278F'),
 '山手線':hx('#9ACD32'), '京浜東北線':hx('#00B2E5'), '東海道線':hx('#F68B1E'), '横須賀線':hx('#0067C0'),
 '総武快速線':hx('#0067C0'), '中央線快速':hx('#F15A22'), '中央総武各駅停車':hx('#FFD400'),
 '宇都宮線':hx('#F68B1E'), '高崎線':hx('#F68B1E'), '埼京線':hx('#00AC9A'), '川越線':hx('#00AC9A'),
 '武蔵野線':hx('#F15A22'), '京葉線':hx('#C9252F'), '南武線':hx('#FFD400'), '横浜線':hx('#80C342'),
 '相模線':hx('#009793'), '鶴見線':hx('#FFD400'),
 '常磐線':hx('#3333FF'), '常磐線快速電車':hx('#00B261'), '常磐線各駅停車':hx('#00B261'),
 '中央本線':hx('#0074BE'), '青梅線':hx('#F15A22'), '八高線':hx('#B4AA96'), '伊東線':hx('#F68B1E'),
 '烏山線':hx('#339966'), '吾妻線':hx('#0F5474'), '小海線':hx('#41934C'),
 '水郡線':(128,128,128), '水戸線':(128,128,128),
}
NAMES = sorted(LC, key=len, reverse=True)

def rel_lum(c):
    def ch(v):
        v=v/255; return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*ch(c[0])+0.7152*ch(c[1])+0.0722*ch(c[2])
def text_on(c):
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
 (BLACK, '6日夜から運転取りやめ（7日夕方頃まで見合わせ）', [
   '【内房線 君津〜安房鴨川】（6日20時頃〜）',
   '【外房線 誉田〜安房鴨川】（6日21時頃〜）',
 ]),
 (PURPLE, '7日始発から運転見合わせ', [
   '【総武本線 佐倉〜銚子】／【東金線 全線】／【鹿島線 佐原〜鹿島神宮】（夕方頃まで）',
   '【成田線 成田〜銚子・成田〜我孫子】（夕方頃まで）',
   '【久留里線 木更津〜久留里】（夕方頃まで）・【久留里〜上総亀山】（終日）',
   '【湘南新宿ライン】（〜17時頃）、【相鉄線直通 新宿〜羽沢横浜国大】（〜15時頃）',
 ]),
 (RED, '運転本数を減らして運転（7日）', [
   '【外房線 千葉〜誉田】（6日21時以降・7日とも大幅減便）',
   '【山手線】・【京浜東北線】・【東海道線 東京〜小田原】・【横須賀線】・【総武快速線】',
   '【中央線快速】・【中央総武各駅停車】・【宇都宮線】・【高崎線】・【埼京線】・【川越線】',
   '【武蔵野線】・【京葉線】・【常磐線】（快速電車を含む）・【南武線】・【横浜線】',
 ]),
 (YELLOW, '予告のみ（6日夜〜7日 遅れ・運休の可能性）', [
   '【上野東京ライン】・【常磐線各駅停車】・【相模線】・【鶴見線】ほか首都圏各線区',
 ]),
 (GREY, '地図の範囲外（7日）', [
   '終日見合わせ：【常磐線 日立〜仙台】、【水郡線】、【水戸線 小山〜友部】、【烏山線】、',
   '　【青梅線 青梅〜奥多摩】、【八高線 寄居〜高麗川】、【吾妻線 長野原草津口〜大前】、',
   '　【小海線 小淵沢〜中込】　／　減便：【常磐線 水戸〜日立】',
   '時間帯見合わせ：【東海道線 小田原〜熱海】（〜19時頃）、',
   '　【中央本線 高尾〜富士見】（〜18時頃）、【伊東線】（6日20時頃〜7日夕方）',
 ]),
 (GREY, '特急・寝台', [
   'しおさい 始発〜昼頃まで運休　／　サンライズ瀬戸・出雲 6日発 全区間運休',
 ]),
]
NOTES = [
 '減便線区は駅構内の混雑が見込まれるため、来駅を控えるよう呼びかけられています。',
 '見合わせ区間は天候回復・点検終了後に再開。いずれもバス等の代行輸送はありません。',
 'えきねっと購入の対象特急券（9/6・7乗車分）は払戻手数料無料（えきねっとQ&A）。',
 '出典：JR東日本 運行情報（9月6日22時17分現在）。最新情報は同社サイトで要確認。',
]

d.text((W//2, 322), '9/7(月) JR東日本 運転計画', font=F('DeBold',58), fill=INK, anchor='mm')
d.text((W//2, 375), '一覧と注記（千葉・東京・茨城南部ほか）　※地図は前ページ', font=F('Medium',30), fill=(60,60,60), anchor='mm')

y = 425
over = []
for color, head, lines in SECTIONS:
    a=Image.new('L',(120,60),0); ImageDraw.Draw(a).line([(24,30),(96,30)], fill=(150 if color!=YELLOW else 190), width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); img.paste(color,(LM-24,y-30,LM+96,y+30),a); d=ImageDraw.Draw(img)
    if color==YELLOW: d.line([(LM,y),(LM+72,y)], fill=(0,178,229), width=5)
    elif color==GREY: d.line([(LM,y),(LM+72,y)], fill=GREY, width=6)
    else: d.line([(LM,y),(LM+72,y)], fill=color, width=14)
    d.text((LM+92, y), head, font=HEAD, fill=INK, anchor='lm')
    y += 42
    for t in lines:
        xe = rich(LM+24, y, t, BODY)
        if xe > W-RM: over.append((int(xe), t[:10]))
        y += LH
    y += 12

d.line([(LM, y), (W-RM, y)], fill=(180,180,180), width=2); y += 26
for t in NOTES:
    xe = rich(LM, y, t, SMALL)
    if xe > W-RM: over.append((int(xe), t[:10]))
    y += 32

print('last y', y, 'limit', SAFE_BOT, 'overflow', [(w, t.encode('unicode_escape')) for w, t in over])
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
print('font:', FAMILY)
img.save(out)
print('saved:', out)
