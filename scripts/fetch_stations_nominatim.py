# -*- coding: utf-8 -*-
"""Overpass API が応答しないときの補助。指定した駅を Nominatim で検索し data/st.json に加える。

  python scripts/fetch_stations_nominatim.py 姉ケ崎 布佐 新木

駅名だけでは同名の地名に当たることがあるため、下の HINT に市名を添えて検索する。
出所は OpenStreetMap（© OpenStreetMap contributors, ODbL 1.0）。利用規約に従い、
1秒に1回を超えて問い合わせない。
"""
import io, json, os, sys, time, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, 'data', 'st.json')
HINT = {'姉ケ崎': '市原市', '布佐': '我孫子市', '新木': '我孫子市'}
UA = 'jreast-service-plan-map/1.0 (https://github.com/yukikase0422/jreast-service-plan-map)'

st = json.load(io.open(ST, encoding='utf-8'))
for name in sys.argv[1:]:
    q = name + '駅 ' + HINT.get(name, '千葉県')
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode(
        {'q': q, 'format': 'json', 'limit': 5, 'accept-language': 'ja'})
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    hits = [x for x in d if x.get('class') in ('railway', 'public_transport')
            or x.get('type') in ('train_station', 'station') or '駅' in x.get('display_name', '')]
    if not hits:
        print('not found:', name); continue
    x = hits[0]
    st[name] = (round(float(x['lon']), 5), round(float(x['lat']), 5), 1, 1)
    print(name, st[name], x.get('display_name', '')[:40])
    time.sleep(1.2)
json.dump(st, io.open(ST, 'w', encoding='utf-8'), ensure_ascii=False)
print('stations', len(st))
