"""Procedural manuscript ornaments, drawn as SVG in the template's gilt.

Units: 120 user units = 1 inch, so art placed at its natural size stays on the template grid.
"""
import math

import numpy as np

from . import tokens as T
from .geom import (curve, leaf, mirror_diag, resample, ribbon, tangents)
from .svg import Svg

U = 120.0  # user units per inch
GILT, GILT_DEEP = '#' + T.GILT, '#' + T.GILT_DEEP


def pen(pts, thin, thick, angle=-30.0, end_taper=0.0):
    """Broad-nib modulation: thick across the nib, thin along it; optional taper at the end."""
    t = tangents(pts)
    th = np.arctan2(t[:, 1], t[:, 0])
    w = thin + (thick - thin) * np.abs(np.sin(th - math.radians(angle)))
    if end_taper:
        u = np.linspace(0, 1, len(pts))
        w *= np.clip((1 - u) / end_taper, 0, 1) ** 0.6 * 0.75 + 0.25
    return w


def spiral(p0, heading, length, r0, r1, sign, step=0.3):
    """Volute: curvature radius shrinks from r0 to r1 over `length`."""
    return curve(p0, heading, length, lambda t: sign / (r0 + (r1 - r0) * t ** 0.9), step)


# ---------------------------------------------------------------------------------------------
#  Corner: frame lines that wind into volutes around a gothic rosette
# ---------------------------------------------------------------------------------------------
OUT, INN = 20.0, 25.5      # frame line offsets inside the corner art (art units, before scaling)
LW_OUT, LW_INN = 1.3, 0.75


def _corner_half():
    shapes = []
    x0 = 57.0
    a = resample(np.array([[110, OUT], [x0, OUT]]), 0.5)[:-1]
    v = spiral((x0, OUT), 180, 74, 16.5, 2.0, -1)
    arm = np.concatenate([a, v])
    w = pen(arm, LW_OUT, 3.8, angle=-30, end_taper=0.2)
    w[:len(a)] = LW_OUT
    shapes.append(ribbon(arm, w))
    b = resample(np.array([[110, INN], [68, INN]]), 0.5)[:-1]
    hk = spiral((68, INN), 180, 19, 8.5, 2.4, -1)
    shapes.append(ribbon(np.concatenate([b, hk]),
                         np.concatenate([np.full(len(b), LW_INN), np.linspace(LW_INN, 1.7, len(hk))])))
    i = int(np.argmin(np.abs(v[:, 1] - (OUT + 9.0)) + (v[:, 0] > x0) * 99))
    sprout, _ = leaf(tuple(v[i] + (-1.2, 0)), 200, 10.5, 3.8, bend=-30)
    shapes.append(sprout)
    return shapes


def corner_shapes():
    """Polygons + circles of the top-left corner (art units, box 110 x 110)."""
    polys = _corner_half()
    polys += [mirror_diag(p) for p in polys]
    cl, _ = leaf((39.0, 39.0), 45, 19, 5.6)
    polys.append(cl)
    c = (22.5, 22.5)
    for ang in (0, 90, 180, 270):
        polys.append(leaf(c, ang, 9.2, 5.4)[0])
    for ang in (45, 135, 225, 315):
        polys.append(leaf(c, ang, 6.0, 2.8)[0])
    dots = [(c[0], c[1], 2.3, GILT), (c[0], c[1], 1.0, GILT_DEEP), (34.6, 34.6, 1.5, GILT)]
    return polys, dots


def _emit(svg, polys, dots, tf, k):
    """Gilt fill over a faint offset shadow; light always comes from the top-left."""
    for pts in polys:
        svg.poly(tf(pts) + (0.35 * k, 0.45 * k), fill=GILT_DEEP, op=0.5)
    for pts in polys:
        svg.poly(tf(pts), fill=GILT)
    for x, y, r, col in dots:
        p = tf(np.array([[x, y]]))[0]
        svg.circle(p[0], p[1], r * k, fill=col)


