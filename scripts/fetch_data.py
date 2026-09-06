# -*- coding: utf-8 -*-
"""地図描画に使う基礎データを取得して data/ に保存する。

いずれも OpenStreetMap を Overpass API 経由で取得したものである。
© OpenStreetMap contributors、Open Database License (ODbL) 1.0。

- data/land.json : 陸地ポリゴン（natural=coastline のウェイを繋ぎ、範囲の縁で閉じたもの）
- data/st.json   : 駅の座標（railway=station のノード）

使い方:  python scripts/fetch_data.py [land|stations]
"""
import json, os, sys, time, urllib.request, urllib.parse
from shapely.geometry import LineString, LinearRing, Polygon, box
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data')
os.makedirs(OUT, exist_ok=True)

# 陸地を切り出す範囲（西, 南, 東, 北）
WEST, SOUTH, EAST, NORTH = 139.40, 34.80, 141.00, 36.30
# 島として残す最小面積（度^2）。約0.7ピクセル相当より小さいものは落とす
MIN_ISLAND_AREA = 1e-6
# 簡略化の許容誤差（度）。約30メートル
SIMPLIFY_TOL = 0.0003

ENDPOINTS = ['https://overpass-api.de/api/interpreter',
             'https://overpass.kumi.systems/api/interpreter',
             'https://overpass.private.coffee/api/interpreter']

STATIONS = [
 '東京','品川','大崎','渋谷','新宿','池袋','田端','上野','大宮','南浦和','赤羽','川崎','横浜','武蔵小杉','大船',
 '武蔵浦和','羽沢横浜国大','錦糸町','船橋','津田沼','千葉','御茶ノ水','秋葉原','三鷹','北千住','松戸','柏','我孫子',
 '取手','土浦','北朝霞','南越谷','新松戸','西船橋','新木場','舞浜','南船橋','海浜幕張','千葉みなと','蘇我','四街道',
 '佐倉','酒々井','成田','成田空港','五井','袖ケ浦','木更津','君津','八街','成東','横芝','八日市場','旭','銚子','滑河',
 '佐原','小見川','笹川','松岸','安食','木下','香取','潮来','鹿島神宮','大網','東金','久留里','上総亀山','誉田','土気',
 '茂原','上総一ノ宮','大原','勝浦','安房小湊','安房鴨川','上総湊','浜金谷','館山','千倉','和田浦','鎌取',
]


def overpass(query):
    """Overpass API に問い合わせる。混雑時に備えて複数のミラーを順に試す。"""
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    last = None
    for ep in ENDPOINTS:
        for attempt in range(2):
            try:
                print('query', ep)
                req = urllib.request.Request(
                    ep, data=data, headers={'User-Agent': 'jr-east-plan-map/1.0'})
                with urllib.request.urlopen(req, timeout=900) as r:
                    return json.load(r)
            except Exception as ex:      # 504 等はミラーを替えると通ることが多い
                print('  failed:', type(ex).__name__, ex)
                last = ex
                time.sleep(10)
    raise last


def chain_ways(ways):
    """coastline のウェイを、共有するノード ID を辿って繋ぐ。

    戻り値は (座標列, 閉じているか) のリスト。ウェイの向きは元のまま保つ。
    """
    by_first = {}
    for w in ways:
        by_first.setdefault(w['nodes'][0], []).append(w['id'])
    ends = set(w['nodes'][-1] for w in ways)
    by_id = {w['id']: w for w in ways}
    used = set()

    def follow(wid):
        nodes = list(by_id[wid]['nodes'])
        coords = [(g['lon'], g['lat']) for g in by_id[wid]['geometry']]
        used.add(wid)
        while nodes[-1] != nodes[0]:
            nxt = [x for x in by_first.get(nodes[-1], []) if x not in used]
            if not nxt:
                break
            w = by_id[nxt[0]]
            used.add(nxt[0])
            nodes += w['nodes'][1:]
            coords += [(g['lon'], g['lat']) for g in w['geometry']][1:]
        return coords, nodes[-1] == nodes[0]

    out = []
    # 端から伸びる鎖を先に辿り、残ったもの（環）を後から拾う
    for wid, w in by_id.items():
        if w['nodes'][0] not in ends and wid not in used:
            out.append(follow(wid))
    for wid in by_id:
        if wid not in used:
            out.append(follow(wid))
    return out


