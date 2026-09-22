# -*- coding: utf-8 -*-
"""1ページ目：運転計画の地図（2026年9月23日）。

  python scripts/render_map_20260923.py [出力先]

data/land.json・data/st.json を読み、既定では
output/JR東日本_運転計画_2026-09-23_ストーリー用_1地図.png を書き出す。
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
DEFAULT_OUT = os.path.join(OUTDIR, 'JR東日本_運転計画_2026-09-23_ストーリー用_1地図.png')

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
used_fb = []
def S(n):
    if n in st: return (st[n][0], st[n][1])
    raise KeyError('station not in st.json: ' + n)

SEA=(205,228,240); LAND=(243,240,232); COAST=(150,180,200)
BLACK=(25,25,25); PURPLE=(125,35,170); RED=(225,30,30)
# 路線カラー：Wikipedia「日本の鉄道ラインカラー一覧」JR東日本の表（2026-09-06 取得）の色コードによる
def hx(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
C = {'yamanote':hx('#9ACD32'),'keihin':hx('#00B2E5'),'tokaido':hx('#F68B1E'),'yokosuka':hx('#0067C0'),
     'sobu_local':hx('#FFD400'),'chuo':hx('#F15A22'),'utsunomiya':hx('#F68B1E'),'saikyo':hx('#00AC9A'),
     'joban':hx('#00B261'),'joban_local':hx('#00B261'),'musashino':hx('#F15A22'),'keiyo':hx('#C9252F'),
     'sobu_main':hx('#FFC20D'),'narita':hx('#00B261'),'uchibo':hx('#00B2E5'),'sotobo':hx('#DB4028'),
     'shonan':hx('#E31F26'),'sotetsu':hx('#00AC9A'),'kashima':hx('#C56E2E'),'togane':hx('#F15A22'),'kururi':hx('#00B5AD')}
GAP = 11.0
THIN, THICK = 6, 12

# (色キー, 駅列, 並走オフセット段数, 太さ, 状態)
#   状態: 'black'=23日終日取りやめ（24日以降も当面）/ 'purple'=23日終日取りやめ / 'red'=減便 / None=計画の発表なし
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
]
# 23日終日取りやめ、24日以降も当面の間取りやめ（被害甚大）
BLACK_LINES = [
 ['姉ケ崎','袖ケ浦','木更津'],
 ['佐倉','八街','成東'],
 ['佐原','小見川','笹川','松岸'],
 ['木更津','久留里','上総亀山'],
]
# 23日終日取りやめ（再開見通しは未定。千葉〜誉田は24日始発再開見込み）
PURPLE_LINES = [
 ['木更津','君津','上総湊','浜金谷','館山','千倉','和田浦','安房鴨川'],
 ['誉田','土気','大網','茂原','上総一ノ宮','大原','勝浦','安房小湊','安房鴨川'],
 ['木下','布佐','新木'],
 ['千葉','蘇我','鎌取','誉田'],
]
# 23日始発から運転再開、本数を減らして運転
RED_LINES = [
 ['千葉','四街道','佐倉'],
 ['成東','横芝','八日市場','旭','松岸','銚子'],
 ['佐倉','酒々井','成田','成田空港'],
 ['成田','滑河','佐原'],
 ['佐原','香取','潮来','鹿島神宮'],
 ['成田','安食','木下'],
 ['新木','我孫子'],
 ['大網','東金','成東'],
]

LB = {
 '東京':('lm',16,10,0),'新宿':('rm',-16,0,0),'池袋':('mb',-10,-14,0),'上野':('lm',14,-14,0),'品川':('rm',-16,6,0),
 '横浜':('lm',16,14,0),'大宮':('lm',18,0,0),'船橋':('mb',0,-16,0),
 '千葉':('rm',-14,-14,1),'蘇我':('rm',-14,12,1),'誉田':('mt',4,14,1),'大網':('lm',14,0,1),'茂原':('lm',14,0,0),
 '上総一ノ宮':('lm',14,0,0),'大原':('rm',-14,0,0),'勝浦':('mt',0,14,0),'安房鴨川':('mt',0,14,1),'館山':('rm',-14,0,0),
 '姉ケ崎':('rm',-14,0,1),'木更津':('rm',-14,0,1),'上総亀山':('lm',14,4,1),
 '佐倉':('mb',0,-12,1),'成田':('mb',4,-12,1),'成田空港':('lm',12,8,1),'成東':('lm',14,0,1),'東金':('rm',-14,-14,0),
 '八街':('mt',0,12,0),'八日市場':('mt',0,12,0),'旭':('mb',0,-12,0),'銚子':('rm',-16,-6,1),'佐原':('mb',-6,-12,1),
 '鹿島神宮':('lm',14,0,1),'我孫子':('mb',-6,-18,1),'木下':('mt',4,12,1),'新木':('lb',4,-10,1),'柏':('rm',-14,8,0),'松戸':('lm',14,0,0),
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
    """内房線（赤）千葉〜姉ケ崎。千葉〜蘇我は外房線（紫）と同じ線路を走るため、
    線の幅より広い 28px だけ西側（東京湾側）へ並べ、蘇我から五井へ向かう間で本来の位置へ戻す。"""
    a, b = raw_pts(['千葉'])[0], raw_pts(['蘇我'])[0]
    dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
    nx, ny = -dy/L*28, dx/L*28
    return [(a[0]+nx, a[1]+ny), (b[0]+nx, b[1]+ny)] + raw_pts(['五井','姉ケ崎'])
RED_EXTRA = [uchibo_pts()]

def draw_glow(groups, color, alpha, width, blur):
    # 色は固定し、透明度だけをぼかす（RGBA ごとぼかすと透明部の黒が混ざり黒ずむ）
    a = Image.new('L',(W,H),0); ad=ImageDraw.Draw(a)
    for pts in groups:
        ad.line(pts, fill=alpha, width=width, joint='curve')
    a = a.filter(ImageFilter.GaussianBlur(blur))
    lay.paste(color, (0,0,W,H), a)

STATUS_COL = {'red':RED, 'purple':PURPLE, 'black':BLACK}
SEV = {None:0, 'red':1, 'purple':2, 'black':3}
# 状態のある区間には各色の帯を敷く。計画の発表がない線区（細線）には帯を敷かない
draw_glow([pts for key,n,k,w,s in LINES if s=='red' for pts in offset_pts(n,k)] + [raw_pts(n) for n in RED_LINES] + RED_EXTRA, RED, 150, 44, 12)
draw_glow([pts for key,n,k,w,s in LINES if s=='purple' for pts in offset_pts(n,k)] + [raw_pts(n) for n in PURPLE_LINES], PURPLE, 170, 48, 12)
draw_glow([pts for key,n,k,w,s in LINES if s=='black' for pts in offset_pts(n,k)] + [raw_pts(n) for n in BLACK_LINES], BLACK, 150, 48, 12)
ld = ImageDraw.Draw(lay)

# 重なる箇所は状態の重大な順（黒＞紫＞赤＞細線）に上へ来るよう、重大度順に描く
segs=[]
for key,names,k,w,s in LINES:
    col = STATUS_COL.get(s, C[key])
    for pts in offset_pts(names,k): segs.append((SEV[s],col,w,pts))
for L in RED_LINES:    segs.append((1,RED,THICK,raw_pts(L)))
for pts in RED_EXTRA:  segs.append((1,RED,THICK,pts))
for L in PURPLE_LINES: segs.append((2,PURPLE,THICK,raw_pts(L)))
for L in BLACK_LINES:  segs.append((3,BLACK,THICK,raw_pts(L)))
segs.sort(key=lambda t:t[0])
for sev,col,w,pts in segs:
    ld.line(pts, fill='white', width=w+4, joint='curve')
    ld.line(pts, fill=col, width=w, joint='curve')

tx,ty = raw_pts(['取手'])[0]
halo_text(lay, (tx+40, MAP_TOP+34), '↑水戸方面', F('Medium',24), 'lm', (30,30,30), pad=4)
# 新木〜木下（約5 km）は紫の区間が短く、両側の赤に埋もれて見えにくいため文字で補う
f_note = F('Medium',22); NOTE_XY = (462, 536); NOTE_TXT = '新木〜木下は取りやめ'
halo_text(lay, NOTE_XY, NOTE_TXT, f_note, 'lt', PURPLE, pad=4)

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
ld.text((LX0+18,y),'凡例（9/23）',font=f_legB,fill=(20,20,20),anchor='lm'); y+=38
def swatch_glow(x0,y0,color,alpha,line_color,line_w):
    a=Image.new('L',(100,56),0); ad=ImageDraw.Draw(a); ad.line([(20,28),(80,28)],fill=alpha,width=30)
    a=a.filter(ImageFilter.GaussianBlur(7)); lay.paste(color,(x0-20,y0-28,x0+80,y0+28),a)
    ImageDraw.Draw(lay).line([(x0,y0),(x0+60,y0)],fill=line_color,width=line_w)
def item(sw, lines):
    global y, ld
    x0=LX0+18
    if sw=='black': swatch_glow(x0,y,BLACK,150,BLACK,THICK)
    elif sw=='purple': swatch_glow(x0,y,PURPLE,170,PURPLE,THICK)
    elif sw=='red': swatch_glow(x0,y,RED,150,RED,THICK)
    elif sw=='thin':
        ImageDraw.Draw(lay).line([(x0,y),(x0+60,y)],fill=C['yokosuka'],width=THIN)
    ld=ImageDraw.Draw(lay)
    for i,t in enumerate(lines):
        ld.text((x0+74,y+(0 if i==0 else 4+i*28)),t,font=f_leg if i else f_legB,fill=(20,20,20),anchor='lm')
    y+= 28*len(lines)+12
item('black',['終日運転取りやめ','（被害甚大。24日以降も','　当面取りやめ見込み）'])
item('purple',['終日運転取りやめ','（再開の見通しは未定）'])
item('red',['本数を減らして運転','（23日始発から運転再開）'])
item('thin',['細線：計画の発表なし','（路線カラー）'])
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
d.text((W//2, 322), '9/23(水・祝) JR東日本 運転計画', font=F('DeBold',58), fill=(20,20,20), anchor='mm')
d.text((W//2, 375), '台風25号被害に伴う運転取りやめ・減便区間　※一覧・注記は次ページ', font=F('Medium',30), fill=(60,60,60), anchor='mm')
out = sys.argv[1] if len(sys.argv)>1 else DEFAULT_OUT
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
img.save(out)
print('font:', FAMILY)
print('saved:', out)

# ---------- 機械検査：駅名ラベル同士・凡例との重なり ----------
boxes=[]
for n,(anc,dx,dy,em) in LB.items():
    x,y0=P(*S(n)); f=f_labB if em else f_lab
    bb=f.getbbox(n, anchor=anc); boxes.append((n,(x+dx+bb[0]-5,y0+dy+bb[1]-5,x+dx+bb[2]+5,y0+dy+bb[3]+5)))
nb = f_note.getbbox(NOTE_TXT, anchor='lt'); boxes.append(('注記', (NOTE_XY[0]+nb[0]-5, NOTE_XY[1]+nb[1]-5, NOTE_XY[0]+nb[2]+5, NOTE_XY[1]+nb[3]+5)))
def ov_(a,b): return not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])
probs=[(a,b) for i,(a,ba) in enumerate(boxes) for b,bb in boxes[i+1:] if ov_(ba,bb)]
probs+=[(n,'凡例') for n,bb in boxes if ov_(bb,(LX0,LY0,LX1,LY1))]
probs+=[(n,'枠外') for n,bb in boxes if bb[0]<0 or bb[2]>W or bb[1]<MAP_TOP or bb[3]>MAP_BOT]
print('label overlaps:', probs)