def frame(w_in=T.W, h_in=T.H, k=1.35, corners=True):
    """Full-slide double-rule frame with ornamental corners. Returns SVG string."""
    W, H = w_in * U, h_in * U
    s = Svg(w_in * 96, h_in * 96, (0, 0, W, H))
    o, i = OUT * k, INN * k
    reach = 110 * k if corners else o
    for off, lw in ((o, LW_OUT * k), (i, LW_INN * k)):
        a = reach if corners else off
        s.line([(a, off), (W - a, off)], GILT, lw, cap='butt')
        s.line([(a, H - off), (W - a, H - off)], GILT, lw, cap='butt')
        s.line([(off, a), (off, H - a)], GILT, lw, cap='butt')
        s.line([(W - off, a), (W - off, H - a)], GILT, lw, cap='butt')
    if corners:
        polys, dots = corner_shapes()
        for fx, fy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            ox, oy = (0 if fx > 0 else W), (0 if fy > 0 else H)
            tf = (lambda fx, fy, ox, oy: lambda p: np.asarray(p) * (k * fx, k * fy) + (ox, oy))(fx, fy, ox, oy)
            _emit(s, polys, dots, tf, k)
    return s.tostring()


# ---------------------------------------------------------------------------------------------
#  Dividers and small marks
# ---------------------------------------------------------------------------------------------
def divider(width_in=2.6, color=None):
    """Hairline – volutes – lozenge – volutes – hairline."""
    col = color or GILT
    W, Hh = width_in * U, 16.0
    s = Svg(width_in * 96, Hh / U * 96, (0, 0, W, Hh))
    cy, cx = Hh / 2, W / 2
    gap = 15.0
    for sgn in (1, -1):
        x_in = cx + sgn * gap
        s.line([(x_in + sgn * 9, cy), (cx + sgn * (W / 2 - 1), cy)], col, 0.8, cap='butt')
        sp = spiral((x_in + sgn * 9, cy), 180 if sgn > 0 else 0, 15, 4.2, 1.2, -sgn)
        s.poly(ribbon(sp, np.linspace(0.8, 1.5, len(sp))), fill=col)
    lz = np.array([[cx - 5.5, cy], [cx, cy - 4.2], [cx + 5.5, cy], [cx, cy + 4.2]])
    s.poly(lz, fill=col)
    s.circle(cx, cy, 1.1, fill='#' + T.PAPER)
    return s.tostring()


def rosette(d_in=0.32, color=None, center=None):
    """Eight-petal rosette used as a bullet/section mark."""
    col = color or GILT
    R = d_in * U / 2
    s = Svg(d_in * 96, d_in * 96, (-R, -R, 2 * R, 2 * R))
    for ang in (0, 90, 180, 270):
        s.poly(leaf((0, 0), ang, R * 0.98, R * 0.58)[0], fill=col)
    for ang in (45, 135, 225, 315):
        s.poly(leaf((0, 0), ang, R * 0.64, R * 0.30)[0], fill=col)
    s.circle(0, 0, R * 0.24, fill=col)
    s.circle(0, 0, R * 0.11, fill=center or GILT_DEEP)
    return s.tostring()


def bookmark(w_in=0.46, h_in=1.05):
    """Silk bookmark hanging from the top frame (marks backup / appendix slides)."""
    W, H = w_in * U, h_in * U
    s = Svg(w_in * 96, h_in * 96, (0, 0, W, H))
    notch = W * 0.42
    body = np.array([[0, 0], [W, 0], [W, H], [W / 2, H - notch], [0, H]])
    s.poly(body + (0.8, 1.0), fill='#' + T.INK, op=0.12)
    s.poly(body, fill='#' + T.RUBRIC)
    s.poly(np.array([[W * 0.72, 0], [W, 0], [W, H], [W * 0.72, H - notch * 0.44]]), fill='#7E3A27', op=0.35)
    for off in (3.2, W - 3.2):
        s.line([(off, 0), (off, H - (notch * (off / (W / 2)) if off < W / 2 else notch * ((W - off) / (W / 2))) - 3)],
               '#E8C9B4', 0.6, dash='1.6 1.6', op=0.8)
    return s.tostring()
