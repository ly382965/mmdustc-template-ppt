"""Engraved, hand-tinted illustrations (SVG). One drawing language for all of them:
warm iron-gall outlines, parchment/brass/clay washes, hatching clipped to shadow sides.

Every function returns an SVG string with a 240 x 240 viewBox unless noted.
"""
import math

import numpy as np

from .geom import arc, cubic, curve, d_line, d_poly, ellipse_pts, leaf, ribbon, rotate
from .svg import Svg

INK = '#4A3D30'
INK_SOFT = '#6B5B4A'
BRASS, BRASS_DK, BRASS_LT = '#D9BF88', '#B59258', '#ECDDB8'
WOOD, WOOD_DK = '#B68C63', '#8E6744'
PARCH, PARCH_DK = '#F4EBD8', '#E0CFAE'
GLASS = '#EEF2F1'
SAND = '#D7B276'
CLAY, CLAY_LT, CLAY_DK = '#B0503A', '#CB7357', '#86392A'
LW, LW2, LWH = 2.0, 1.2, 0.7      # outline, detail, hatch widths


def canvas(w=240, h=240):
    return Svg(w / 240 * 144, h / 240 * 144, (0, 0, w, h))


def shape(s, pts, fill, lw=LW, stroke=INK, op=None):
    s.poly(pts, fill=fill, stroke=stroke, sw=lw, op=op)


def hatch(s, clip_pts, angle=60, gap=3.2, lw=LWH, color=INK, op=0.55, box=(0, 0, 240, 240)):
    """Parallel engraving lines clipped to a polygon."""
    cid = s.clip(d_poly(clip_pts))
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = math.hypot(x1 - x0, y1 - y0) / 2 + 4
    a = math.radians(angle)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    s.open(clip=cid, op=op)
    for k in np.arange(-r, r, gap):
        p = np.array([cx, cy]) + n * k
        s.line([p - d * r, p + d * r], color, lw, cap='butt')
    s.close()


def ground(s, cx, cy, rx, ry=None, op=0.09):
    s.ellipse(cx, cy, rx, ry or rx * 0.075, fill=INK, op=op)


def lathe(cx, ys, rs):
    """Outline of a turned object: profile radii rs at heights ys (top -> bottom)."""
    ys, rs = np.asarray(ys, float), np.asarray(rs, float)
    right = np.stack([cx + rs, ys], 1)
    left = np.stack([cx - rs, ys], 1)[::-1]
    return np.concatenate([right, left])


def bumps(y, base, spec):
    """Profile radius = base + sum of gaussian beads (centre, height, width)."""
    r = np.full_like(y, base, dtype=float)
    for c, hgt, wid in spec:
        r += hgt * np.exp(-((y - c) / wid) ** 2)
    return r


