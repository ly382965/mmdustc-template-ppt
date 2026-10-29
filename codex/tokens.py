"""Design tokens: palette, type roles, grid. Every page builder reads from here."""

# ---- palette (hex, no '#') -------------------------------------------------------------
PAPER = 'F7F3EA'        # parchment base (background image is built around it)
CARD = 'EFE8DB'         # card / plate fill, one step darker than paper
CARD_LINE = 'D6CAB4'    # card border
RULE = 'D3C7B1'         # hairline separators
INK = '2B2620'          # titles
TEXT = '3E3830'         # body text
MUTED = '766C5F'        # secondary text
FAINT = 'A3998A'        # tertiary text, inactive items
RUBRIC = 'A8533A'       # accent: rubric red-brown (Claude clay, deepened for text contrast)
RUBRIC_TINT = 'F1E0D4'  # highlight row / chip fill
GILT = 'B39363'         # ornament gold
GILT_DEEP = '8B6E42'
GILT_PALE = 'D9C7A2'
# manuscript pigments for data series, in order of use
SERIES = ['A8533A', '4F6D8C', '6E8A5F', 'C2964B', '86587A', '8C8578']

# ---- type roles: (latin face, east-asian face) -----------------------------------------
FONTS = {
    'title':  ('Noto Serif SC SemiBold', 'Noto Serif SC SemiBold'),
    'head':   ('Noto Serif SC Medium', 'Noto Serif SC Medium'),
    'body':   ('Noto Serif SC', 'Noto Serif SC'),
    'light':  ('Noto Serif SC Light', 'Noto Serif SC Light'),
    'kai':    ('Garamond', '华文楷体'),
    'kicker': ('Goudy Old Style', 'Noto Serif SC Medium'),
    'num':    ('Goudy Old Style', 'Noto Serif SC'),
    'mono':   ('Cascadia Mono', 'Noto Sans SC'),
}
# default tracking per role, in em (Huawen Kaiti sits loose on its em-box)
TRACK = {'kai': -0.04}

# ---- grid (inches, 13.333 x 7.5 canvas) --------------------------------------------------
W, H = 13.333, 7.5
ML = 0.85                 # content left edge
MR = W - 0.85             # content right edge
CW = MR - ML              # content width
KICKER_Y = 0.60
TITLE_Y = 0.88
BODY_Y = 1.85             # first row of page content (pages have no subtitle line)
BODY_B = 6.42             # last row of page content
FOOT_Y = 6.86             # bottom line: references at left, page number at right
