"""LaTeX -> vector SVG (XeLaTeX + dvisvgm, glyphs as paths), cached by content hash.

Formulas are typeset at the requested point size, so placing the SVG at its natural size keeps
them on the slide's type scale. Fonts: Libertinus Math / Serif, CJK in \\text{} via Noto Serif SC.
"""
import hashlib
import os
import subprocess
import tempfile

from . import tokens as T

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'cache', 'math')

PREAMBLE = r"""\documentclass[border=0.5pt]{standalone}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage{unicode-math}
\setmainfont{Libertinus Serif}
\setmathfont{Libertinus Math}
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif SC}
\newcommand{\bm}[1]{\symbfit{#1}}
\definecolor{ink}{HTML}{%s}
\begin{document}
\fontsize{%s}{%s}\selectfont\color{ink}%%
"""


def render(latex, size=24, color=T.INK, display=True):
    """SVG string for `latex` (math mode content, no $...$)."""
    body = ('$\\displaystyle %s$' if display else '$%s$') % latex
    return compile_svg(PREAMBLE % (color, size, round(size * 1.2, 1)) + body + '\n\\end{document}\n')


def compile_svg(src, via='dvi'):
    """Compile a complete XeLaTeX document to SVG (glyphs as paths); cached by source hash.
    via='dvi' uses dvisvgm (exact glyph boxes, best for formulas); via='pdf' goes through the PDF
    (needed for TikZ and \\resizebox, whose xdvipdfmx specials dvisvgm cannot read)."""
    key = hashlib.sha1((via + src).encode('utf-8')).hexdigest()[:16]
    out = os.path.join(CACHE, key + '.svg')
    if os.path.exists(out):
        return open(out, encoding='utf-8').read()
    os.makedirs(CACHE, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, 'f.tex'), 'w', encoding='utf-8') as fh:
            fh.write(src)
        cmd = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', 'f.tex']
        if via == 'dvi':
            cmd.insert(1, '-no-pdf')
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            err = [ln for ln in r.stdout.splitlines() if ln.startswith('!')]
            raise RuntimeError('LaTeX failed: %s' % ('; '.join(err) or r.stdout[-400:]))
        if via == 'dvi':
            subprocess.run(['dvisvgm', '--no-fonts', '--exact-bbox', '-o', 'f.svg', 'f.xdv'],
                           cwd=tmp, capture_output=True, check=True)
            svg = open(os.path.join(tmp, 'f.svg'), encoding='utf-8').read()
        else:
            import fitz
            with fitz.open(os.path.join(tmp, 'f.pdf')) as doc:
                svg = doc[0].get_svg_image(text_as_path=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(svg)
    return svg