# ---------------------------------------------------------------------------------------------
#  Hourglass — scarcity, time
# ---------------------------------------------------------------------------------------------
def hourglass():
    s = canvas()
    cx = 120.0
    ground(s, cx, 216, 70)
    # glass bulbs (right half as cubic segments, mirrored)
    top = cubic((cx + 31, 45), (cx + 47, 56), (cx + 40, 100), (cx + 3.2, 120), 60)
    bot = cubic((cx + 3.2, 120), (cx + 40, 140), (cx + 47, 184), (cx + 31, 195), 60)
    right = np.concatenate([top, bot[1:]])
    left = right[::-1] * (-1, 1) + (2 * cx, 0)
    glass = np.concatenate([right, left])
    # sand: bottom heap and the last grains in the upper bulb, clipped to the glass
    cid = s.clip(d_poly(glass))
    s.open(clip=cid)
    heap = np.concatenate([cubic((cx - 50, 200), (cx - 30, 176), (cx - 10, 160), (cx, 156), 30),
                           cubic((cx, 156), (cx + 10, 160), (cx + 30, 176), (cx + 50, 200), 30)[1:],
                           [[cx + 50, 205], [cx - 50, 205]]])
    s.poly(heap, fill=SAND, stroke=INK_SOFT, sw=LW2)
    upper = np.concatenate([cubic((cx - 30, 104), (cx - 12, 108), (cx + 12, 108), (cx + 30, 104), 30),
                            [[cx + 30, 125], [cx - 30, 125]]])
    s.poly(upper, fill=SAND, stroke=INK_SOFT, sw=LW2)
    s.close()
    s.open(clip=cid)
    hatch(s, heap, angle=-35, gap=3.4, op=0.35)
    s.close()
    s.poly(glass, fill=GLASS, stroke=INK, sw=1.6, fop=0.35)
    # glints
    s.line(cubic((cx - 34, 58), (cx - 40, 70), (cx - 34, 90), (cx - 20, 104), 30), '#FFFFFF', 2.4, op=0.85)
    s.line(cubic((cx - 24, 140), (cx - 38, 152), (cx - 40, 172), (cx - 33, 186), 30), '#FFFFFF', 2.4, op=0.85)
    # turned posts
    ys = np.linspace(43, 197, 120)
    for px in (cx - 48, cx + 48):
        rs = bumps(ys, 2.6, [(52, 2.6, 4), (120, 3.4, 8), (188, 2.6, 4), (86, 1.0, 10), (154, 1.0, 10)])
        post = lathe(px, ys, rs)
        shape(s, post, WOOD, LW2 + 0.3)
        hatch(s, np.concatenate([np.stack([px + rs * 0.1, ys], 1), np.stack([px + rs, ys], 1)[::-1]]),
              angle=90, gap=2.2, op=0.55)
    # plates
    for y0, sign in ((28, 1), (197, -1)):
        plate = np.array([[cx - 62, y0], [cx + 62, y0], [cx + 62, y0 + 15], [cx - 62, y0 + 15]])
        shape(s, plate, WOOD)
        band_y = y0 + (10 if sign > 0 else 5)
        s.line([(cx - 62, band_y), (cx + 62, band_y)], INK, LW2)
        shade = np.array([[cx - 62, band_y], [cx + 62, band_y], [cx + 62, y0 + 15 if sign > 0 else y0],
                          [cx - 62, y0 + 15 if sign > 0 else y0]])
        hatch(s, shade, angle=0, gap=2.0, op=0.5)
    for fx in (cx - 48, cx + 48):
        s.path('M%s 212 a7 5 0 0 0 14 0Z' % (fx - 7), fill=WOOD_DK, stroke=INK, sw=LW2)
        s.path('M%s 28 a5 4 0 0 1 10 0Z' % (fx - 5), fill=WOOD_DK, stroke=INK, sw=LW2)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Balance scales — comparing two modalities
