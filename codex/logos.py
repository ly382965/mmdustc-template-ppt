"""USTC marks (vector, from ../logos/*.pdf) recoloured to any template ink."""
import os
import re

import fitz  # PyMuPDF

LOGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logos')


def _pdf_svg(name):
    doc = fitz.open(os.path.join(LOGO_DIR, name + '.pdf'))
    return doc[0].get_svg_image(text_as_path=True)


def mark(name, color):
    """'ustc-badge' or 'ustc-name' as SVG filled with `color` (hex without '#')."""
    svg = _pdf_svg(name)
    svg = re.sub(r'\sxmlns:inkscape="[^"]*"', '', svg)
    # the marks are pure black fills with no explicit colour: set the colour on every top-level group
    return re.sub(r'<g\b', '<g fill="#%s"' % color, svg)


# Lab mark traced in ../LaTeX/mmdustc.cls (\LabLogo): two interlaced loops + five bars on a 463-unit grid,
# Chinese name in Microsoft YaHei Light, English name in TeX Gyre Heros letter-spaced.
LAB_TEX = r"""\documentclass[border=0pt]{standalone}
\usepackage{tikz,graphicx,xcolor,fontspec,xeCJK}
\newCJKfontfamily\labcjk{msyhl.ttc}[FontIndex=0]
\newfontfamily\labheros{texgyreheros-regular.otf}[LetterSpace=9]
\definecolor{ink}{HTML}{%s}
\begin{document}
\edef\labu{\fpeval{28.45/463}}
\begin{tikzpicture}[x=\labu pt, y=-\labu pt, color=ink]
\draw[line width=12*\labu pt, line join=round] plot[smooth cycle, tension=.55] coordinates {
  (34,299)(39,361)(63,418)(105,464)(150,500)(203,522)(250,540)(300,546)
  (347,540)(389,526)(426,509)(459,489)(512,446)(583,412)(637,389)(687,352)
  (704,300)(692,246)(659,201)(619,167)(581,139)(541,119)(502,106)(440,92)
  (380,88)(315,88)(268,89)(222,100)(173,118)(125,147)(82,188)(50,240)};
\draw[line width=12*\labu pt, line join=round] plot[smooth cycle, tension=.55] coordinates {
  (94,299)(90,352)(97,406)(121,455)(165,490)(221,500)(273,500)(319,493)
  (357,487)(389,478)(419,467)(446,455)(476,448)(512,446)(552,436)(624,435)
  (693,410)(728,359)(737,300)(732,239)(707,184)(665,141)(616,109)(564,91)
  (515,83)(460,86)(400,88)(350,92)(315,100)(284,117)(247,129)(209,148)
  (170,173)(137,207)(110,250)};
\foreach \x/\a/\b in {232/210/355, 310/255/330, 378/200/370, 450/245/330, 525/215/345}
  {\draw[line width=13*\labu pt] (\x,\a) -- (\x,\b);}
%s\end{tikzpicture}
\end{document}
"""
LAB_NAMES = (r'\node[anchor=base west, inner sep=0] at (842,352) {\resizebox{\fpeval{2830*\labu}pt}{!}'
             r'{\labcjk 认知智能全国重点实验室}};'
             r'\node[anchor=base west, inner sep=0] at (842,489) {\resizebox{\fpeval{2830*\labu}pt}{!}'
             r'{\labheros STATE KEY LABORATORY OF COGNITIVE INTELLIGENCE}};')


def lab(color, names=True):
    """State Key Laboratory of Cognitive Intelligence logo (mark + names) as SVG in `color`."""
    from .mathtex import compile_svg
    return compile_svg(LAB_TEX % (color, LAB_NAMES if names else ''), via='pdf')
