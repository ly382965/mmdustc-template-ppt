"""Page types of the Codex template. Each builder takes structured content and lays it out on the
fixed grid from tokens.py; the shape names (Chinese) tell an editor/AI what each box is for.

Every content page has the same head: kicker (e.g. 'Part I：研究背景') + one-line assertion title.
The bottom-left corner is reserved for references (`refs`) and nothing else."""
import re

from . import art, illus, logos, mathtex, metrics, paper
from . import tokens as T
from .pptkit import Deck, P, R
from .svg import svg_size

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
ILLUS = {'hourglass': illus.hourglass, 'scales': illus.scales, 'astrolabe': illus.astrolabe,
         'magnifier': illus.magnifier, 'armillary': illus.armillary, 'laurel': illus.laurel,
         'seal': illus.seal}
KEYWORDS = r'\b(for|each|end|if|else|then|while|do|return|repeat|until|in|to)\b|输入|输出|返回'
MARKS = {'yes': ('●', T.INK), 'part': ('◐', T.GILT_DEEP), 'no': ('○', T.FAINT)}


class Codex:
    def __init__(self, title='', author=''):
        self.title, self.author = title, author
        d = self.d = Deck()
        d.set_theme()
        d.set_background(d.prs.slide_master, paper.parchment())
        frame = art.frame()
        badge = logos.mark('ustc-badge', T.GILT_DEEP)

        def framed(c):
            c.svg(frame, 0, 0, T.W, T.H, name='装饰 · 边框')

        def content(c):
            framed(c)
            c.svg(badge, T.MR - 0.5, 0.5, 0.5, name='装饰 · 校徽')
            c.text(T.MR - 1.2, T.FOOT_Y - 0.02, 1.2, 0.3,
                   P(R('#', 'num', 12, T.MUTED, field='slidenum'), align='r'), name='页码')

        d.add_layout('封面', framed)
        d.add_layout('正文', content)
        d.add_layout('章节', framed)
        d.add_layout('结束', framed)

    def save(self, path):
        import datetime
        cp = self.d.prs.core_properties
        now = datetime.datetime.now().replace(microsecond=0)
        cp.title, cp.author, cp.last_modified_by = self.title, self.author, self.author
        cp.comments, cp.revision, cp.created, cp.modified = 'mmdustc Codex template', 1, now, now
        self.d.save(path)

    # ---- shared pieces ---------------------------------------------------------------------
    def page(self, kicker=None, title=None, refs=None, layout='正文', width=T.CW - 0.8):
        """New slide with the standard head and the bottom-left reference slot."""
        c = self.d.slide(layout)
        if kicker:
            c.text(T.ML, T.KICKER_Y, width, 0.3, P(R(kicker, 'kicker', 12, T.RUBRIC, spc=300)), name='眉题')
        if title:
            c.text(T.ML, T.TITLE_Y, width, 0.62, P(R(title, 'title', 28, T.INK)), name='标题')
        if refs:
            refs = [refs] if isinstance(refs, str) else list(refs)
            lh = 0.2
            y = T.FOOT_Y + 0.03 - lh * (len(refs) - 1)
            c.text(T.ML, y, T.CW - 1.4, lh * len(refs) + 0.05,
                   [P(R(r, 'body', 9.5, T.MUTED), exact=14) for r in refs], name='参考文献')
        return c

    @staticmethod
    def numeral_ring(c, cx, cy, n, d=0.5, size=15, color=T.INK, fill=None):
        c.oval(cx - d / 2, cy - d / 2, d, d, fill=fill, line=T.TEXT, lw=0.75, name='序号圈')
        c.text(cx - d / 2, cy - d / 2, d, d, P(R(ROMAN[n], 'num', size, color), align='c'), anchor='m',
               name='序号')

    @staticmethod
    def plate(c, x, y, w, h):
        """Mounted-print frame: pale mount, gilt double rule."""
        c.rect(x, y, w, h, fill='FBF8F1', line=T.GILT, lw=1.0, name='图版外框')
        c.rect(x + 0.07, y + 0.07, w - 0.14, h - 0.14, line=T.GILT, lw=0.5, name='图版内框')

    @staticmethod
    def booktabs(c, x, y, columns, rows, width, cell, ours=None, row_h=(0.56, 0.54), name='表格'):
        """Three-rule table; column widths measured from content, numeric-looking columns equalised."""
        pad = 0.24 + 0.16
        n = len(columns)
        nat = [max(metrics.width(str(v), 13.5, 'title') for v in [columns[ci]] + [r[ci] for r in rows]) + pad
               for ci in range(n)]
        numeric = [ci > 0 and all(re.fullmatch(r'[\s+\-−–—.,%\d●◐○]*', str(r[ci])) for r in rows)
                   for ci in range(n)]
        num_w = max([nat[ci] for ci in range(n) if numeric[ci]] or [0])
        nat = [num_w if numeric[ci] else nat[ci] for ci in range(n)]
        extra = width - sum(nat)
        col_w = [v + extra / n for v in nat] if extra >= 0 else [v * width / sum(nat) for v in nat]
        heights = [row_h[0]] + [row_h[1]] * len(rows)
        cells = [[cell(h, -1, ci) for ci, h in enumerate(columns)]]
        cells += [[cell(v, r, ci) for ci, v in enumerate(row)] for r, row in enumerate(rows)]
        c.table(x, y, col_w, heights, cells, name=name,
                borders={(0, 'T'): (T.INK, 1.25), (0, 'B'): (T.INK, 0.6), (len(rows), 'B'): (T.INK, 1.25)},
                fills={ours + 1: T.RUBRIC_TINT} if ours is not None else {}, margins=(0.12, 0.04))
        return sum(heights)

    def side_points(self, c, x, y, points, size=13.5, step=1.42, numerals=True):
        """Numbered (or rosette-marked) lead + two-line detail, separated by hairlines."""
        w = T.MR - x
        for k, (lead, detail) in enumerate(points):
            if numerals:
                c.text(x, y - 0.04, 0.55, 0.45, P(R(ROMAN[k], 'num', 20, T.RUBRIC)), name='序号')
            else:
                c.svg(art.rosette(0.22), x + 0.04, y + 0.09, 0.22, name='装饰 · 条目')
            dw = w - 0.55
            c.text(x + 0.55, y, dw, 0.4, P(R(lead, 'head', 16.5, T.INK)), name='要点')
            c.text(x + 0.55, y + 0.46, dw, 0.72, P(R(metrics.tidy(detail, dw, size, 'body', balance=True), 'body',
                                                    size, T.MUTED), line=1.1), name='要点说明')
            if k < len(points) - 1:
                c.line(x + 0.55, y + step - 0.18, T.MR, y + step - 0.18, T.RULE, 0.75, name='分隔线')
            y += step

    # ---- 1 cover ---------------------------------------------------------------------------
    def cover(self, kicker, title_lines, title_en, affiliation, presenter, date, advisor, hero='armillary'):
        c = self.d.slide('封面')
        c.svg(logos.mark('ustc-badge', T.INK), 0.98, 0.8, 0.62, name='校徽')
        c.svg(logos.mark('ustc-name', T.INK), 1.76, 0.96, h=0.3, name='校名')
        c.line(4.33, 0.84, 4.33, 1.38, T.GILT, 0.75, name='分隔线')
        c.svg(logos.lab(T.INK), 4.6, 0.91, h=0.4, name='实验室标识')
        x, w = T.ML + 0.12, 7.3
        M = metrics
        c.text(x, 2.28, w, 0.32, P(R(kicker, 'kicker', 13, T.RUBRIC, spc=400)), name='眉题')
        th = len(title_lines) * M.line_height(42, 'title', 0.97)
        c.text(x, 2.66, w, th + 0.1, [P(R(t, 'title', 42, T.INK), line=0.97) for t in title_lines], name='主标题')
        y = 2.66 + th + 0.16
        en = M.tidy(title_en, w, 20, 'num', balance=True)
        eh = M.text_height(en, w, 20, 'num', 1.0)
        c.text(x, y, w, eh + 0.05, P(R(en, 'num', 20, T.MUTED)), name='英文标题')
        y += eh + 0.36
        c.svg(art.divider(2.5), x, y, 2.5, name='装饰 · 分隔')
        y += 0.36
        c.text(x, y, w, 0.38, P([R(affiliation, 'body', 15, T.TEXT), R('　' + presenter, 'head', 15, T.INK)]),
               name='单位与汇报人')
        c.text(x, y + 0.46, w, 0.3, P(R('%s　·　指导老师　%s' % (date, advisor), 'body', 13, T.MUTED)),
               name='日期与指导老师')
        svg = ILLUS[hero]()
        sw, sh = svg_size(svg)
        h = 5.45
        c.svg(svg, 12.55 - h * sw / sh, 1.0, h=h, name='插画')
        return c

    # ---- 2 table of contents -------------------------------------------------------------------
    def art_in(self, c, key, cx, top, box, name='插画'):
        """Illustration `key` fitted (contain) in a square box centred on cx."""
        svg = ILLUS[key]()
        sw, sh = svg_size(svg)
        k = box / max(sw, sh)
        w, h = sw * k, sh * k
        c.svg(svg, cx - w / 2, top + (box - h) / 2, w, h, name=name)

    def toc(self, items):
        """items: [dict(title, art, pages=(first, last))], 3-5 parts. Words are only the part names: what
        each part is about is carried by its illustration, how long it is by the row of page marks."""
        self.outline = items
        c = self.page('目录')
        n = len(items)
        colw = T.CW / n
        ly = 2.35                                   # the journey line the numerals sit on
        centers = [T.ML + colw * (k + 0.5) for k in range(n)]
        c.line(centers[0], ly, centers[-1], ly, T.GILT, 1.0, name='章节连线')
        for k, it in enumerate(items):
            cx = centers[k]
            self.numeral_ring(c, cx, ly, k, d=0.6, size=19, color=T.RUBRIC, fill=T.PAPER)
            self.art_in(c, it['art'], cx, 2.93, 1.8)
            c.line(cx - 0.55, 4.95, cx + 0.55, 4.95, T.RULE, 0.75, name='分隔线')
            c.text(cx - colw / 2, 5.07, colw, 0.5, P(R(it['title'], 'head', 22, T.INK), align='c'), name='章节名')
            first, last = it['pages']
            m, d, g = last - first + 1, 0.11, 0.09        # one gilt lozenge per slide of the part
            x = cx - (m * d + (m - 1) * g) / 2
            for j in range(m):
                c.shape('diamond', x + j * (d + g), 5.78, d, d, fill=T.GILT, name='页数标记')
            rng = str(first) if first == last else '%d – %d' % (first, last)
            c.text(cx - colw / 2, 6.01, colw, 0.32, P(R(rng, 'num', 13, T.FAINT), align='c'), name='页码')
        return c

    # ---- 3 section divider -----------------------------------------------------------------------
    def section(self, index, title, art=None):
        """index: current part (0-based). The part's illustration (from the TOC outline unless `art` is
        given) sits in the medallion; the bead row below shows done / current / ahead without words."""
        c = self.d.slide('章节')
        outline = getattr(self, 'outline', None) or []
        art = art or (outline[index]['art'] if index < len(outline) else 'armillary')
        md = 2.75
        mx, my = (T.W - md) / 2, 0.72
        c.svg(illus.medallion(), mx, my, md, name='装饰 · 章节徽章')
        rcx, rcy = mx + md / 2, my + md * 112 / 240
        self.art_in(c, art, rcx, rcy - 0.66, 1.32)
        c.text(1.5, 3.62, T.W - 3, 0.34, P(R('Part %s' % ROMAN[index], 'kicker', 14, T.RUBRIC, spc=400), align='c'),
               name='眉题')
        c.text(1.5, 4.0, T.W - 3, 0.72, P(R(title, 'title', 32, T.INK), align='c'), name='章节标题')
        n = max(len(outline), index + 1)
        gap, py = 1.0, 5.55
        xs = [T.W / 2 + (k - (n - 1) / 2) * gap for k in range(n)]
        c.line(xs[0], py, xs[-1], py, T.GILT, 1.0, name='进度连线')
        for k, x in enumerate(xs):
            if k < index:            # done: gilt bead
                d, fill, ring, col = 0.42, T.GILT, T.GILT, 'FBF8F1'
            elif k == index:         # here: rubric seal, larger
                d, fill, ring, col = 0.58, T.RUBRIC, T.RUBRIC, 'FBF8F1'
            else:                    # ahead: open ring
                d, fill, ring, col = 0.42, T.PAPER, T.FAINT, T.FAINT
            c.oval(x - d / 2, py - d / 2, d, d, fill=fill, line=ring, lw=0.75, name='进度节点')
            c.text(x - d / 2, py - d / 2, d, d, P(R(ROMAN[k], 'num', 15 if k == index else 12, col), align='c'),
                   anchor='m', name='进度序号')
        return c

    # ---- 4 figure + text -------------------------------------------------------------------------
    def figure_text(self, kicker, title, image, caption, points, label='图 1', refs=None):
        c = self.page(kicker, title, refs)
        px, py, pw, ph = T.ML, T.BODY_Y + 0.05, 6.3, 4.05
        self.plate(c, px, py, pw, ph)
        c.image(image, px + 0.2, py + 0.2, pw - 0.4, ph - 0.4, name='图片', fit='contain')
        c.text(px, py + ph + 0.12, pw, 0.3, P([R(label + '　', 'head', 11.5, T.RUBRIC), R(caption, 'kai', 12.5, T.MUTED)]),
               name='图注')
        x = 7.62
        w = T.MR - x
        y = py + 0.12
        for k, (lead, detail) in enumerate(points):
            c.svg(art.rosette(0.22), x, y + 0.09, 0.22, name='装饰 · 条目')
            c.text(x + 0.38, y, w - 0.38, 0.42, P(R(lead, 'head', 17, T.INK)), name='要点')
            dw = w - 0.38
            c.text(x + 0.38, y + 0.47, dw, 0.75, P(R(metrics.tidy(detail, dw, 13.5, 'body', balance=True), 'body', 13.5,
                                                     T.MUTED), line=1.1), name='要点说明')
            y += 1.36
        return c

    # ---- 5 method architecture --------------------------------------------------------------
    def architecture(self, kicker, title, inputs, stages, bracket=None, refs=None):
        """inputs = (title, [items], sub); stages = [dict(title, sub, chips)]; bracket = (first, last, text)
        spans stage indices first..last with a dashed gilt brace and a note."""
        c = self.page(kicker, title, refs)
        y0, bh, iw, gap = 2.2, 3.0, 1.95, 0.5
        sw = (T.CW - iw - gap * len(stages)) / len(stages)
        chip = dict(r=0.12, fill='FBF8F1', line=T.RULE, lw=0.75, inset=(0.04, 0, 0.04, 0))
        x = T.ML
        c.rrect(x, y0, iw, bh, r=0.03, line=T.GILT, lw=1.0, dash='dash', name='输入框')
        c.text(x, y0 + 0.34, iw, 0.4, P(R(inputs[0], 'head', 16, T.INK), align='c'), name='输入标题')
        if len(inputs) > 2:
            c.text(x, y0 + 0.72, iw, 0.3, P(R(inputs[2], 'body', 11.5, T.MUTED), align='c'), name='输入说明')
        for k, item in enumerate(inputs[1]):
            c.rrect(x + 0.16, y0 + 1.1 + k * 0.6, iw - 0.32, 0.46, name='输入项',
                    paras=[P(R(item, 'body', 12, T.TEXT), align='c')], **chip)
        boxes = [(x, iw)]
        x += iw + gap
        for k, st in enumerate(stages):
            c.rrect(x, y0, sw, bh, r=0.03, fill=T.CARD, line=T.CARD_LINE, name='模块')
            self.numeral_ring(c, x + sw / 2, y0, k, d=0.46, size=14, fill=T.PAPER)
            c.text(x, y0 + 0.34, sw, 0.4, P(R(st['title'], 'head', 16, T.INK), align='c'), name='模块名')
            c.text(x, y0 + 0.72, sw, 0.3, P(R(st['sub'], 'body', 11.5, T.MUTED), align='c'), name='模块说明')
            for j, item in enumerate(st['chips']):
                c.rrect(x + 0.18, y0 + 1.1 + j * 0.6, sw - 0.36, 0.46, name='子模块',
                        paras=[P(R(item, 'body', 12, T.TEXT), align='c')], **chip)
            boxes.append((x, sw))
            x += sw + gap
        ay = y0 + bh / 2
        for (x1, w1), (x2, _) in zip(boxes, boxes[1:]):
            c.line(x1 + w1 + 0.08, ay, x2 - 0.08, ay, T.INK, 1.0, tail='triangle', name='箭头')
        if bracket:
            a, b, text = bracket
            xa, xb = boxes[a + 1][0], boxes[b + 1][0] + boxes[b + 1][1]
            by = y0 + bh + 0.32
            c.line(xa, by, xb, by, T.GILT, 1.0, dash='dash', name='括注线')
            c.line(xa, by - 0.12, xa, by, T.GILT, 1.0, name='括注线')
            c.line(xb, by - 0.12, xb, by, T.GILT, 1.0, name='括注线')
            c.text(xa, by + 0.12, xb - xa, 0.34, P(R(text, 'kai', 13.5, T.MUTED), align='c'), name='括注')
        return c

    # ---- 6 formula ------------------------------------------------------------------------
    def formula(self, kicker, title, latex, eqno, legend, note=None, refs=None):
        c = self.page(kicker, title, refs)
        px, py, pw, ph = 1.35, T.BODY_Y + 0.05, T.W - 2.7, 2.05
        c.rrect(px, py, pw, ph, r=0.03, fill=T.CARD, line=T.CARD_LINE, name='公式底板')
        svg = mathtex.render(latex, 26)
        w, h = (v / 96 for v in svg_size(svg))
        k = min(1.0, (pw - 2.1) / w, (ph - 0.3) / h)      # wide formulas shrink to the plate, never grow
        w, h = w * k, h * k
        c.svg(svg, (T.W - w) / 2, py + (ph - h) / 2, w, h, dpi=450, name='公式')
        c.text(px + pw - 1.0, py + ph / 2 - 0.2, 0.72, 0.4, P(R('(%s)' % eqno, 'num', 15, T.MUTED), align='r'),
               anchor='m', name='公式编号')
        colw = pw / 2
        ly = py + ph + 0.42
        for k, (sym, text) in enumerate(legend):
            cx = px + 0.35 + (k % 2) * colw
            cy = ly + (k // 2) * 0.74
            s = mathtex.render(sym, 20)
            sw, sh = (v / 96 for v in svg_size(s))
            c.svg(s, cx + (0.8 - sw) / 2, cy + 0.2 - sh / 2, sw, sh, dpi=450, name='符号')
            c.text(cx + 1.05, cy, colw - 1.4, 0.4, P(R(text, 'body', 14, T.TEXT)), anchor='m', name='符号说明')
        if note:
            ny = ly + ((len(legend) + 1) // 2) * 0.74 + 0.2
            c.text(T.ML, ny, T.CW, 0.34, P([R('注　', 'head', 12.5, T.RUBRIC), R(note, 'kai', 13.5, T.MUTED)],
                                            align='c'), name='注释')
        return c

    # ---- 7 experiment table ---------------------------------------------------------------------
    def compare_table(self, kicker, title, columns, rows, ours, best, second, note, stats, remark,
                      muted=(), refs=None):
        """rows: list of string lists; ours: row index highlighted; best/second: {(row, col)};
        muted: column indices printed in the secondary colour (e.g. a venue column)."""
        c = self.page(kicker, title, refs)

        def cell(text, r, ci):
            align = 'l' if ci == 0 else 'c'
            if r < 0:
                return [P(R(text, 'head', 13, T.INK), align=align)]
            if (r, ci) in best:
                run = R(text, 'title', 13.5, T.RUBRIC)
            elif ci == 0 and r == ours:
                run = R(text, 'head', 13.5, T.INK)
            else:
                run = R(text, 'body', 13.5, T.MUTED if ci in muted else T.TEXT, underline=(r, ci) in second)
            return [P(run, align=align)]

        ty = T.BODY_Y + 0.05
        th = self.booktabs(c, T.ML, ty, columns, rows, 7.5, cell, ours=ours, name='对比表')
        c.text(T.ML, ty + th + 0.14, 7.5, 0.3, P(R(note, 'kai', 12.5, T.MUTED)), name='表注')
        sx = 9.15
        sw = T.MR - sx
        y = T.BODY_Y
        for k, (num, label) in enumerate(stats):
            c.text(sx, y, sw, 0.82, P(R(num, 'num', 46, T.RUBRIC)), name='关键数字')
            c.text(sx, y + 0.86, sw, 0.3, P(R(label, 'body', 12.5, T.MUTED)), name='数字说明')
            y += 1.42
            c.line(sx, y - 0.2, sx + sw, y - 0.2, T.RULE, 0.75, name='分隔线')
        c.text(sx, y + 0.02, sw, 0.8, P(R(remark, 'kai', 16, T.INK), line=1.05), name='结论句')
        return c

    # ---- 8 chart analysis ---------------------------------------------------------------------
    def chart_analysis(self, kicker, title, categories, series, points, x_title=None, y_title=None,
                       y_range=(None, None, None), refs=None):
        c = self.page(kicker, title, refs)
        c.line_chart(T.ML - 0.08, T.BODY_Y - 0.05, 7.45, 4.6, categories, series, *y_range, x_title=x_title,
                     y_title=y_title, label=0, name='折线图')
        self.side_points(c, 8.8, T.BODY_Y + 0.12, points, size=13, step=1.45)
        return c

    # ---- 9 multi-point cards ------------------------------------------------------------------
    def cards(self, kicker, title, cards, takeaway=None, refs=None):
        c = self.page(kicker, title, refs)
        n, gap = len(cards), 0.28
        cw = (T.CW - gap * (n - 1)) / n
        y0, ch = T.BODY_Y + 0.05, 4.1
        for k, cd in enumerate(cards):
            x = T.ML + k * (cw + gap)
            c.rrect(x, y0, cw, ch, r=0.02, fill=T.CARD, line=T.CARD_LINE, name='卡片')
            self.numeral_ring(c, x + cw / 2, y0 + 0.52, k)
            c.svg(ILLUS[cd['art']](), x + cw / 2 - 0.76, y0 + 0.9, 1.52, name='插画')
            c.line(x + cw * 0.2, y0 + 2.58, x + cw * 0.8, y0 + 2.58, T.RULE, 0.75, name='分隔线')
            c.text(x + 0.15, y0 + 2.7, cw - 0.3, 0.42, P(R(cd['title'], 'head', 17, T.INK), align='c'), name='卡片标题')
            tw = cw - 0.24
            body = metrics.tidy(cd['text'], tw, 13.5, 'kai', balance=True)
            c.text(x + 0.12, y0 + 3.16, tw, 0.8, P(R(body, 'kai', 13.5, T.TEXT), align='c', line=1.02),
                   name='卡片说明')
        if takeaway:
            c.text(T.ML, y0 + ch + 0.2, T.CW, 0.4, P(R(takeaway, 'head', 15, T.INK), align='c'), name='结论句')
        return c

    # ---- 10 closing ---------------------------------------------------------------------------
    def closing(self, kicker, title, points, thanks, contact):
        c = self.page(kicker, title, layout='结束', width=7.4)
        y = 2.0
        for k, (lead, detail) in enumerate(points):
            c.text(T.ML, y - 0.04, 0.7, 0.5, P(R(ROMAN[k], 'num', 22, T.RUBRIC)), name='序号')
            c.text(T.ML + 0.75, y, 6.5, 0.42, P(R(lead, 'head', 17.5, T.INK)), name='要点')
            c.text(T.ML + 0.75, y + 0.48, 6.5, 0.4, P(R(detail, 'body', 13.5, T.MUTED)), name='要点说明')
            if k < len(points) - 1:
                c.line(T.ML + 0.75, y + 1.12, 7.6, y + 1.12, T.RULE, 0.75, name='分隔线')
            y += 1.38
        lx, ly, ls = 8.45, 1.05, 3.75
        c.svg(illus.laurel(), lx, ly, ls, name='装饰 · 桂冠')
        scx, scy = lx + ls / 2, ly + ls * 124 / 240
        sd = 1.72
        c.svg(illus.seal(), scx - sd / 2, scy - sd / 2, sd, name='装饰 · 火漆印')
        c.text(lx, ly + ls + 0.16, ls, 0.5, P(R(thanks, 'title', 22, T.INK), align='c'), name='致谢')
        c.text(lx - 0.3, ly + ls + 0.72, ls + 0.6, 0.32, P(R(contact, 'body', 12.5, T.MUTED), align='c'), name='联系方式')
        return c

    # ---- 11 plain text ------------------------------------------------------------------------
    def text_page(self, kicker, title, paragraphs, notes=(), refs=None):
        """Manuscript page for longer prose: outdented illuminated initial, justified paragraphs,
        optional marginal notes on the right. paragraphs: list of str (the first opens with the initial)."""
        c = self.page(kicker, title, refs)
        y0 = T.BODY_Y + 0.1
        ds = 0.95
        c.rect(T.ML, y0 + 0.06, ds, ds, fill=T.CARD, line=T.GILT, lw=1.0, name='首字底框')
        c.rect(T.ML + 0.06, y0 + 0.12, ds - 0.12, ds - 0.12, line=T.GILT, lw=0.5, name='首字内框')
        first = paragraphs[0]
        c.text(T.ML, y0 + 0.06, ds, ds, P(R(first[0], 'title', 44, T.RUBRIC), align='c'), anchor='m', name='首字')
        tx = T.ML + ds + 0.3
        tw = (9.75 if notes else T.MR) - tx
        size = 16
        indent = 2 * size / 72                      # two-character first-line indent

        def para(text, ind):
            """Justified paragraph; a right margin is added until the last line is no orphan."""
            probe = ('　　' if ind else '') + text
            right = next((r / 20 for r in range(0, 16)
                          if len(metrics.wrap(probe, tw - r / 20, size, 'body')[-1]) > 3), 0)
            return P(R(text, 'body', size, T.TEXT), align='j', line=1.25, after=9, first=ind, right=right)

        paras = [para(first[1:], 0)] + [para(p, indent) for p in paragraphs[1:]]
        c.text(tx, y0, tw, T.BODY_B - y0, paras, name='正文')
        if notes:
            nx = 10.15
            y = y0 + 0.05
            for k, note in enumerate(notes):
                c.svg(art.rosette(0.2), nx, y + 0.07, 0.2, name='装饰 · 旁注')
                nw = T.MR - nx - 0.32
                body = metrics.tidy(note, nw, 12.5, 'kai')
                h = metrics.text_height(body, nw, 12.5, 'kai', 1.05)
                c.text(nx + 0.32, y, nw, h + 0.05, P(R(body, 'kai', 12.5, T.MUTED), line=1.05), name='旁注')
                y += h + 0.42
        return c

    # ---- 12 timeline ---------------------------------------------------------------------------
    def timeline(self, kicker, title, events, refs=None):
        """events: [dict(date, title, text, key=False)], 4-6 entries; `key` marks this work."""
        c = self.page(kicker, title, refs)
        n = len(events)
        step = T.CW / n
        ay = 3.85
        c.line(T.ML, ay, T.MR, ay, T.GILT, 1.25, name='时间轴')
        for k, ev in enumerate(events):
            cx = T.ML + step * (k + 0.5)
            key = ev.get('key')
            d = 0.3 if key else 0.22
            c.text(cx - step / 2, ay - 0.98, step, 0.6, P(R(ev['date'], 'num', 24 if key else 21,
                                                           T.RUBRIC if key else T.INK), align='c'), anchor='b',
                   name='时间')
            c.line(cx, ay - 0.32, cx, ay - 0.16, T.GILT, 0.75, name='刻度')
            c.shape('diamond', cx - d / 2, ay - d / 2, d, d, fill=T.RUBRIC if key else T.GILT, line=T.PAPER, lw=1.0,
                    name='节点')
            tw = step - 0.24
            c.text(cx - tw / 2, ay + 0.36, tw, 0.42, P(R(ev['title'], 'head', 15.5, T.INK), align='c'), name='事件')
            body = metrics.tidy(ev['text'], tw, 12.5, 'body', balance=True)
            c.text(cx - tw / 2, ay + 0.84, tw, 1.3, P(R(body, 'body', 12.5, T.MUTED), align='c', line=1.1),
                   name='事件说明')
            if key:
                c.rrect(cx - step / 2 + 0.06, ay - 1.1, step - 0.12, 3.35, r=0.03, line=T.RUBRIC, lw=0.75,
                        dash='dash', name='本文标记')
        return c

    # ---- 13 related work -------------------------------------------------------------------------
    def related_work(self, kicker, title, columns, rows, ours, note, refs=None):
        """Feature matrix. rows: [[method, source, mark, ...]] with marks 'yes' / 'part' / 'no'."""
        c = self.page(kicker, title, refs)

        def cell(text, r, ci):
            align = 'l' if ci == 0 else 'c'
            if r < 0:
                return [P(R(text, 'head', 13, T.INK), align=align)]
            if text in MARKS:
                glyph, col = MARKS[text]
                return [P(R(glyph, size=15, color=T.RUBRIC if r == ours and text == 'yes' else col,
                            font='Segoe UI Symbol'), align='c')]
            if ci == 0:
                return [P(R(text, 'head' if r == ours else 'body', 13.5, T.INK), align=align)]
            return [P(R(text, 'body', 13, T.MUTED), align=align)]

        shown = [[MARKS[v][0] if v in MARKS else v for v in row] for row in rows]
        ty = T.BODY_Y + 0.05
        th = self.booktabs(c, T.ML, ty, columns, shown, T.CW, lambda t, r, ci: cell(
            rows[r][ci] if r >= 0 else t, r, ci), ours=ours, row_h=(0.56, 0.52), name='相关工作表')
        legend = [R(MARKS['yes'][0], size=13, color=T.INK, font='Segoe UI Symbol'), R(' 支持　　', 'body', 12, T.MUTED),
                  R(MARKS['part'][0], size=13, color=T.GILT_DEEP, font='Segoe UI Symbol'),
                  R(' 部分支持　　', 'body', 12, T.MUTED),
                  R(MARKS['no'][0], size=13, color=T.FAINT, font='Segoe UI Symbol'), R(' 不支持', 'body', 12, T.MUTED)]
        c.text(T.ML, ty + th + 0.16, 6, 0.3, P(legend), name='图例')
        c.text(T.MR - 6.5, ty + th + 0.16, 6.5, 0.3, P(R(note, 'kai', 13, T.INK), align='r'), name='结论句')
        return c

    # ---- 14 pseudocode ---------------------------------------------------------------------------
    def pseudocode(self, kicker, title, caption, lines, notes, refs=None):
        """lines: [(indent_level, text)]; '▷' starts a comment. notes: [(line_range, explanation)]."""
        c = self.page(kicker, title, refs)
        x0, y0, w = T.ML, T.BODY_Y + 0.05, 7.1
        lh = 21.0                                    # exact line pitch (pt): numbers and code stay aligned
        c.line(x0, y0, x0 + w, y0, T.INK, 1.25, name='算法顶线')
        c.text(x0 + 0.05, y0 + 0.1, w, 0.36, P([R(caption.split('　')[0] + '　', 'title', 14, T.RUBRIC),
                                              R('　'.join(caption.split('　')[1:]), 'head', 14, T.INK)]),
               name='算法标题')
        c.line(x0, y0 + 0.56, x0 + w, y0 + 0.56, T.INK, 0.6, name='算法分隔线')
        code, nums = [], []
        for k, (lvl, text) in enumerate(lines):
            body, _, comment = text.partition('▷')
            runs = []
            pos = 0
            for m in re.finditer(KEYWORDS, body):
                if m.start() > pos:
                    runs.append(R(body[pos:m.start()], 'body', 13, T.TEXT))
                runs.append(R(m.group(0), 'title', 13, T.INK))
                pos = m.end()
            if pos < len(body):
                runs.append(R(body[pos:], 'body', 13, T.TEXT))
            if comment:
                runs.append(R('▷ ' + comment.strip(), 'kai', 12.5, T.RUBRIC))
            code.append(P(runs or [R(' ', 'body', 13)], exact=lh, indent=0.32 * lvl))
            nums.append(P(R(str(k + 1), 'num', 12, T.FAINT), exact=lh, align='r'))
        ch = len(lines) * lh / 72 + 0.1
        c.text(x0, y0 + 0.68, 0.3, ch, nums, name='行号')
        c.text(x0 + 0.5, y0 + 0.68, w - 0.55, ch, code, name='伪代码')
        by = y0 + 0.68 + ch + 0.08
        c.line(x0, by, x0 + w, by, T.INK, 1.25, name='算法底线')
        x = 8.55
        y = T.BODY_Y + 0.12
        nw = T.MR - x
        for k, (rng, text) in enumerate(notes):
            c.text(x, y, nw, 0.34, P(R('第 %s 行' % rng, 'head', 13, T.RUBRIC)), name='行号说明')
            body = metrics.tidy(text, nw, 13.5, 'body', balance=True)
            c.text(x, y + 0.4, nw, 0.72, P(R(body, 'body', 13.5, T.MUTED), line=1.1), name='说明')
            if k < len(notes) - 1:
                c.line(x, y + 1.28, T.MR, y + 1.28, T.RULE, 0.75, name='分隔线')
            y += 1.46
        return c

    # ---- 15 image showcase -------------------------------------------------------------------------
    def gallery(self, kicker, title, images, refs=None):
        """images: [(path, caption)], 1-3 plates in a row, captions labelled 图 a / b / c."""
        c = self.page(kicker, title, refs)
        n, gap = len(images), 0.35
        pw = (T.CW - gap * (n - 1)) / n
        ph = min(4.05, pw * 0.78 + 0.4)
        py = T.BODY_Y + 0.05 + (4.05 - ph) / 2
        for k, (path, cap) in enumerate(images):
            px = T.ML + k * (pw + gap)
            self.plate(c, px, py, pw, ph)
            c.image(path, px + 0.18, py + 0.18, pw - 0.36, ph - 0.36, name='图片', fit='contain')
            body = metrics.tidy(cap, pw - 0.5, 12.5, 'kai')
            c.text(px, py + ph + 0.12, pw, 0.6, P([R('图 %s　' % 'abcdef'[k], 'head', 11.5, T.RUBRIC),
                                                  R(body, 'kai', 12.5, T.MUTED)], align='c'), name='图注')
        return c

    # ---- 16 references -----------------------------------------------------------------------------
    def references(self, entries, kicker='参考文献'):
        """entries: full citations as strings; split into two columns (long text allowed here)."""
        c = self.page(kicker)
        half = (len(entries) + 1) // 2
        colw = (T.CW - 0.5) / 2
        for col, chunk in enumerate((entries[:half], entries[half:])):
            paras = [P([R('[%d]' % (col * half + i + 1), 'num', 12.5, T.RUBRIC), R('　' + e, 'body', 12, T.TEXT)],
                       hang=0.42, line=1.08, after=7) for i, e in enumerate(chunk)]
            c.text(T.ML + col * (colw + 0.5), 1.25, colw, T.BODY_B - 1.25, paras, name='文献列表')
        c.line(T.ML + colw + 0.25, 1.3, T.ML + colw + 0.25, 6.2, T.RULE, 0.75, name='分栏线')
        return c

    # ---- 17 backup / appendix -----------------------------------------------------------------------
    def appendix(self, tag, kicker, title, columns, rows, notes, refs=None):
        """Backup slide: bookmark ribbon with a short vertical `tag` (≤ 3 CJK chars, e.g. '附录'),
        a compact table, dense notes."""
        c = self.page(kicker, title, refs, width=9.9)
        c.svg(art.bookmark(h_in=1.25), 11.0, 0.25, 0.46, name='装饰 · 书签')
        c.text(11.0, 0.3, 0.46, 1.0, P(R(tag, 'head', 12, 'FBF3E6', spc=300), align='c'), vert='eaVert',
               anchor='m', name='附录标签')

        def cell(text, r, ci):
            if r < 0:
                return [P(R(text, 'head', 12.5, T.INK), align='l' if ci == 0 else 'c')]
            return [P(R(text, 'body', 12.5, T.TEXT), align='l' if ci == 0 else 'c')]

        ty = T.BODY_Y + 0.05
        self.booktabs(c, T.ML, ty, columns, rows, 6.6, cell, name='附录表')
        x = 7.95
        paras = [P(R(metrics.tidy(n, T.MR - x - 0.3, 13, 'body'), 'body', 13, T.TEXT), bullet='◆', bullet_color=T.GILT,
                   bullet_size=0.6, hang=0.3, line=1.12, after=9) for n in notes]
        c.text(x, ty + 0.05, T.MR - x, T.BODY_B - ty, paras, name='附录要点')
        return c