# ---------------------------------------------------------------------------------------------
def scales(tilt=5.0):
    s = canvas()
    cx, by = 120.0, 64.0
    ground(s, cx, 214, 64)
    # column + flared foot (one turned profile)
    ys = np.linspace(56, 212, 200)
    rs = bumps(ys, 3.6, [(74, 2.6, 3.5), (124, 3.2, 5), (176, 2.8, 3.5)])
    rs += 44 * (np.clip(ys - 184, 0, None) / 28) ** 2.2
    col = lathe(cx, ys, rs)
    shape(s, col, BRASS)
    hatch(s, np.concatenate([np.stack([cx + rs * 0.15, ys], 1), np.stack([cx + rs, ys], 1)[::-1]]),
          angle=90, gap=2.2, op=0.5)
    fw = float(np.interp(204, ys, rs))
    s.line([(cx - fw, 204), (cx + fw, 204)], INK, LW2)
    # beam, pivot and pointer
    a = math.radians(-tilt)
    d = np.array([math.cos(a), math.sin(a)])
    ends = [np.array([cx, by]) - d * 84, np.array([cx, by]) + d * 84]
    beam = np.stack([np.linspace(ends[0][0], ends[1][0], 80), np.linspace(ends[0][1], ends[1][1], 80)], 1)
    u = np.linspace(-1, 1, 80)
    shape(s, ribbon(beam, 2.6 + 3.6 * (1 - np.abs(u)) ** 1.5), BRASS, LW2 + 0.2)
    for e in ends:
        s.circle(e[0], e[1], 3.6, fill=BRASS, stroke=INK, sw=LW2)
    tip = np.array([cx, by]) + rotate(np.array([[0, -24]]), -tilt)[0]
    shape(s, np.array([[cx - 3.2, by], tip, [cx + 3.2, by]]), BRASS_DK, LW2)
    s.circle(cx, by, 7, fill=BRASS, stroke=INK, sw=LW)
    s.circle(cx, by, 2.2, fill=INK)
    s.circle(cx, 44 - 2, 4.2, fill=BRASS, stroke=INK, sw=LW2)
    # pans hang from the beam ends; the lower pan carries a weight
    for i, e in enumerate(ends):
        py = e[1] + 74
        for k in (-1, 0, 1):
            s.line([(e[0], e[1] + 3.5), (e[0] + k * 27, py)], INK_SOFT, 1.0)
        bowl = arc((e[0], py), 29, 0, 180, 60, ry=14)
        rim = ellipse_pts((e[0], py), 29, 4.6, 0, 90)
        shape(s, bowl, BRASS)
        hatch(s, bowl, angle=75, gap=2.4, op=0.4)
        shape(s, rim, BRASS_LT, LW2 + 0.2)
        if i == 0:
            wy = py - 3
            wt = np.array([[e[0] - 9, wy], [e[0] - 6.5, wy - 13], [e[0] + 6.5, wy - 13], [e[0] + 9, wy]])
            shape(s, wt, BRASS_DK, LW2 + 0.2)
            s.circle(e[0], wy - 16, 3.2, fill=BRASS_DK, stroke=INK, sw=LW2)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Astrolabe — navigating the unseen
# ---------------------------------------------------------------------------------------------
def astrolabe():
    s = canvas()
    c = np.array([120.0, 132.0])
    R = 80.0
    ground(s, 120, 222, 58)
    # shackle + throne
    s.circle(120, 28, 9.5, fill='none', stroke=INK, sw=5.2)
    s.circle(120, 28, 9.5, fill='none', stroke=BRASS, sw=3.0)
    throne = np.concatenate([cubic((100, 58), (104, 48), (110, 40), (120, 38), 30),
                             cubic((120, 38), (130, 40), (136, 48), (140, 58), 30)[1:]])
    shape(s, throne, BRASS)
    s.circle(120, 47, 3.4, fill=BRASS_DK, stroke=INK, sw=LW2)
    # mater + limb with degree scale
    s.circle(c[0], c[1], R, fill=BRASS, stroke=INK, sw=LW)
    lim = np.concatenate([arc(c, R, 0, 360, 240), arc(c, R - 9, 360, 0, 240)])
    shade = np.concatenate([arc(c, R, -20, 120, 120), arc(c, R - 9, 120, -20, 120)])
    hatch(s, shade, angle=-45, gap=2.3, op=0.45)
    for k in range(72):
        a = math.radians(k * 5)
        r0 = R - (8.5 if k % 3 == 0 else 4.5)
        p0 = c + r0 * np.array([math.cos(a), math.sin(a)])
        p1 = c + (R - 1.2) * np.array([math.cos(a), math.sin(a)])
        s.line([p0, p1], INK, 0.8 if k % 3 else 1.1, cap='butt')
    # plate with almucantars, horizon and meridian
    s.circle(c[0], c[1], R - 9, fill=BRASS_LT, stroke=INK, sw=LW2)
    pid = s.clip(d_poly(arc(c, R - 9, 0, 360, 240)))
    s.open(clip=pid)
    for k in range(1, 8):
        rr = 64 - k * 7.2
        s.circle(c[0], c[1] - 10 - k * 4.2, rr, fill='none', stroke=INK_SOFT, sw=0.7, op=0.8)
    s.line([(c[0] - R, c[1] + 6), (c[0] + R, c[1] + 6)], INK_SOFT, 0.8)
    s.line([(c[0], c[1] - R), (c[0], c[1] + R)], INK_SOFT, 0.8)
    s.close()
    # rete: ecliptic ring, spokes and flame-shaped star pointers
    ec = c + (0, -9)
    s.circle(ec[0], ec[1], 45, fill='none', stroke=INK, sw=7.6)
    s.circle(ec[0], ec[1], 45, fill='none', stroke=BRASS, sw=5.0)
    for k in range(24):
        a = math.radians(k * 15)
        u = np.array([math.cos(a), math.sin(a)])
        s.line([ec + u * 42.6, ec + u * 47.4], INK, 0.7, cap='butt')
    for ang in (30, 150, 270):
        a = math.radians(ang)
        u = np.array([math.cos(a), math.sin(a)])
        s.line([c + u * 6, ec + u * 41], INK, 3.6)
        s.line([c + u * 6, ec + u * 41], BRASS, 1.8)
    for ang in (-55, 35, 120, 205):
        a = math.radians(ang)
        u = np.array([math.cos(a), math.sin(a)])
        base = ec + u * 47.5
        fl = curve(tuple(base), ang - 18, 17, lambda t: math.radians(70) / 17 * (0.4 + t))
        tip = fl[-1]
        shape(s, ribbon(fl, 6.4 * (1 - np.linspace(0, 1, len(fl))) ** 0.8 + 0.2), BRASS, LW2)
        s.circle(tip[0], tip[1], 1.6, fill=INK)
    # rule across the face
    a = math.radians(-32)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    L, w = R - 6, 4.2
    rule = np.array([c - d * L, c - d * (L - 10) + n * w, c + d * (L - 10) + n * w, c + d * L,
                     c + d * (L - 10) - n * w, c - d * (L - 10) - n * w])
    shape(s, rule, BRASS, LW2 + 0.2)
    s.line([c - d * (L - 10), c + d * (L - 10)], INK, 0.7)
    s.circle(c[0], c[1], 5.6, fill=BRASS_DK, stroke=INK, sw=LW2)
    s.circle(c[0], c[1], 1.8, fill=INK)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Magnifier over a sealed scroll — scrutiny, interpretability
