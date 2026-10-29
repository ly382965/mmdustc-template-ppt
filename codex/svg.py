"""Minimal SVG document builder + resvg rasterizer (PNG fallback for PowerPoint's svgBlip)."""
import re

from .geom import d_poly, d_line, fmt


class Svg:
    def __init__(self, w, h, vb=None):
        self.w, self.h = w, h
        self.vb = vb or (0, 0, w, h)
        self.defs, self.body = [], []
        self._n = 0

    def uid(self, prefix='k'):
        self._n += 1
        return '%s%d' % (prefix, self._n)

    # -- primitives ---------------------------------------------------------------------------
    @staticmethod
    def _attrs(fill='none', stroke=None, sw=None, op=None, fop=None, sop=None, cap='round', join='round',
               dash=None, clip=None, rule=None, transform=None):
        a = ['fill="%s"' % fill]
        if stroke:
            a += ['stroke="%s"' % stroke, 'stroke-width="%s"' % fmt(sw or 1),
                  'stroke-linecap="%s"' % cap, 'stroke-linejoin="%s"' % join]
            if dash:
                a.append('stroke-dasharray="%s"' % dash)
        if op is not None:
            a.append('opacity="%s"' % fmt(op, 3))
        if fop is not None:
            a.append('fill-opacity="%s"' % fmt(fop, 3))
        if sop is not None:
            a.append('stroke-opacity="%s"' % fmt(sop, 3))
        if clip:
            a.append('clip-path="url(#%s)"' % clip)
        if rule:
            a.append('fill-rule="%s"' % rule)
        if transform:
            a.append('transform="%s"' % transform)
        return ' '.join(a)

    def path(self, d, **kw):
        self.body.append('<path d="%s" %s/>' % (d, self._attrs(**kw)))

    def poly(self, pts, closed=True, **kw):
        self.path(d_poly(pts, closed) if closed else d_line(pts), **kw)

    def line(self, pts, stroke, sw, **kw):
        self.path(d_line(pts), stroke=stroke, sw=sw, **kw)

    def circle(self, cx, cy, r, **kw):
        self.body.append('<circle cx="%s" cy="%s" r="%s" %s/>' % (fmt(cx), fmt(cy), fmt(r), self._attrs(**kw)))

    def ellipse(self, cx, cy, rx, ry, rot=0, **kw):
        t = (' transform="rotate(%s %s %s)"' % (fmt(rot), fmt(cx), fmt(cy))) if rot else ''
        self.body.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s %s/>' % (
            fmt(cx), fmt(cy), fmt(rx), fmt(ry), t, self._attrs(**kw)))

    def rect(self, x, y, w, h, rx=0, **kw):
        self.body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" %s/>' % (
            fmt(x), fmt(y), fmt(w), fmt(h), fmt(rx), self._attrs(**kw)))

    def clip(self, d):
        cid = self.uid('c')
        self.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, d))
        return cid

    def raw(self, s):
        self.body.append(s)

    def open(self, transform=None, op=None, clip=None, fill=None):
        a = []
        if transform:
            a.append('transform="%s"' % transform)
        if op is not None:
            a.append('opacity="%s"' % fmt(op, 3))
        if clip:
            a.append('clip-path="url(#%s)"' % clip)
        if fill:
            a.append('fill="%s"' % fill)
        self.body.append('<g %s>' % ' '.join(a))

    def close(self):
        self.body.append('</g>')

    def tostring(self):
        vb = ' '.join(fmt(v) for v in self.vb)
        defs = ('<defs>%s</defs>' % ''.join(self.defs)) if self.defs else ''
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="%s">%s%s</svg>'
                % (fmt(self.w), fmt(self.h), vb, defs, '\n'.join(self.body)))


def svg_size(svg):
    """(width, height) in SVG px from the root element (pt/in/px understood)."""
    head = svg[:2000]
    def dim(name):
        m = re.search(r'\b%s\s*=\s*["\']([0-9.]+)\s*(pt|px|in|mm)?["\']' % name, head)
        v, u = float(m.group(1)), (m.group(2) or 'px')
        return v * {'px': 1, 'pt': 4 / 3, 'in': 96, 'mm': 96 / 25.4}[u]
    return dim('width'), dim('height')


def rasterize(svg, width_px):
    """PNG bytes of `svg` rendered at `width_px` wide with transparent background."""
    import resvg_py
    w, h = svg_size(svg)
    # resvg wants plain px sizes on the root
    svg = re.sub(r'(<svg[^>]*?)\bwidth\s*=\s*["\'][^"\']*["\']', r'\g<1>width="%s"' % fmt(w, 3), svg, count=1)
    svg = re.sub(r'(<svg[^>]*?)\bheight\s*=\s*["\'][^"\']*["\']', r'\g<1>height="%s"' % fmt(h, 3), svg, count=1)
    png = resvg_py.svg_to_bytes(svg_string=svg, width=int(width_px), skip_system_fonts=True)
    return bytes(png)
