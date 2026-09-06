# -*- coding: utf-8 -*-
"""1ページ目：運転計画の地図。

  python scripts/render_map.py [出力先]

data/land.json・data/st.json を読み、既定では
output/JR東日本_運転計画_2026-09-07_ストーリー用_1地図.png を書き出す。
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
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-07_ストーリー用_1地図.png')

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
FALLBACK = {
 '川崎': (139.6969,35.5318), '御茶ノ水': (139.7650,35.6996), '新橋': (139.7585,35.6660),
 '大船': (139.5307,35.3538), '四街道': (140.1690,35.6660), '鎌取': (140.1785,35.5628),
 '香取': (140.5320,35.8980), '潮来': (140.5496,35.9371),
 '武蔵小杉': (139.6597,35.5766), '羽沢横浜国大': (139.6015,35.4714),
}
used_fb = []
def S(n):
    if n in st: return (st[n][0], st[n][1])
    used_fb.append(n); return FALLBACK[n]

SEA=(205,228,240); LAND=(243,240,232); COAST=(150,180,200)
BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30); YELLOW=(255,200,0)
# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
C = {'yamanote':hx('#9ACD32'),'keihin':hx('#00B2E5'),'tokaido':hx('#F68B1E'),'yokosuka':hx('#0067C0'),
     'sobu_local':hx('#FFD400'),'chuo':hx('#F15A22'),'utsunomiya':hx('#F68B1E'),'saikyo':hx('#00AC9A'),
     'joban':hx('#00B261'),'joban_local':hx('#00B261'),'musashino':hx('#F15A22'),'keiyo':hx('#C9252F'),
     'sobu_main':hx('#FFC20D'),'narita':hx('#00B261'),'uchibo':hx('#00B2E5'),'sotobo':hx('#DB4028'),
     'shonan':hx('#E31F26'),'sotetsu':hx('#00AC9A')}
GAP = 16.0

# (色キー, 駅列, 並走オフセット段数, 太さ, 状態)  状態: 'red'=減便 / 'purple'=始発〜見合わせ / None=予告のみ
LINES = [
 ('yamanote', ['東京','品川','大崎','渋谷','新宿','池袋','田端','上野','東京'], 0, 12, 'red'),
 ('keihin',   ['大宮','南浦和','赤羽','田端','上野','東京','品川','川崎','横浜'], 1, 12, 'red'),
 ('utsunomiya',['大宮','赤羽','上野'], 2, 12, 'red'),
 ('tokaido',  ['東京','品川','川崎','横浜','大船'], 2, 12, 'red'),
 ('yokosuka', ['東京','品川','武蔵小杉','横浜','大船'], -1, 12, 'red'),
 ('saikyo',   ['大崎','渋谷','新宿','池袋','赤羽','武蔵浦和','大宮'], 1, 12, 'red'),
 ('shonan',   ['大宮','赤羽','池袋','新宿','渋谷','大崎','武蔵小杉','横浜','大船'], -2, 12, 'purple'),
 ('sotetsu',  ['新宿','渋谷','大崎','武蔵小杉','羽沢横浜国大'], -3, 12, 'purple'),
 ('yokosuka', ['東京','錦糸町','船橋','津田沼','千葉'], 1, 12, 'red'),
 ('sobu_local',['御茶ノ水','秋葉原','錦糸町','船橋','津田沼','千葉'], -1, 12, 'red'),
 ('chuo',     ['東京','御茶ノ水','新宿','三鷹'], 1, 12, 'red'),
 ('sobu_local',['御茶ノ水','新宿','三鷹'], -1, 12, 'red'),
 ('joban',    ['上野','北千住','松戸','柏','我孫子','取手','土浦'], 0, 12, 'red'),
 ('joban_local',['北千住','松戸','柏','我孫子','取手'], 1, 6, None),
 ('musashino',['北朝霞','武蔵浦和','南浦和','南越谷','新松戸','西船橋'], 0, 12, 'red'),
 ('keiyo',    ['東京','新木場','舞浜','南船橋','海浜幕張','千葉みなと','蘇我'], 0, 12, 'red'),
 ('sobu_main',['千葉','四街道','佐倉'], 0, 6, None),
 ('narita',   ['佐倉','酒々井','成田','成田空港'], 0, 6, None),
 ('uchibo',   ['蘇我','五井','袖ケ浦','木更津','君津'], 0, 6, None),
]
PURPLE_LINES = [
 ['佐倉','八街','成東','横芝','八日市場','旭','銚子'],
 ['成田','滑河','佐原','小見川','笹川','松岸','銚子'],
 ['成田','安食','木下','我孫子'],
 ['佐原','香取','潮来','鹿島神宮'],
 ['大網','東金','成東'],
 ['木更津','久留里','上総亀山'],
]
BLACK_LINES = [
 ['誉田','土気','大網','茂原','上総一ノ宮','大原','勝浦','安房小湊','安房鴨川'],
 ['君津','上総湊','浜金谷','館山','千倉','和田浦','安房鴨川'],
]
RED_LINES = [ ['千葉','蘇我','鎌取','誉田'] ]

LB = {
 '東京':('lm',16,10,0),'新宿':('rm',-16,0,0),'池袋':('mb',-10,-14,0),'上野':('lm',14,-14,0),'品川':('rm',-16,6,0),
 '横浜':('lm',16,14,0),'大宮':('lm',18,0,0),'船橋':('mb',0,-16,0),
 '千葉':('rm',-14,-14,1),'蘇我':('rm',-14,12,1),'誉田':('mt',4,14,1),'大網':('lm',14,0,1),'茂原':('lm',14,0,0),
 '上総一ノ宮':('lm',14,0,0),'大原':('rm',-14,0,0),'勝浦':('mt',0,14,0),'安房鴨川':('mt',0,14,1),'館山':('rm',-14,0,0),
 '木更津':('rm',-14,0,1),'君津':('rm',-14,4,1),'五井':('rm',-14,0,0),'久留里':('mb',0,-12,0),'上総亀山':('lm',14,4,1),
 '佐倉':('mb',0,-12,1),'成田':('mb',4,-12,1),'成田空港':('lm',12,8,0),'成東':('lm',14,0,1),'東金':('rm',-14,-14,0),
 '八街':('mt',0,12,0),'八日市場':('mt',0,12,0),'旭':('mb',0,-12,0),'銚子':('rm',-16,-6,1),'佐原':('mb',-6,-12,1),
 '鹿島神宮':('lm',14,0,1),'我孫子':('mb',-6,-18,1),'柏':('rm',-14,8,0),'松戸':('lm',14,0,0),
}

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
print('stations on sea:', len(bad))

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

# ---------- 線 ----------
def raw_pts(names):
    return [P(*S(n)) for n in names]
def offset_pts(names, k):
    pts=raw_pts(names)
    if k==0: return [pts]
    oc=LineString(pts).offset_curve(k*GAP, join_style='round')
    geoms = list(oc.geoms) if oc.geom_type=='MultiLineString' else [oc]
    return [list(g.coords) for g in geoms if len(g.coords)>=2]
def draw_glow(groups, color, alpha, width, blur):
    # 色は固定し、透明度だけをぼかす（RGBA ごとぼかすと透明部の黒が混ざり黒ずむ）
    a = Image.new('L',(W,H),0); ad=ImageDraw.Draw(a)
    for pts in groups:
        ad.line(pts, fill=alpha, width=width, joint='curve')
    a = a.filter(ImageFilter.GaussianBlur(blur))
    lay.paste(color, (0,0,W,H), a)

# 黄色の帯は予告のみ（状態指定なし）の線区に限る。黒・紫・赤の区間には各色の帯だけを敷く
draw_glow([raw_pts(n) for _,n,_,_,s in LINES if s is None], YELLOW, 190, 44, 12)
draw_glow([raw_pts(n) for _,n,_,_,s in LINES if s=='red'] + [raw_pts(n) for n in RED_LINES], RED, 150, 44, 12)
draw_glow([raw_pts(n) for _,n,_,_,s in LINES if s=='purple'] + [raw_pts(n) for n in PURPLE_LINES], PURPLE, 170, 48, 12)
draw_glow([raw_pts(n) for n in BLACK_LINES], BLACK, 150, 48, 12)
ld = ImageDraw.Draw(lay)

# 重なる箇所は状態の重大な順（黒＞紫＞赤＞細線）に上へ来るよう、重大度順に描く
SEV = {None:0, 'red':1, 'purple':2}
segs=[]
for key,names,k,w,s in LINES:
    col = RED if s=='red' else PURPLE if s=='purple' else C[key]
    for pts in offset_pts(names,k): segs.append((SEV[s],col,w,pts))
for L in RED_LINES:    segs.append((1,RED,12,raw_pts(L)))
for L in PURPLE_LINES: segs.append((2,PURPLE,12,raw_pts(L)))
for L in BLACK_LINES:  segs.append((3,BLACK,12,raw_pts(L)))
segs.sort(key=lambda t:t[0])
for sev,col,w,pts in segs:
    ld.line(pts, fill='white', width=w+4, joint='curve')
    ld.line(pts, fill=col, width=w, joint='curve')

tx,ty = raw_pts(['取手'])[0]
halo_text(lay, (tx+40, MAP_TOP+34), '↑水戸方面', F('Medium',24), 'lm', (30,30,30), pad=4)
# 直通サービスの注記（横浜南側）
f_note=F('Medium',24)
halo_text(lay, (22, 1165), '湘南新宿ライン・', f_note, 'lm', PURPLE, pad=4)
halo_text(lay, (22, 1193), '相鉄線直通（紫）', f_note, 'lm', PURPLE, pad=4)

f_lab=F('Medium',30); f_labB=F('Bold',32)
for n,(anc,dx,dy,em) in LB.items():
    x,y=P(*S(n)); r=10 if em else 8
    ld.ellipse([x-r,y-r,x+r,y+r], fill='white', outline=(30,30,30), width=3 if em else 2)
for n,(anc,dx,dy,em) in LB.items():
    x,y=P(*S(n))
    halo_text(lay, (x+dx,y+dy), n, f_labB if em else f_lab, anc, (20,20,20), pad=5)
ld = ImageDraw.Draw(lay)

# ---------- 凡例 ----------
LX0,LY0,LX1,LY1 = 684,1120,1072,1568
ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov)
od.rounded_rectangle([LX0,LY0,LX1,LY1], radius=18, fill=(255,255,255,235), outline=(90,90,90,255), width=2)
lay.paste(ov,(0,0),ov); ld=ImageDraw.Draw(lay)
f_leg=F('Medium',22); f_legB=F('Bold',26)
y=LY0+28
ld.text((LX0+18,y),'凡例',font=f_legB,fill=(20,20,20),anchor='lm'); y+=38
def swatch_glow(x0,y0,color,alpha,line_color,line_w):
    a=Image.new('L',(100,56),0); ad=ImageDraw.Draw(a); ad.line([(20,28),(80,28)],fill=alpha,width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); lay.paste(color,(x0-20,y0-28,x0+80,y0+28),a)
    ImageDraw.Draw(lay).line([(x0,y0),(x0+60,y0)],fill=line_color,width=line_w)
def item(sw, lines):
    global y, ld
    x0=LX0+18
    if sw=='black': swatch_glow(x0,y,BLACK,150,BLACK,12)
    elif sw=='purple': swatch_glow(x0,y,PURPLE,170,PURPLE,12)
    elif sw=='red': swatch_glow(x0,y,RED,150,RED,12)
    elif sw=='yellow': swatch_glow(x0,y,YELLOW,190,C['uchibo'],6)
    ld=ImageDraw.Draw(lay)
    for i,t in enumerate(lines):
        ld.text((x0+74,y+(0 if i==0 else 4+i*28)),t,font=f_leg if i else f_legB,fill=(20,20,20),anchor='lm')
    y+= 28*len(lines)+12
item('black',['6日夜〜運転取りやめ','（7日夕方頃まで継続）'])
item('purple',['7日始発〜運転見合わせ','（夕方頃まで。久留里〜','　上総亀山間は終日）'])
item('red',['本数を減らして運転','（7日。混雑のため来駅は','　控えるよう呼びかけ）'])
item('yellow',['遅れ・運休の可能性あり','（6日夜〜7日。細線は','　路線カラー）'])
ld.text((LX0+18,y-2),'※バス代行輸送なし',font=f_leg,fill=(20,20,20),anchor='lm')

sx,sy=30,MAP_BOT-75; L20=20*PXKM
ld.line([(sx,sy),(sx+L20,sy)],fill=(30,30,30),width=4)
ld.line([(sx,sy-8),(sx,sy+8)],fill=(30,30,30),width=4); ld.line([(sx+L20,sy-8),(sx+L20,sy+8)],fill=(30,30,30),width=4)
halo_text(lay, (sx+L20/2,sy-14), '20 km', F('Medium',22), 'mb', (30,30,30), pad=3)

# ODbL は Produced Work に権利表示を求める。画像単体で共有されるため、図中に置く
f_attr=F('Medium',22)
halo_text(lay, (30,1532), '地図データ © OpenStreetMap contributors', f_attr, 'lm', (60,60,60), pad=4)
halo_text(lay, (30,1560), 'openstreetmap.org/copyright（ODbL 1.0）', f_attr, 'lm', (60,60,60), pad=4)

# ---------- 最終キャンバス ----------
img = Image.new('RGB', (W,H), 'white')
img.paste(lay.crop((0,MAP_TOP,W,MAP_BOT)), (0,MAP_TOP))
d = ImageDraw.Draw(img)
d.text((W//2, 322), '9/7(月) JR東日本 運転計画', font=F('DeBold',58), fill=(20,20,20), anchor='mm')
d.text((W//2, 375), '大雨に伴う運転見合わせ・減便区間　※一覧・注記は次ページ', font=F('Medium',30), fill=(60,60,60), anchor='mm')
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
img.save(out)
print('font:', FAMILY)
print('fallback used:', used_fb)
print('saved:', out)