# ---------------------------------------------------------------------------------------------
def magnifier():
    s = canvas()
    ground(s, 122, 206, 96, 6)
    x0, x1, y0, y1 = 40.0, 200.0, 86.0, 168.0
    xs = np.linspace(x0, x1, 60)
    top = np.stack([xs, y0 + 2.2 * np.sin((xs - x0) / 26)], 1)
    bot = np.stack([xs[::-1], y1 + 2.0 * np.sin((xs[::-1] - x0) / 23 + 1)], 1)
    paper = np.concatenate([top, bot])
    shape(s, paper, PARCH)
    rng = np.random.default_rng(3)
    rows = np.arange(y0 + 13, y1 - 6, 8.6)
    for y in rows:
        x_end = x1 - 10 - rng.uniform(0, 46)
        s.line([(x0 + 12, y), (x_end, y)], INK_SOFT, 1.0, op=0.55)
    # rolled ends
    for rx in (x0 - 6, x1 + 6):
        body = np.array([[rx - 8, y0 - 8], [rx + 8, y0 - 8], [rx + 8, y1 + 8], [rx - 8, y1 + 8]])
        shape(s, body, PARCH_DK)
        hatch(s, np.array([[rx + 1, y0 - 8], [rx + 8, y0 - 8], [rx + 8, y1 + 8], [rx + 1, y1 + 8]]),
              angle=90, gap=2.0, op=0.5)
        s.ellipse(rx, y0 - 8, 8, 3.4, fill=PARCH, stroke=INK, sw=LW2 + 0.2)
        s.ellipse(rx, y1 + 8, 8, 3.4, fill=PARCH_DK, stroke=INK, sw=LW2 + 0.2)
        sp = np.array([[rx, y0 - 8]]) + arc((0, 0), 4.6, 0, 540, 80) * np.linspace(1, 0.2, 80)[:, None] * (1, 0.42)
        s.line(sp, INK, 0.8)
    # wax seal with ribbon tails
    sx, sy = 172.0, 152.0
    for dx in (-5, 5):
        tail = np.array([[sx + dx - 3, sy], [sx + dx + 3, sy], [sx + dx * 2.6 + 3, sy + 30], [sx + dx * 2.6, sy + 25],
                         [sx + dx * 2.6 - 3, sy + 30]])
        shape(s, tail, CLAY_LT, LW2)
    th = np.linspace(0, 2 * math.pi, 90, endpoint=False)
    rr = 13 * (1 + 0.06 * np.sin(5 * th + 0.4) + 0.04 * np.sin(9 * th + 1.3))
    blob = np.stack([sx + rr * np.cos(th), sy + rr * np.sin(th)], 1)
    shape(s, blob, CLAY, LW2 + 0.2)
    s.circle(sx, sy, 8.2, fill='none', stroke=CLAY_DK, sw=1.6)
    s.circle(sx - 0.6, sy - 0.6, 8.2, fill='none', stroke=CLAY_LT, sw=0.8, op=0.8)
    for ang in (0, 90, 180, 270):
        s.poly(leaf((sx, sy), ang + 45, 5.6, 3.0)[0], fill=CLAY_DK)
    # magnifying glass
    lc, lr = np.array([104.0, 120.0]), 35.0
    a = math.radians(42)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    p0 = lc + d * (lr + 5)
    hs = np.linspace(0, 64, 80)
    hw = np.interp(hs, [0, 9, 10, 14, 15, 52, 64], [6.4, 6.4, 5.0, 5.0, 5.6, 8.6, 7.6])
    handle = np.concatenate([p0 + np.outer(hs, d) + np.outer(hw, n), (p0 + np.outer(hs, d) - np.outer(hw, n))[::-1]])
    shape(s, handle, WOOD)
    hatch(s, np.concatenate([p0 + np.outer(hs, d), (p0 + np.outer(hs, d) - np.outer(hw, n))[::-1]]),
          angle=math.degrees(a), gap=2.0, op=0.5)
    ferrule = np.array([p0 + n * 6.8, p0 + d * 10 + n * 6.8, p0 + d * 10 - n * 6.8, p0 - n * 6.8])
    shape(s, ferrule, BRASS, LW2 + 0.2)
    s.circle(*(p0 + d * 66), 4.6, fill=WOOD_DK, stroke=INK, sw=LW2)
    lid = s.clip(d_poly(arc(lc, lr, 0, 360, 160)))
    s.open(clip=lid)
    s.circle(lc[0], lc[1], lr, fill='#FBF6EA')
    for y in np.arange(lc[1] - 30, lc[1] + 34, 12.5):
        s.line([(lc[0] - 40, y), (lc[0] + 30 - (y % 7) * 3, y)], INK_SOFT, 2.0, op=0.6)
    s.close()
    s.circle(lc[0], lc[1], lr, fill=GLASS, fop=0.25, stroke='none')
    s.circle(lc[0], lc[1], lr + 3.4, fill='none', stroke=INK, sw=9.4)
    s.circle(lc[0], lc[1], lr + 3.4, fill='none', stroke=BRASS, sw=6.6)
    s.line(arc(lc, lr - 7, 200, 245, 30), '#FFFFFF', 3.0, op=0.9)
    s.line(arc(lc, lr - 7, 252, 262, 10), '#FFFFFF', 3.0, op=0.9)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Armillary sphere — cover hero (300 x 400 viewBox, true 3D rings with depth ordering)
