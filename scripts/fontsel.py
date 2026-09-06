# -*- coding: utf-8 -*-
"""日本語フォントの選択。

作図に用いたモリサワ 新ゴ Pro は再配布できないため、環境にあるものを次の順で採る。

1. モリサワ 新ゴ Pro（A-OTF-ShinGoPro-*.otf）
2. BIZ UDゴシック（Windows 10/11 に同梱。BIZ-UDGothicB.ttc / BIZ-UDGothicR.ttc）
3. Noto Sans JP（可変フォント・静的ウェイトのいずれでも可）

ウェイトは新ゴの名称（DeBold / Bold / Medium / Regular）で指定する。代替フォントは
Bold と Regular の2段しか持たないため、DeBold・Bold は Bold、Medium・Regular は
Regular に割り当てる。字面と字送りが変わるので、版面は新ゴの場合と完全には一致しない。
"""
import os
from PIL import ImageFont

SHINGO_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                          r'Microsoft\Windows\Fonts\MorisawaFonts')
WINFONTS = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Fonts')

# DeBold・Bold → 太字、Medium・Regular → 細字
IS_BOLD = {'DeBold': True, 'Bold': True, 'Medium': False, 'Regular': False}

NOTO_VARIABLE = ['NotoSansJP-VF.ttf', 'NotoSansJP[wght].ttf', 'NotoSansJP-VariableFont_wght.ttf']
NOTO_STATIC = {True: ['NotoSansJP-Bold.otf', 'NotoSansJP-Bold.ttf', 'NotoSansCJKjp-Bold.otf'],
               False: ['NotoSansJP-Regular.otf', 'NotoSansJP-Regular.ttf', 'NotoSansCJKjp-Regular.otf']}
NOTO_DIRS = [WINFONTS,
             os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Microsoft\Windows\Fonts'),
             '/usr/share/fonts/opentype/noto', '/usr/share/fonts/truetype/noto',
             '/usr/share/fonts/opentype/notosanscjk', '/Library/Fonts',
             os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')]


def _first_existing(dirs, names):
    for d in dirs:
        if not d:
            continue
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def _pick():
    """(名称, ウェイト名を受け取ってフォントを返す関数) を決める。"""
    if all(os.path.exists(os.path.join(SHINGO_DIR, 'A-OTF-ShinGoPro-%s.otf' % w)) for w in IS_BOLD):
        def load(weight, size):
            return ImageFont.truetype(os.path.join(SHINGO_DIR, 'A-OTF-ShinGoPro-%s.otf' % weight), size)
        return 'モリサワ 新ゴ Pro', load

    biz_b = os.path.join(WINFONTS, 'BIZ-UDGothicB.ttc')
    biz_r = os.path.join(WINFONTS, 'BIZ-UDGothicR.ttc')
    if os.path.exists(biz_b) and os.path.exists(biz_r):
        def load(weight, size):
            return ImageFont.truetype(biz_b if IS_BOLD[weight] else biz_r, size, index=0)
        return 'BIZ UDゴシック', load

    vf = _first_existing(NOTO_DIRS, NOTO_VARIABLE)
    if vf:
        def load(weight, size):
            f = ImageFont.truetype(vf, size)
            try:
                f.set_variation_by_name('Bold' if IS_BOLD[weight] else 'Regular')
            except Exception:
                pass
            return f
        return 'Noto Sans JP (Variable)', load

    st_b = _first_existing(NOTO_DIRS, NOTO_STATIC[True])
    st_r = _first_existing(NOTO_DIRS, NOTO_STATIC[False])
    if st_b and st_r:
        def load(weight, size):
            return ImageFont.truetype(st_b if IS_BOLD[weight] else st_r, size)
        return 'Noto Sans JP', load

    raise SystemExit('日本語フォントが見つかりません。新ゴ Pro・BIZ UDゴシック・'
                     'Noto Sans JP のいずれかを導入するか、リポジトリ直下の fonts/ に '
                     'NotoSansJP-Regular.ttf と NotoSansJP-Bold.ttf を置いてください。')


FAMILY, _load = _pick()
_cache = {}


def F(weight, size):
    """新ゴのウェイト名（DeBold / Bold / Medium / Regular）でフォントを得る。"""
    key = (weight, size)
    if key not in _cache:
        _cache[key] = _load(weight, size)
    return _cache[key]
