"""Text measurement from the real font files (advance widths, line metrics).

Used to size pills and cards to their content, and to place manual line breaks so that wrapped
Chinese text never leaves a one-to-three-character orphan and centred text breaks at punctuation.
"""
import functools
import os
import re

from fontTools.ttLib import TTFont

from . import tokens as T

FONT_DIR = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
FILES = {
    'Noto Serif SC': 'NotoSerifSC-VF.ttf', 'Noto Serif SC SemiBold': 'NotoSerifSC-VF.ttf',
    'Noto Serif SC Medium': 'NotoSerifSC-VF.ttf', 'Noto Serif SC Light': 'NotoSerifSC-VF.ttf',
    'Noto Sans SC': 'NotoSansSC-VF.ttf', 'Goudy Old Style': 'GOUDOS.TTF', 'Garamond': 'GARA.TTF',
    '华文楷体': 'STKAITI.TTF', 'Cascadia Mono': 'CascadiaMono.ttf', 'Palatino Linotype': 'pala.ttf',
}
NO_START = set('，。、；：？！）》」』】〉’”%,.;:?!)]}…·')   # may not begin a line
NO_END = set('（《「『【〈‘“([{')                         # may not end a line
BREAK_AFTER = '，；：、,;:'


@functools.lru_cache(maxsize=None)
def _font(face):
    f = TTFont(os.path.join(FONT_DIR, FILES[face]), lazy=True)
    os2 = f['OS/2']
    return f.getBestCmap(), f['hmtx'].metrics, f['head'].unitsPerEm, os2.usWinAscent + os2.usWinDescent


def is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def _spc(role, size, spc):
    return spc if spc is not None else T.TRACK.get(role, 0) * size * 100


def width(text, size, role='body', spc=None):
    """Advance width (inches) of `text` at `size` pt in type role `role`; spc in 1/100 pt."""
    latin, ea = T.FONTS[role]
    total = 0.0
    for ch in text:
        cmap, hmtx, upm, _ = _font(ea if is_cjk(ch) else latin)
        g = cmap.get(ord(ch))
        if g is None:
            cmap, hmtx, upm, _ = _font(ea)
            g = cmap.get(ord(ch), '.notdef')
        total += hmtx.get(g, (upm // 2, 0))[0] / upm * size
    return (total + _spc(role, size, spc) / 100.0 * len(text)) / 72.0


def line_height(size, role='body', mult=1.0):
    """Height (inches) of one line at PowerPoint 'multiple' spacing `mult`."""
    _, _, upm, win = _font(T.FONTS[role][1])
    return size * win / upm * mult / 72.0


def _units(text):
    units = re.findall(r'[A-Za-z0-9][A-Za-z0-9.+%/]*-?|\s+|.', text)   # PowerPoint breaks after '-'
    out = []
    for u in units:
        if out and (u[0] in NO_START or out[-1][-1] in NO_END):
            out[-1] += u
        else:
            out.append(u)
    return out


def wrap(text, box_w, size, role='body', spc=None):
    """Greedy line breaking close to PowerPoint's (kinsoku rules on, Latin words kept whole)."""
    lines = []
    for para in text.split('\n'):
        cur, cur_w = '', 0.0
        for u in _units(para):
            uw = width(u, size, role, spc)
            if cur and not u.isspace() and cur_w + uw > box_w + 1e-6:
                lines.append(cur.rstrip())
                cur, cur_w = u, uw
            else:
                cur, cur_w = cur + u, cur_w + uw
        lines.append(cur.rstrip())
    return lines


def tidy(text, box_w, size, role='body', spc=None, balance=False, soft=''):
    """Return `text` with at most one manual break so the last line is not an orphan (<= 3 chars)
    and, with balance=True, two-line text splits at the punctuation closest to the middle.
    `soft` adds extra break-after characters (e.g. '的' for titles)."""
    if '\n' in text:
        return text
    lines = wrap(text, box_w, size, role, spc)
    if len(lines) < 2 or (len(lines[-1]) > 3 and not (balance and len(lines) == 2)):
        return text
    best, best_score = None, None
    for m in re.finditer('[%s]' % re.escape(BREAK_AFTER + soft), text):
        a, b = text[:m.end()], text[m.end():].lstrip()
        if not b:
            continue
        la, lb = wrap(a, box_w, size, role, spc), wrap(b, box_w, size, role, spc)
        if len(la) + len(lb) > len(lines) or len(lb[-1]) <= 3 or len(la[-1]) <= 3:
            continue
        score = abs(width(la[-1], size, role, spc) - width(lb[0], size, role, spc))
        if best_score is None or score < best_score:
            best, best_score = a + '\n' + b, score
    if best or len(lines[-1]) > 3:
        return best or text
    # no punctuation split: pull a few characters down at a CJK boundary so the last line reads as a phrase
    p = len(text) - len(lines[-1])
    for m in (3, 4, 2, 5):
        q = p - m
        if q <= 0 or not (is_cjk(text[q]) and is_cjk(text[q - 1])) or text[q] in NO_START:
            continue
        cand = text[:q] + '\n' + text[q:]
        if len(wrap(cand, box_w, size, role, spc)) == len(lines):
            return cand
    return text


def text_height(text, box_w, size, role='body', mult=1.0, spc=None):
    return len(wrap(text, box_w, size, role, spc)) * line_height(size, role, mult)