# ---------------------------------------------------------------------------------------------
def _rot(axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _basis(n):
    n = n / np.linalg.norm(n)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def armillary():
    W, H = 300.0, 370.0
    s = Svg(W / 240 * 144, H / 240 * 144, (0, 0, W, H))
    C = np.array([150.0, 156.0])
    R = 104.0
    V = _rot('x', 16) @ _rot('y', -32)

    def P(p3):
        q = np.atleast_2d(p3) @ V.T
        return np.stack([C[0] + q[:, 0], C[1] - q[:, 1]], 1), q[:, 2]

    pieces, ticks = [], []

    def band(normal, r_out, width, center=(0, 0, 0), fill=BRASS, n_ticks=0, n=288, split=36):
        u, v = _basis(np.asarray(normal, float))
        t = np.linspace(0, 2 * math.pi, n + 1)[:, None]
        cen = np.asarray(center, float)
        po, zo = P(cen + r_out * (np.cos(t) * u + np.sin(t) * v))
        pi, zi = P(cen + (r_out - width) * (np.cos(t) * u + np.sin(t) * v))
        step = n // split
        for k in range(split):
            a, b = k * step, min(n, (k + 1) * step + 1)
            pieces.append(dict(z=float((zo[a:b].mean() + zi[a:b].mean()) / 2),
                               poly=np.concatenate([po[a:b], pi[a:b][::-1]]), edges=(po[a:b], pi[a:b]), fill=fill))
        if n_ticks:
            for i in range(0, n, n // n_ticks):
                ticks.append(dict(z=float(zo[i]), seg=np.stack([po[i], pi[i]]), major=(i // (n // n_ticks)) % 3 == 0))

    lat = math.radians(36)
    axis = np.array([0.0, math.sin(lat), math.cos(lat)])
    ecl_n = _rot('x', -23.4) @ axis
    band([1, 0, 0], R * 1.05, R * 0.075, n_ticks=72)                        # meridian (fixed, vertical)
    band([0, 1, 0], R * 1.13, R * 0.10, fill=BRASS_LT, n_ticks=48)          # horizon (broad, flat)
    band(axis, R * 0.95, R * 0.06)                                           # equator
    band(ecl_n, R * 0.95, R * 0.13, fill='#DDB08F', n_ticks=48)             # ecliptic / zodiac band
    for phi, w in ((23.4, 0.03), (-23.4, 0.03), (66.6, 0.028), (-66.6, 0.028)):
        f = math.radians(phi)
        band(axis, R * 0.95 * math.cos(f), R * w, center=axis * R * 0.95 * math.sin(f), split=24)

    # stand: cradle, turned stem, round foot
    ys = np.linspace(C[1] + R * 1.0, 344, 160)
    yy = (ys - ys[0]) / (ys[-1] - ys[0])
    rs = 5 + 9 * np.exp(-((yy - 0.02) / 0.05) ** 2) + 9 * np.exp(-((yy - 0.30) / 0.08) ** 2) + 54 * yy ** 5
    stem = lathe(C[0], ys, rs)
    s.ellipse(C[0], 350, 72, 9, fill=INK, op=0.09)
    shape(s, stem, BRASS)
    hatch(s, np.concatenate([np.stack([C[0] + rs * 0.2, ys], 1), np.stack([C[0] + rs, ys], 1)[::-1]]),
          angle=90, gap=2.3, op=0.5, box=(0, 0, W, H))
    s.ellipse(C[0], 343, 59, 7.0, fill=BRASS_LT, stroke=INK, sw=LW2 + 0.2)

    def draw_piece(pc, back):
        if back:
            s.poly(pc['poly'], fill=BRASS_LT, op=0.6)
            for e in pc['edges']:
                s.line(e, INK_SOFT, 0.75, op=0.6)
        else:
            s.poly(pc['poly'], fill=pc['fill'])
            for e in pc['edges']:
                s.line(e, INK, 1.25)

    def draw_tick(tk, back):
        s.line(tk['seg'], INK_SOFT if back else INK, (0.5 if back else 0.7) * (1.3 if tk['major'] else 1.0),
               op=0.7 if back else 1.0, cap='butt')

    items = [('p', pc) for pc in pieces] + [('t', tk) for tk in ticks]
    items.sort(key=lambda it: it[1]['z'] + (0.001 if it[0] == 't' else 0))
    for kind, it in items:
        if it['z'] < 0:
            (draw_piece if kind == 'p' else draw_tick)(it, True)
    # polar axis and the small earth at the centre
    a2, _ = P(np.stack([-axis * R * 1.24, axis * R * 1.24]))
    s.line(a2, INK, 3.4)
    s.line(a2, BRASS_DK, 1.6)
    for p in a2:
        s.circle(p[0], p[1], 3.6, fill=BRASS, stroke=INK, sw=LW2)
    gr = 25.0
    s.circle(C[0], C[1], gr, fill=PARCH, stroke=INK, sw=LW2 + 0.3)
    gid = s.clip(d_poly(arc(C, gr, 0, 360, 120)))
    s.open(clip=gid)
    for k in (-0.5, 0.0, 0.5):
        s.ellipse(C[0], C[1] + k * gr * 0.9, gr * math.sqrt(1 - (k * 0.9) ** 2), gr * 0.2, fill='none',
                  stroke=INK_SOFT, sw=0.6)
    s.ellipse(C[0], C[1], gr * 0.45, gr, fill='none', stroke=INK_SOFT, sw=0.6)
    lune = np.concatenate([arc(C, gr + 1, -50, 140, 60), arc(C + (-7, -8), gr, 140, -50, 60)])
    hatch(s, lune, angle=-40, gap=2.0, op=0.55, box=(0, 0, W, H))
    s.close()
    for kind, it in items:
        if it['z'] >= 0:
            (draw_piece if kind == 'p' else draw_tick)(it, False)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Laurel wreath, wax seal, section medallion
# ---------------------------------------------------------------------------------------------
def laurel(size=240, leaf_fill=BRASS, vein='#9A7A47', gap_top=26, bow=True, r=86, n_leaves=13):
    s = canvas(size, size)
    c = np.array([size / 2, size / 2 + 4])
    for side in (-1, 1):                       # -1: left branch, +1: right branch (both grow upward)
        a0, a1 = (90 + 13, 270 - gap_top / 2) if side < 0 else (90 - 13, -90 + gap_top / 2)
        angs = np.linspace(a0, a1, 160)
        stem = np.stack([c[0] + r * np.cos(np.radians(angs)), c[1] + r * np.sin(np.radians(angs))], 1)
        s.poly(ribbon(stem, np.linspace(2.8, 0.9, len(stem))), fill=vein)
        tg = np.gradient(stem, axis=0)
        for k, f in enumerate(np.linspace(0.04, 0.93, n_leaves)):
            i = int(f * (len(stem) - 1))
            p, d = stem[i], tg[i] / np.linalg.norm(tg[i])
            h = math.degrees(math.atan2(d[1], d[0]))
            k_sz = 1.0 - 0.42 * f
            for off in (-38, 38):
                lf, mid = leaf(tuple(p + d * (1.8 if off > 0 else -1.8)), h + off, 25 * k_sz, 9.6 * k_sz,
                               bend=14 if off > 0 else -14)
                s.poly(lf, fill=leaf_fill, stroke=vein, sw=0.8)
                s.line(mid[: int(len(mid) * 0.82)], vein, 0.7)
            if k % 3 == 1:
                radial = (p - c) / np.linalg.norm(p - c)
                bp = p + radial * 12 * k_sz + d * 4
                s.circle(bp[0], bp[1], 2.6 * k_sz + 0.6, fill=vein)
        d = tg[-1] / np.linalg.norm(tg[-1])
        lf, mid = leaf(tuple(stem[-1]), math.degrees(math.atan2(d[1], d[0])), 17, 7.0)
        s.poly(lf, fill=leaf_fill, stroke=vein, sw=0.8)
        s.line(mid[: int(len(mid) * 0.8)], vein, 0.7)
    if bow:
        bx, by = c[0], c[1] + r - 1
        for sgn in (-1, 1):
            loop = ellipse_pts((bx + sgn * 12, by - 2), 12, 6.2, sgn * -18, 60)
            s.poly(loop, fill=CLAY, stroke=CLAY_DK, sw=1.0)
            tail = np.array([[bx + sgn * 2, by + 2], [bx + sgn * 8, by + 2], [bx + sgn * 24, by + 26],
                             [bx + sgn * 17, by + 22], [bx + sgn * 15, by + 30]])
            s.poly(tail, fill=CLAY_LT, stroke=CLAY_DK, sw=1.0)
        s.rect(bx - 5, by - 7, 10, 11, rx=2.5, fill=CLAY, stroke=CLAY_DK, sw=1.0)
    return s.tostring()


def seal(size=200, emblem=True):
    s = canvas(size, size)
    c = np.array([size / 2, size / 2])
    R = size * 0.40
    th = np.linspace(0, 2 * math.pi, 240, endpoint=False)
    rr = R * (1 + 0.035 * np.sin(5 * th + 0.7) + 0.025 * np.sin(9 * th + 2.1) + 0.018 * np.sin(14 * th)
              + 0.06 * np.exp(-((th - 4.0) / 0.18) ** 2) + 0.05 * np.exp(-((th - 0.9) / 0.14) ** 2))
    blob = np.stack([c[0] + rr * np.cos(th), c[1] + rr * np.sin(th)], 1)
    s.poly(blob + (1.6, 2.2), fill=INK, op=0.12)
    s.poly(blob, fill=CLAY, stroke=CLAY_DK, sw=1.6)
    s.circle(c[0], c[1], R * 0.74, fill=CLAY_DK, fop=0.22, stroke=CLAY_DK, sw=3.2)
    s.circle(c[0] - 0.9, c[1] - 0.9, R * 0.74, fill='none', stroke=CLAY_LT, sw=1.2, op=0.9)
    s.circle(c[0], c[1], R * 0.66, fill='none', stroke=CLAY_DK, sw=1.0, op=0.8)
    for k in range(36):
        a = math.radians(k * 10)
        p = c + R * 0.70 * np.array([math.cos(a), math.sin(a)])
        s.circle(p[0], p[1], 1.1, fill=CLAY_DK)
    if emblem:
        for dx, col, op in ((-0.9, CLAY_LT, 0.9), (0.6, CLAY_DK, 1.0)):
            s.open(op=op)
            for ang in (0, 90, 180, 270):
                s.poly(leaf((c[0] + dx, c[1] + dx), ang, R * 0.46, R * 0.26)[0], fill=col)
            for ang in (45, 135, 225, 315):
                s.poly(leaf((c[0] + dx, c[1] + dx), ang, R * 0.30, R * 0.13)[0], fill=col)
            s.circle(c[0] + dx, c[1] + dx, R * 0.1, fill=col)
            s.close()
    s.line(arc(c, R * 0.88, 200, 255, 40), CLAY_LT, 3.0, op=0.55)
    return s.tostring()


def medallion(size=240):
    """Double gilt ring with bead circle and laurel sprigs; the numeral goes on top as live text."""
    s = canvas(size, size)
    c = np.array([size / 2, size / 2 - 8])
    R = size * 0.30
    g, gd = '#B39363', '#8B6E42'
    s.circle(c[0], c[1], R, fill='none', stroke=g, sw=2.2)
    s.circle(c[0], c[1], R - 6.5, fill='none', stroke=g, sw=0.9)
    for k in range(48):
        a = math.radians(k * 7.5)
        p = c + (R - 3.25) * np.array([math.cos(a), math.sin(a)])
        s.circle(p[0], p[1], 0.95, fill=g)
    for side in (-1, 1):
        angs = np.linspace(90 - side * 8, 90 - side * 82, 90)
        rr = R + 13
        stem = np.stack([c[0] + rr * np.cos(np.radians(angs)), c[1] + rr * np.sin(np.radians(angs))], 1)
        s.poly(ribbon(stem, np.linspace(2.0, 0.7, len(stem))), fill=gd)
        tg = np.gradient(stem, axis=0)
        for k, f in enumerate(np.linspace(0.08, 0.9, 6)):
            i = int(f * (len(stem) - 1))
            d = tg[i] / np.linalg.norm(tg[i])
            h = math.degrees(math.atan2(d[1], d[0]))
            for j, off in enumerate((-36, 36)):
                lf, _ = leaf(tuple(stem[i]), h + off, 15 * (1 - 0.35 * f), 5.8 * (1 - 0.35 * f),
                             bend=(12 if j else -12))
                s.poly(lf, fill=g)
    s.circle(c[0], c[1] + R + 13, 2.6, fill=gd)
    return s.tostring()