def close_along_bbox(pieces):
    """範囲の縁で切れた海岸線を、縁を辿って閉じ、陸のポリゴンにする。

    coastline のウェイは進行方向の左が陸と定められている。左が内側になる向き
    （反時計回り）に縁を辿って次の海岸線の始点へ繋げば、囲まれた側が陸になる。
    """
    w, h = EAST - WEST, NORTH - SOUTH
    per = 2 * (w + h)

    def t_of(p):
        """範囲の縁上の点を、南西角を起点とする反時計回りの距離で表す。"""
        x, y = p
        if abs(y - SOUTH) < 1e-7: return x - WEST
        if abs(x - EAST) < 1e-7:  return w + (y - SOUTH)
        if abs(y - NORTH) < 1e-7: return w + h + (EAST - x)
        if abs(x - WEST) < 1e-7:  return 2 * w + h + (NORTH - y)
        raise ValueError('端点が範囲の縁にない: %r' % (p,))

    corners = [(0.0, (WEST, SOUTH)), (w, (EAST, SOUTH)),
               (w + h, (EAST, NORTH)), (2 * w + h, (WEST, NORTH))]
    starts = sorted((t_of(p[0]), i) for i, p in enumerate(pieces))
    rings, unused = [], set(range(len(pieces)))
    while unused:
        first = min(unused)
        cur, coords = first, []
        while True:
            unused.discard(cur)
            coords += pieces[cur]
            te = t_of(pieces[cur][-1])
            nxt = next((s for s in starts if s[0] > te + 1e-9), starts[0])
            ts = nxt[0] if nxt[0] > te else nxt[0] + per
            # 途中の角を挟む。起点をまたぐ場合があるので、辿る順に並べ直してから加える
            for tc, pc in sorted((tc if tc > te else tc + per, pc) for tc, pc in corners):
                if te < tc < ts:
                    coords.append(pc)
            if nxt[1] == first or nxt[1] not in unused:
                break
            cur = nxt[1]
        rings.append(Polygon(coords).buffer(0))
    return rings


def fetch_land():
    q = ('[out:json][timeout:600];'
         'way["natural"="coastline"](%s,%s,%s,%s);'
         'out geom;' % (SOUTH, WEST, NORTH, EAST))
    d = overpass(q)
    ways = [e for e in d['elements'] if e['type'] == 'way' and e.get('geometry')]
    print('coastline ways', len(ways))
    chains = chain_ways(ways)
    bb = box(WEST, SOUTH, EAST, NORTH)

    pieces, islands = [], []
    for coords, is_ring in chains:
        if is_ring:
            # 閉じた環は島（反時計回り）か、陸に囲まれた海（時計回り）
            ring = LinearRing(coords)
            poly = Polygon(ring).buffer(0)
            if poly.area < MIN_ISLAND_AREA:
                continue
            poly = poly.intersection(bb)
            if poly.is_empty:
                continue
            islands.append((poly, ring.is_ccw))
        else:
            g = LineString(coords).intersection(bb)
            for gg in (g.geoms if g.geom_type == 'MultiLineString' else [g]):
                if not gg.is_empty and len(gg.coords) >= 2:
                    pieces.append(list(gg.coords))
    print('open pieces', len(pieces), ' rings kept', len(islands))

    land = unary_union(close_along_bbox(pieces) + [p for p, ccw in islands if ccw])
    inner_sea = [p for p, ccw in islands if not ccw]
    if inner_sea:
        land = land.difference(unary_union(inner_sea))
    land = land.simplify(SIMPLIFY_TOL).buffer(0)
    print('land area (deg^2) %.4f / bbox %.4f' % (land.area, bb.area))
    json.dump(land.__geo_interface__, open(os.path.join(OUT, 'land.json'), 'w'))


def fetch_stations():
    names = '|'.join(STATIONS)
    q = ('[out:json][timeout:120];'
         'node["railway"="station"]["name"~"^(' + names + ')$"](34.8,139.3,36.7,141.0);out;')
    d = overpass(q)
    st = {}
    for e in d['elements']:
        n = e['tags'].get('name')
        st.setdefault(n, []).append((e['lon'], e['lat'], e['tags'].get('operator', ''), e['tags'].get('network', '')))
    out = {}
    for n, v in st.items():
        # 同名駅が複数ある場合は JR 東日本のものを優先し、平均座標を採る
        jr = [x for x in v if 'JR' in x[2] or '東日本' in x[2] or 'JR' in x[3]]
        use = jr if jr else v
        out[n] = (round(sum(x[0] for x in use) / len(use), 5), round(sum(x[1] for x in use) / len(use), 5), len(v), len(jr))
    missing = [n for n in STATIONS if n not in out]
    print('stations', len(out), 'missing', missing)
    json.dump(out, open(os.path.join(OUT, 'st.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    if 'stations' not in sys.argv: fetch_land()
    if 'land' not in sys.argv: fetch_stations()
