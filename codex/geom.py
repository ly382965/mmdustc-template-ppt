"""Vector geometry for procedural ornaments: curvature-integrated scrolls, tapered strokes, leaves.

All coordinates are SVG user units (y grows downward). Shapes are returned as numpy point arrays
and turned into SVG path data with `d_poly` / `d_line`.
"""
import math

import numpy as np


def fmt(v, nd=2):
    s = ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


def d_poly(pts, closed=True, nd=2):
    pts = np.asarray(pts, float)
    head = 'M%s %s' % (fmt(pts[0, 0], nd), fmt(pts[0, 1], nd))
    body = ''.join('L%s %s' % (fmt(x, nd), fmt(y, nd)) for x, y in pts[1:])
    return head + body + ('Z' if closed else '')


def d_line(pts, nd=2):
    return d_poly(pts, closed=False, nd=nd)


def resample(pts, step):
    pts = np.asarray(pts, float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(2, int(math.ceil(s[-1] / step)) + 1)
    t = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], 1)


def tangents(pts):
    d = np.gradient(np.asarray(pts, float), axis=0)
    return d / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-12)


def ribbon(pts, widths, caps=(True, True), cap_n=10):
    """Closed outline of a stroke along `pts` whose width varies per point (calligraphic taper)."""
    pts = np.asarray(pts, float)
    w = np.broadcast_to(np.asarray(widths, float), (len(pts),)) / 2.0
    t = tangents(pts)
    n = np.stack([-t[:, 1], t[:, 0]], 1)
    left, right = pts + n * w[:, None], pts - n * w[:, None]
    parts = [left]
    if caps[1] and w[-1] > 0.05:
        a0 = math.atan2(n[-1, 1], n[-1, 0])
        a = np.linspace(a0, a0 - math.pi, cap_n)[1:-1]
        parts.append(pts[-1] + w[-1] * np.stack([np.cos(a), np.sin(a)], 1))
    parts.append(right[::-1])
    if caps[0] and w[0] > 0.05:
        a0 = math.atan2(-n[0, 1], -n[0, 0])
        a = np.linspace(a0, a0 - math.pi, cap_n)[1:-1]
        parts.append(pts[0] + w[0] * np.stack([np.cos(a), np.sin(a)], 1))
    return np.concatenate(parts)


def curve(p0, heading, length, kfun, step=0.4):
    """Integrate a curve from p0 with initial heading (degrees) and curvature kfun(t), t in [0, 1]."""
    n = max(3, int(length / step) + 1)
    ds = length / (n - 1)
    th = math.radians(heading)
    x, y = p0
    out = [(x, y)]
    for i in range(1, n):
        th += kfun((i - 0.5) / (n - 1)) * ds
        x += math.cos(th) * ds
        y += math.sin(th) * ds
        out.append((x, y))
    return np.array(out)


def cubic(p0, p1, p2, p3, n=80):
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def arc(c, r, a0, a1, n=None, ry=None):
    """Arc from a0 to a1 degrees around c (ellipse when ry given)."""
    n = n or max(8, int(abs(a1 - a0) / 2))
    a = np.radians(np.linspace(a0, a1, n))
    return np.stack([c[0] + r * np.cos(a), c[1] + (ry or r) * np.sin(a)], 1)


def leaf(base, angle, length, width, bend=0.0, fat=0.42, step=0.35):
    """Almond leaf from `base` pointing at `angle` degrees; bend = total turn in degrees."""
    k = math.radians(bend) / max(length, 1e-6)
    c = curve(base, angle - bend / 2, length, lambda t: k, step)
    n = len(c)
    t = np.linspace(0.0, 1.0, n)
    w = width * np.where(t < fat, np.sin(np.clip(t / fat, 0, 1) * math.pi / 2) ** 0.7,
                         np.cos(np.clip((t - fat) / (1 - fat), 0, 1) * math.pi / 2) ** 0.9)
    return ribbon(c, w, caps=(False, False)), c


def mirror_diag(pts):
    pts = np.asarray(pts, float)
    return pts[:, ::-1].copy()


def rotate(pts, deg, c=(0.0, 0.0)):
    a = math.radians(deg)
    m = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return (np.asarray(pts, float) - c) @ m.T + c


def ellipse_pts(c, rx, ry, rot=0.0, n=180):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    p = np.stack([rx * np.cos(a), ry * np.sin(a)], 1)
    return rotate(p, rot) + np.asarray(c, float)
