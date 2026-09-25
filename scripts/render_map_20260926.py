# -*- coding: utf-8 -*-
"""1ページ目：運転計画の地図（2026年9月26日以降）。

  python scripts/render_map_20260926.py [出力先]

data/land.json・data/st.json を読み、既定では
output/JR東日本_運転計画_2026-09-26_ストーリー用_1地図.png を書き出す。
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, LineString
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontsel import F, FAMILY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUTDIR = os.path.join(ROOT, 'output')
if not os.path.exists(os.path.join(DATA, 'st.json')):   # 作業用の平置き配置
    DATA = os.path.dirname(os.path.abspath(__file__)); OUTDIR = DATA
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-26_ストーリー用_1地図.png')

W, H = 1080, 1920
MAP_TOP, MAP_BOT = 400, 1575
MH = MAP_BOT - MAP_TOP
LON0, LON1 = 139.53, 140.93
LAT1 = 36.09
KM_LON = 111.32*math.cos(math.radians(35.5))
PXKM = W/((LON1-LON0)*KM_LON)
LAT0 = LAT1 - MH/(PXKM*111.32)
def P(lon, lat):
    return ((lon-LON0)*KM_LON*PXKM, MAP_TOP+(LAT1-lat)*111.32*PXKM)


st = json.load(open(os.path.join(DATA, 'st.json'), encoding='utf-8'))
def S(n):
    if n in st: return (st[n][0], st[n][1])
    raise KeyError('station not in st.json: ' + n)

SEA=(205,228,240); LAND=(243,240,232); COAST=(150,180,200)
BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30); BLUE=(20,110,210)
# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
C = {'yamanote':hx('#9ACD32'),'keihin':hx('#00B2E5'),'tokaido':hx('#F68B1E'),'yokosuka':hx('#0067C0'),
     'sobu_local':hx('#FFD400'),'chuo':hx('#F15A22'),'utsunomiya':hx('#F68B1E'),'saikyo':hx('#00AC9A'),
     'joban':hx('#00B261'),'joban_local':hx('#00B261'),'musashino':hx('#F15A22'),'keiyo':hx('#C9252F'),
     'sobu_main':hx('#FFC20D'),'narita':hx('#00B261'),'uchibo':hx('#00B2E5'),'sotobo':hx('#DB4028'),
     'shonan':hx('#E31F26'),'sotetsu':hx('#00AC9A'),'kashima':hx('#C56E2E'),'togane':hx('#F15A22'),'kururi':hx('#00B5AD')}
GAP = 11.0
THIN, THICK = 6, 12
# 細線（計画の対象外）は路線カラーを白へ 35% 寄せて淡くし、状態のある太線と見分けやすくする
# （外房線・東金線・京葉線の路線カラーは赤系で、減便の赤と紛れやすい）
def fade(c, t=0.35): return tuple(round(v + (255 - v)*t) for v in c)

# (色キー, 駅列, 並走オフセット段数, 太さ, 状態)
#   状態: None=計画の対象外（平常運転）。状態のある区間は下の各リストに置く
LINES = [
 ('yamanote', ['東京','品川','大崎','渋谷','新宿','池袋','田端','上野','東京'], 0, THIN, None),
 ('keihin',   ['大宮','南浦和','赤羽','田端','上野','東京','品川','川崎','横浜'], 1, THIN, None),
 ('utsunomiya',['大宮','赤羽','上野'], 2, THIN, None),
 ('tokaido',  ['東京','品川','川崎','横浜','大船'], 2, THIN, None),
 ('yokosuka', ['東京','品川','武蔵小杉','横浜','大船'], -1, THIN, None),
 ('saikyo',   ['大崎','渋谷','新宿','池袋','赤羽','武蔵浦和','大宮'], 1, THIN, None),
 ('shonan',   ['大宮','赤羽','池袋','新宿','渋谷','大崎','武蔵小杉','横浜','大船'], -2, THIN, None),
 ('sotetsu',  ['新宿','渋谷','大崎','武蔵小杉','羽沢横浜国大'], -3, THIN, None),
 ('yokosuka', ['東京','錦糸町','船橋','津田沼','千葉'], 1, THIN, None),
 ('sobu_local',['御茶ノ水','秋葉原','錦糸町','船橋','津田沼','千葉'], -1, THIN, None),
 ('chuo',     ['東京','御茶ノ水','新宿','三鷹'], 1, THIN, None),
 ('sobu_local',['御茶ノ水','新宿','三鷹'], -1, THIN, None),
 ('joban',    ['上野','北千住','松戸','柏','我孫子','取手','土浦'], 0, THIN, None),
 ('joban_local',['北千住','松戸','柏','我孫子','取手'], 1, THIN, None),
 ('musashino',['北朝霞','武蔵浦和','南浦和','南越谷','新松戸','西船橋'], 0, THIN, None),
 ('keiyo',    ['東京','新木場','舞浜','南船橋','海浜幕張','千葉みなと','蘇我'], 0, THIN, None),
 # 千葉県内で計画の対象外の線区（25日夜は平常運転）
 ('sotobo',   ['千葉','蘇我','鎌取','誉田','土気','大網','茂原','上総一ノ宮','大原','勝浦','安房小湊','安房鴨川'], 0, THIN, None),
 ('togane',   ['大網','東金','成東'], 0, THIN, None),
 ('narita',   ['佐倉','酒々井','成田','成田空港'], 0, THIN, None),
 ('narita',   ['成田','安食','木下','布佐','新木','我孫子'], 0, THIN, None),
 ('kashima',  ['佐原','香取','潮来','鹿島神宮'], 0, THIN, None),
]
# 26日以降も運転取りやめ・長期（復旧まで1か月以上、または見込みなし）
BLACK_LINES = [
 ['姉ケ崎','袖ケ浦','木更津'],
 ['榎戸','八街','成東'],
 ['久留里','上総亀山'],
]
# 26日以降も運転取りやめ・10月初めの再開を目指す
PURPLE_LINES = [
 ['木更津','久留里'],
 ['佐原','小見川','笹川','松岸'],
]
# 26日始発から運転再開
BLUE_LINES = [
 ['木更津','君津','上総湊','浜金谷','館山','千倉','和田浦','安房鴨川'],
]
# 本数を減らして運転
RED_LINES = [
 ['千葉','四街道','佐倉','榎戸'],
 ['成東','横芝','八日市場','旭','松岸','銚子'],
 ['成田','滑河','佐原'],
]

LB = {
 '東京':('lm',16,10,0),'新宿':('rm',-16,0,0),'池袋':('mb',-10,-14,0),'上野':('lm',14,-14,0),'品川':('rm',-16,6,0),
 '横浜':('lm',16,14,0),'大宮':('lm',18,0,0),'船橋':('mb',0,-16,0),
 '千葉':('rm',-14,-14,1),'大網':('lm',14,0,0),'茂原':('lm',14,0,0),
 '大原':('rm',-14,0,0),'勝浦':('mt',0,14,0),'安房鴨川':('mt',0,14,1),'館山':('rm',-14,0,0),
 '姉ケ崎':('lt',10,9,1),'木更津':('rm',-14,0,1),'久留里':('lm',14,0,1),'上総亀山':('lm',14,4,1),
 '佐倉':('mb',0,-12,0),'榎戸':('lb',8,-10,1),'成田':('lm',21,-20,1),'成田空港':('lm',12,12,0),'成東':('lm',14,0,1),
 '旭':('mb',0,-12,0),'銚子':('mt',0,14,1),'佐原':('mb',-6,-12,1),
 '鹿島神宮':('lm',14,0,0),'我孫子':('mb',-6,-18,0),'柏':('rm',-14,8,0),'松戸':('lm',14,0,0),
}

# 区間ごとの見込み・運転本数の札 (文字列の行, 色, 基準点, 基準点が札のどこに当たるか)
TAGS = [
 (['朝夕3割程度'], RED, (408, 922), 'rm'),        # 内房線 千葉〜姉ケ崎
 (['6割程度'], RED, (503, 795), 'mm'),            # 総武本線 千葉〜榎戸（周囲が混むため線の上に置く）
 (['6割程度', '25日夜時点'], RED, (785, 794), 'lt'),  # 総武本線 成東〜銚子（計画に記載がなく、運行情報による）
 (['8割程度'], RED, (610, 626), 'rb'),            # 成田線 成田〜佐原（成田〜滑河の西側）
 (['少なくとも', '3か月程度'], BLACK, (306, 1008), 'rm'),  # 内房線 姉ケ崎〜木更津
 (['約1か月'], BLACK, (579, 846), 'mt'),          # 総武本線 榎戸〜成東（線の南側。蘇我の駅名は置かない）
 (['再開の見込み立たず'], BLACK, (432, 1244), 'mt'),  # 久留里線 久留里〜上総亀山
 (['10/3再開目標'], PURPLE, (372, 1098), 'lb'),   # 久留里線 木更津〜久留里
 (['10/4再開目標'], PURPLE, (812, 580), 'lm'),    # 成田線 佐原〜銚子
 (['26日始発から', '運転再開'], BLUE, (250, 1170), 'rm'),  # 内房線 木更津〜安房鴨川
]

# ---------- 陸地 ----------
lay = Image.new('RGB',(W,H),SEA); ld = ImageDraw.Draw(lay)
land = shape(json.load(open(os.path.join(DATA, 'land.json'), encoding='utf-8')))
for p in (land.geoms if land.geom_type=='MultiPolygon' else [land]):
    ld.polygon([P(*c) for c in p.exterior.coords], fill=LAND)
    for r in p.interiors:
        ld.polygon([P(*c) for c in r.coords], fill=SEA)
a=np.array(lay)
land_mask = np.all(a==np.array(LAND,dtype=np.uint8),axis=2)
er=land_mask.copy()
for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)):
    er &= np.roll(np.roll(land_mask,dy,0),dx,1)
edge = land_mask & ~er
edge |= np.roll(edge,1,0) | np.roll(edge,1,1)
a[edge]=np.array(COAST,dtype=np.uint8)
lay=Image.fromarray(a); ld=ImageDraw.Draw(lay)
bad=[n for n,v in st.items() if 0<=P(v[0],v[1])[0]<W and MAP_TOP<=P(v[0],v[1])[1]<MAP_BOT and lay.getpixel((int(P(v[0],v[1])[0]),int(P(v[0],v[1])[1])))==SEA]
print('stations on sea:', bad)

def halo_text(im, xy, text, font, anchor, fill, pad=5, close=9):
    """文字の外側 pad px を白で縁取り、字の内側の空間（幅 2*(pad+close) px 未満）も白で埋める。"""
    bb = font.getbbox(text, anchor=anchor)
    m = pad + close + 4
    w = bb[2] - bb[0] + 2*m; h = bb[3] - bb[1] + 2*m
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((m - bb[0], m - bb[1]), text, font=font, fill=255, anchor=anchor)
    halo = mask.filter(ImageFilter.MaxFilter(2*(pad+close)+1)).filter(ImageFilter.MinFilter(2*close+1))
    ox, oy = int(round(xy[0] + bb[0] - m)), int(round(xy[1] + bb[1] - m))
    im.paste((255, 255, 255), (ox, oy, ox + w, oy + h), halo)
    ImageDraw.Draw(im).text(xy, text, font=font, fill=fill, anchor=anchor)

F_TAG = F('Bold', 24)
TAG_LH, TAG_PX, TAG_PY = 30, 9, 5
def tag_box(lines, xy, anchor):
    w = max(F_TAG.getlength(t) for t in lines) + 2*TAG_PX
    h = TAG_LH*len(lines) + 2*TAG_PY
    x, y = xy
    x0 = {'l': x, 'm': x - w/2, 'r': x - w}[anchor[0]]
    y0 = {'t': y, 'm': y - h/2, 'b': y - h}[anchor[1]]
    return (x0, y0, x0 + w, y0 + h)
def draw_tag(im, lines, color, xy, anchor):
    """状態色の地に白抜き文字の札。白の縁で線・陸地から切り離す。"""
    x0, y0, x1, y1 = tag_box(lines, xy, anchor)
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([x0-3, y0-3, x1+3, y1+3], radius=11, fill='white')
    dd.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=color)
    for i, t in enumerate(lines):
        dd.text(((x0+x1)/2, y0 + TAG_PY + TAG_LH*i + TAG_LH/2), t, font=F_TAG, fill='white', anchor='mm')

# ---------- 線 ----------
def raw_pts(names):
    return [P(*S(n)) for n in names]
def offset_pts(names, k):
    pts=raw_pts(names)
    if k==0: return [pts]
    oc=LineString(pts).offset_curve(k*GAP, join_style='round')
    geoms = list(oc.geoms) if oc.geom_type=='MultiLineString' else [oc]
    return [list(g.coords) for g in geoms if len(g.coords)>=2]
def uchibo_pts():
    """内房線（赤）千葉〜姉ケ崎。千葉〜蘇我は外房線（細線）と同じ線路を走るため、
    線の幅より広い 36px だけ西側（東京湾側）へ並べ、蘇我から五井へ向かう間で本来の位置へ戻す。"""
    a, b = raw_pts(['千葉'])[0], raw_pts(['蘇我'])[0]
    dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
    nx, ny = -dy/L*36, dx/L*36
    return [(a[0]+nx, a[1]+ny), (b[0]+nx, b[1]+ny)] + raw_pts(['五井','姉ケ崎'])
RED_EXTRA = [uchibo_pts()]

def draw_glow(groups, color, alpha, width, blur):
    # 色は固定し、透明度だけをぼかす（RGBA ごとぼかすと透明部の黒が混ざり黒ずむ）
    a = Image.new('L',(W,H),0); ad=ImageDraw.Draw(a)
    for pts in groups:
        ad.line(pts, fill=alpha, width=width, joint='curve')
    a = a.filter(ImageFilter.GaussianBlur(blur))
    lay.paste(color, (0,0,W,H), a)

# 状態のある区間には各色の帯を敷く。計画の対象外の線区（細線）には帯を敷かない
draw_glow([raw_pts(n) for n in BLUE_LINES], BLUE, 150, 44, 12)
draw_glow([raw_pts(n) for n in RED_LINES] + RED_EXTRA, RED, 150, 44, 12)
draw_glow([raw_pts(n) for n in PURPLE_LINES], PURPLE, 170, 48, 12)
draw_glow([raw_pts(n) for n in BLACK_LINES], BLACK, 150, 48, 12)
ld = ImageDraw.Draw(lay)

# 重なる箇所は状態の重大な順（黒＞紫＞赤＞青＞細線）に上へ来るよう、重大度順に描く
segs=[]
for key,names,k,w,s in LINES:
    for pts in offset_pts(names,k): segs.append((0,fade(C[key]),w,pts))
for L in BLUE_LINES:   segs.append((1,BLUE,THICK,raw_pts(L)))
for L in RED_LINES:    segs.append((2,RED,THICK,raw_pts(L)))
for pts in RED_EXTRA:  segs.append((2,RED,THICK,pts))
for L in PURPLE_LINES: segs.append((3,PURPLE,THICK,raw_pts(L)))
for L in BLACK_LINES:  segs.append((4,BLACK,THICK,raw_pts(L)))
segs.sort(key=lambda t:t[0])
for sev,col,w,pts in segs:
    ld.line(pts, fill='white', width=w+4, joint='curve')
    ld.line(pts, fill=col, width=w, joint='curve')

tx,ty = raw_pts(['取手'])[0]
halo_text(lay, (tx+40, MAP_TOP+34), '↑水戸方面', F('Medium',24), 'lm', (30,30,30), pad=4)
# 外房線・東金線の路線カラーは赤系で、減便（赤）と紛れやすいため文字で補う
f_note = F('Medium',24); NOTE_XY = (682, 1044); NOTE_LH = 30; NOTE_TXT = ['外房線・東金線は計画に記載なし', '（25日夜は平常運転）']
for i, t in enumerate(NOTE_TXT):
    halo_text(lay, (NOTE_XY[0], NOTE_XY[1]+NOTE_LH*i), t, f_note, 'lm', (60,60,60), pad=4)

f_lab=F('Medium',30); f_labB=F('Bold',32)
for n,(anc,dx,dy,em) in LB.items():
    x,y=P(*S(n)); r=10 if em else 8
    ld.ellipse([x-r,y-r,x+r,y+r], fill='white', outline=(30,30,30), width=3 if em else 2)
for n,(anc,dx,dy,em) in LB.items():
    x,y=P(*S(n))
    halo_text(lay, (x+dx,y+dy), n, f_labB if em else f_lab, anc, (20,20,20), pad=5)
for lines,col,xy,anc in TAGS:
    draw_tag(lay, lines, col, xy, anc)
ld = ImageDraw.Draw(lay)

# ---------- 凡例 ----------
LX0,LY0,LX1,LY1 = 684,1100,1072,1568
ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
od.rounded_rectangle([LX0,LY0,LX1,LY1], radius=18, fill=(255,255,255,235), outline=(90,90,90,255), width=2)
lay.paste(ov,(0,0),ov); ld=ImageDraw.Draw(lay)
f_leg=F('Medium',24); f_legB=F('Bold',26)
y=LY0+28
ld.text((LX0+18,y),'凡例（9/26〜）',font=f_legB,fill=(20,20,20),anchor='lm'); y+=36
def swatch_glow(x0,y0,color,alpha,line_color,line_w):
    a=Image.new('L',(100,56),0); ad=ImageDraw.Draw(a); ad.line([(20,28),(80,28)],fill=alpha,width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); lay.paste(color,(x0-20,y0-28,x0+80,y0+28),a)
    ImageDraw.Draw(lay).line([(x0,y0),(x0+60,y0)],fill=line_color,width=line_w)
def item(sw, lines):
    global y, ld
    x0=LX0+18
    if sw=='black': swatch_glow(x0,y,BLACK,150,BLACK,THICK)
    elif sw=='purple': swatch_glow(x0,y,PURPLE,170,PURPLE,THICK)
    elif sw=='blue': swatch_glow(x0,y,BLUE,150,BLUE,THICK)
    elif sw=='red': swatch_glow(x0,y,RED,150,RED,THICK)
    elif sw=='thin':
        # 細線は路線ごとに色が異なるため、2色を並べて示す
        ImageDraw.Draw(lay).line([(x0,y),(x0+28,y)],fill=fade(C['sotobo']),width=THIN)
        ImageDraw.Draw(lay).line([(x0+32,y),(x0+60,y)],fill=fade(C['narita']),width=THIN)
    ld=ImageDraw.Draw(lay)
    for i,t in enumerate(lines):
        ld.text((x0+74,y+(0 if i==0 else 4+i*30)),t,font=f_leg if i else f_legB,fill=(20,20,20),anchor='lm')
    y+= 30*len(lines)+10
item('black',['運転取りやめ（長期）','1・3か月は9/23起点'])
item('purple',['運転取りやめ','10月初めの再開が目標'])
item('blue',['運転再開（26日始発）','本数は大幅に減る予定'])
item('red',['本数を減らして運転','図中は通常との比'])
item('thin',['細線（路線カラー）','計画に記載のない線区'])
ld.text((LX0+18,y-2),'※バス等の代行輸送は',font=f_leg,fill=(20,20,20),anchor='lm')
ld.text((LX0+18,y+26),'　28日の開始を目指す',font=f_leg,fill=(20,20,20),anchor='lm')
LEG_LAST_Y = y+26

sx,sy=30,MAP_BOT-75; L20=20*PXKM
ld.line([(sx,sy),(sx+L20,sy)],fill=(30,30,30),width=4)
ld.line([(sx,sy-8),(sx,sy+8)],fill=(30,30,30),width=4); ld.line([(sx+L20,sy-8),(sx+L20,sy+8)],fill=(30,30,30),width=4)
halo_text(lay, (sx+L20/2,sy-14), '20 km', F('Medium',22), 'mb', (30,30,30), pad=3)

# ODbL は Produced Work に権利表示を求める。画像単体で共有されるため、図中に置く
f_attr=F('Medium',24)
halo_text(lay, (30,1530), '地図データ © OpenStreetMap contributors', f_attr, 'lm', (60,60,60), pad=4)
halo_text(lay, (30,1560), 'openstreetmap.org/copyright（ODbL 1.0）', f_attr, 'lm', (60,60,60), pad=4)

# ---------- 最終キャンバス ----------
img = Image.new('RGB', (W,H), 'white')
img.paste(lay.crop((0,MAP_TOP,W,MAP_BOT)), (0,MAP_TOP))
d = ImageDraw.Draw(img)
d.text((W//2, 322), '9/26(土)以降 JR東日本 運転計画', font=F('DeBold',58), fill=(20,20,20), anchor='mm')
SUBTITLE = '台風25号被害 千葉県内の取りやめ・減便・再開区間　※一覧は次ページ'
d.text((W//2, 375), SUBTITLE, font=F('Medium',30), fill=(60,60,60), anchor='mm')
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
img.save(out)
print('font:', FAMILY)
print('saved:', out)

# ---------- 機械検査：駅名ラベル・札・注記同士、凡例・枠との重なり ----------
boxes=[]
for n,(anc,dx,dy,em) in LB.items():
    x,y0=P(*S(n)); f=f_labB if em else f_lab
    bb=f.getbbox(n, anchor=anc); boxes.append((n,(x+dx+bb[0]-5,y0+dy+bb[1]-5,x+dx+bb[2]+5,y0+dy+bb[3]+5)))
    boxes.append((n+'●',(x-10,y0-10,x+10,y0+10)))
for lines,col,xy,anc in TAGS:
    b = tag_box(lines, xy, anc); boxes.append(('札:'+lines[0], (b[0]-3,b[1]-3,b[2]+3,b[3]+3)))
for i, t in enumerate(NOTE_TXT):
    nx, ny = NOTE_XY[0], NOTE_XY[1]+NOTE_LH*i; nb = f_note.getbbox(t, anchor='lm')
    boxes.append(('注記', (nx+nb[0]-4, ny+nb[1]-4, nx+nb[2]+4, ny+nb[3]+4)))
def ov_(a,b): return not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])
probs=[(a,b) for i,(a,ba) in enumerate(boxes) for b,bb in boxes[i+1:] if ov_(ba,bb) and a.rstrip('●')!=b.rstrip('●')]
probs+=[(n,'凡例') for n,bb in boxes if ov_(bb,(LX0,LY0,LX1,LY1))]
probs+=[(n,'枠外') for n,bb in boxes if bb[0]<0 or bb[2]>W or bb[1]<MAP_TOP or bb[3]>MAP_BOT]
print('label overlaps:', probs)
print('legend last line y:', LEG_LAST_Y, 'box bottom:', LY1)
print('subtitle width:', round(F('Medium',30).getlength(SUBTITLE)), 'of', W)
print('legend widest line:', max(round(f_leg.getlength(t)) for t in ['1・3か月は9/23起点','10月初めの再開が目標','本数は大幅に減る予定','図中は通常との比','計画に記載のない線区']), 'of', LX1-(LX0+18+74)-8)

# 札・注記の下に、状態を持つ線（帯を含まない線そのもの）が通っていないかを調べる
from shapely.geometry import box as sbox
status_lines = [('黒',raw_pts(L)) for L in BLACK_LINES]+[('紫',raw_pts(L)) for L in PURPLE_LINES]+\
               [('青',raw_pts(L)) for L in BLUE_LINES]+[('赤',raw_pts(L)) for L in RED_LINES]+[('赤',p) for p in RED_EXTRA]+\
               [(key,p) for key,names,k,w,s in LINES for p in offset_pts(names,k)]
hits=[]
for n,bb in boxes:
    if not (n.startswith('札:') or n=='注記'): continue
    r = sbox(*bb)
    for nm,pts in status_lines:
        if LineString(pts).buffer(THICK/2+2).intersects(r): hits.append((n,nm))
print('tag/line crossings:', hits)
