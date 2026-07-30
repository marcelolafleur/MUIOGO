#!/usr/bin/env python3
"""Build the MUIOGO-AI headless-mode logo set.

One dragon definition + one path-drawn wordmark -> app icon, small mark,
horizontal lockup, README banner. No font dependency for the wordmark.

Run:  python3 build_logo.py [outdir]
"""
import re
import sys
from pathlib import Path

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")

INK = "#0E1B2E"
BG0, BG1 = "#132540", "#060D18"
CYAN, GOLD, MUTED = "#38BDF8", "#FFB01F", "#8FA6C4"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

GRADS = f"""
    <linearGradient id="d-gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFE985"/><stop offset=".55" stop-color="#FFC02E"/><stop offset="1" stop-color="#E8890C"/>
    </linearGradient>
    <linearGradient id="d-frill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#E29A12"/><stop offset="1" stop-color="#B06103"/>
    </linearGradient>
    <linearGradient id="d-horn" x1="0" y1="1" x2=".3" y2="0">
      <stop offset="0" stop-color="#E8930D"/><stop offset="1" stop-color="#FFE79B"/>
    </linearGradient>
    <linearGradient id="d-tongue" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FF8FAE"/><stop offset="1" stop-color="#E2456F"/>
    </linearGradient>
    <linearGradient id="w-cool" x1="0" y1="0" x2=".85" y2="1">
      <stop offset="0" stop-color="#8AE7FF"/><stop offset=".45" stop-color="#4FA8FF"/><stop offset="1" stop-color="#9B6BFF"/>
    </linearGradient>
    <linearGradient id="w-warm" x1="0" y1="0" x2=".3" y2="1">
      <stop offset="0" stop-color="#FFE066"/><stop offset=".5" stop-color="#FFB01F"/><stop offset="1" stop-color="#FF7A00"/>
    </linearGradient>
    <radialGradient id="bg" cx=".5" cy=".38" r=".78">
      <stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/>
    </radialGradient>
    <radialGradient id="halo" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#FFB320" stop-opacity=".22"/><stop offset="1" stop-color="#FFB320" stop-opacity="0"/>
    </radialGradient>
"""

# ================================================================== dragon head
# Drawn on a 200x200 grid; visual bounds x 24..176, y 5..198.
MANE = ("M73.7,54.6 Q66.0,51.8 53.3,44.0 Q47.9,69.8 50.7,77.5 Q42.7,79.5 27.9,80.1 "
        "Q37.7,104.5 44.3,109.4 Q38.7,115.5 26.7,124.2 Q48.5,139.1 56.7,139.5 "
        "Q55.5,147.6 50.4,161.6 Q76.7,161.8 83.7,157.6 Q87.2,165.0 109.3,179.4 "
        "Q112.8,165.0 116.3,157.6 Q123.3,161.8 149.6,161.6 Q144.5,147.6 143.3,139.5 "
        "Q151.5,139.1 173.3,124.2 Q161.3,115.5 155.7,109.4 Q162.3,104.5 172.1,80.1 "
        "Q157.3,79.5 149.3,77.5 Q152.1,69.8 146.7,44.0 Q134.0,51.8 126.3,54.6 "
        "L135.8,82.0 L142.0,103.1 L136.7,124.5 L121.3,140.2 L100.0,146.0 L78.7,140.2 "
        "L63.3,124.5 L58.0,103.1 L64.2,82.0 L80.3,66.9 Z")
HORN_L = "M65.9,67.4 C48.0,50.0 30.0,30.0 34.0,8.0 C48.0,30.0 62.0,44.0 82.1,57.3 Z"
HORN_R = "M134.1,67.4 C152.0,50.0 170.0,30.0 166.0,8.0 C152.0,30.0 138.0,44.0 117.9,57.3 Z"
BANDS = ["M55.0,52.1 L64.8,47.9", "M45.9,41.1 L55.1,38.5", "M38.8,29.4 L46.4,28.3",
         "M145.0,52.1 L135.2,47.9", "M154.1,41.1 L144.9,38.5", "M161.2,29.4 L153.6,28.3"]
FACE = ("M100,52 C130,52 151,70 152,96 C153,118 145,132 132,142 C121,150 112,155 100,155 "
        "C88,155 79,150 68,142 C55,132 47,118 48,96 C49,70 70,52 100,52 Z")
MUZZLE = ("M100,120 C92,117 78,117 70,125 C61,134 66,149 78,151 C88,153 96,146 100,138 "
          "C104,146 112,153 122,151 C134,149 139,134 130,125 C122,117 108,117 100,120 Z")
NOSE = ("M92,104 C87,104 84,108 85,113 C86,119 93,122 100,122 C107,122 114,119 115,113 "
        "C116,108 113,104 108,104 Z")
TONGUE = ("M110,146 C122,144 137,154 142,169 C146,184 135,196 122,192 C110,188 105,175 "
          "106,161 C107,152 106,148 110,146 Z")


def dragon(transform, simple=False):
    """The dragon head. simple=True strips fine detail so it survives small sizes."""
    k = 1.25 if simple else 1.0          # heavier ink once detail is gone
    p = [f'  <g transform="{transform}" stroke="{INK}" stroke-linejoin="round" stroke-linecap="round">',
         f'    <path d="{MANE}" fill="url(#d-frill)" stroke-width="{3.6 * k:.1f}"/>',
         f'    <g fill="url(#d-horn)" stroke-width="{3.8 * k:.1f}">',
         f'      <path d="{HORN_L}"/>',
         f'      <path d="{HORN_R}"/>',
         '    </g>']
    if not simple:
        p.append(f'    <g fill="none" stroke="{INK}" stroke-opacity=".55" stroke-width="2.6">')
        p += [f'      <path d="{b}"/>' for b in BANDS]
        p.append('    </g>')
    p.append(f'    <path d="{FACE}" fill="url(#d-gold)" stroke-width="{4.5 * k:.1f}"/>')
    if not simple:
        p += [f'    <g fill="none" stroke="{INK}" stroke-opacity=".45" stroke-width="3.4">',
              '      <path d="M94.5,56 L100,62 L105.5,56"/>',
              '      <path d="M94.5,66 L100,72 L105.5,66"/>',
              '    </g>',
              '    <g fill="none" stroke="#D98A0B" stroke-width="3.4" stroke-opacity=".9">',
              '      <path d="M55,86 C60,76 70,72 80,74"/>',
              '      <path d="M145,82 C140,72 130,68 120,70"/>',
              '    </g>']
    # googly eyes: mismatched size and gaze, on purpose
    p += [f'    <circle cx="74" cy="95" r="21" fill="#fff" stroke-width="{4 * k:.1f}"/>',
          f'    <circle cx="128" cy="91" r="22.5" fill="#fff" stroke-width="{4 * k:.1f}"/>',
          f'    <circle cx="65" cy="93" r="8.8" fill="{INK}" stroke="none"/>',
          f'    <circle cx="137" cy="84" r="9.4" fill="{INK}" stroke="none"/>',
          '    <circle cx="62" cy="89" r="3" fill="#fff" stroke="none"/>',
          '    <circle cx="134" cy="80" r="3.2" fill="#fff" stroke="none"/>',
          f'    <path d="{MUZZLE}" fill="#FFD968" stroke-width="{3.6 * k:.1f}"/>',
          f'    <path d="{NOSE}" fill="#E89A10" stroke-width="{3.4 * k:.1f}"/>',
          f'    <circle cx="93.5" cy="112" r="2.2" fill="{INK}" stroke="none"/>',
          f'    <circle cx="106.5" cy="112" r="2.2" fill="{INK}" stroke="none"/>']
    if not simple:
        p += ['    <path d="M100,122 L100,136" fill="none" stroke-width="3.2" stroke-opacity=".8"/>',
              '    <path d="M79,148 L87,150 L82,161 Z" fill="#fff" stroke-width="3"/>',
              '    <path d="M90,151 L97,152 L93,161 Z" fill="#fff" stroke-width="3"/>']
    p.append(f'    <path d="{TONGUE}" fill="url(#d-tongue)" stroke-width="{4 * k:.1f}"/>')
    if not simple:
        p.append('    <path d="M116,157 C126,163 132,172 134,182" fill="none" stroke="#C33459"'
                 ' stroke-width="3" stroke-opacity=".85"/>')
    p.append('  </g>')
    return "\n".join(p)


def place(cx, cy, height):
    """Transform centring the dragon's visual bounds on (cx,cy) at the given height."""
    s = height / 193.0
    return f"translate({cx - 100 * s:.2f},{cy - 101.5 * s:.2f}) scale({s:.4f})"


# ==================================================================== wordmark
# Stroke-drawn display letters. Cell: y 8 (cap top) .. 140 (baseline), stroke 26.
STROKE, TRACK, CAP = 26, 5, 132
GLYPHS = {
    "M": (116, ["M8,140 L8,8 L54,74 L100,8 L100,140"]),
    "U": (116, ["M8,8 L8,78 C8,118 100,118 100,78 L100,8"]),
    "I": (60,  ["M30,8 L30,140"]),
    "O": (116, ["M100,74 C100,110 79,140 54,140 C29,140 8,110 8,74 "
                "C8,38 29,8 54,8 C79,8 100,38 100,74 Z"]),
    "G": (116, ["M100,48 C92,24 75,8 54,8 C28,8 8,37 8,74 C8,111 28,140 54,140 "
                "C80,140 100,120 100,92 L64,92"]),
    "A": (120, ["M4,140 L54,8 L104,140", "M25,98 L83,98"]),
    "-": (62,  ["M10,74 L52,74"]),
}


def _shift(d, dx):
    """Offset every x coordinate of an absolute M/L/C/Z path by dx."""
    out, k = [], 0
    for t in re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", d):
        if t.isalpha():
            out.append(t)
            k = 0
        else:
            out.append(f"{float(t) + (dx if k % 2 == 0 else 0):g}")
            k += 1
    return " ".join(out)


def word_width(text):
    return sum(GLYPHS[c][0] for c in text) + TRACK * (len(text) - 1)


def wordmark(segments, x, y, cap_height, skew=-8):
    """segments: [(text, paint), ...]. y is the cap-top. Returns (svg, width)."""
    s = cap_height / CAP
    cursor, parts = 0, []
    for text, paint in segments:
        ds = []
        for ch in text:
            adv, subpaths = GLYPHS[ch]
            ds += [_shift(d, cursor) for d in subpaths]
            cursor += adv + TRACK
        parts.append(f'      <path d="{" ".join(ds)}" stroke="{paint}"/>')
    total = cursor - TRACK
    g = (f'  <g transform="translate({x:.1f},{y - 8 * s:.1f}) scale({s:.4f}) skewX({skew})" '
         f'fill="none" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">\n'
         + "\n".join(parts) + "\n  </g>")
    return g, total * s


BRAND = [("MUIO", "url(#w-cool)"), ("GO", "url(#w-warm)"), ("-AI", MUTED)]


# ====================================================================== bits
def prompt(x, y, size, cursor=CYAN, chevron=GOLD):
    """Vector '>_' prompt: chevron plus block cursor, left edge at x, centred on y."""
    h = size
    return (f'  <g stroke-linecap="round" stroke-linejoin="round">\n'
            f'    <path d="M{x:.0f},{y - h * .40:.0f} L{x + h * .38:.0f},{y:.0f} '
            f'L{x:.0f},{y + h * .40:.0f}" fill="none" stroke="{chevron}" '
            f'stroke-width="{h * .17:.1f}"/>\n'
            f'    <rect x="{x + h * .60:.0f}" y="{y - h * .38:.0f}" width="{h * .32:.0f}" '
            f'height="{h * .76:.0f}" rx="{h * .06:.1f}" fill="{cursor}"/>\n  </g>')


def bar(x, y, w, fill, h=14, op=1.0):
    """A rounded bar standing in for a line of terminal output - no words."""
    return (f'  <rect x="{x:.0f}" y="{y - h / 2:.0f}" width="{w:.0f}" height="{h}" '
            f'rx="{h / 2}" fill="{fill}" fill-opacity="{op}"/>')


def caret(x, y, s, colour=GOLD):
    """A small prompt chevron."""
    return (f'  <path d="M{x:.0f},{y - s * .5:.0f} L{x + s * .45:.0f},{y:.0f} '
            f'L{x:.0f},{y + s * .5:.0f}" fill="none" stroke="{colour}" '
            f'stroke-width="{s * .2:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


def mono(x, y, size, fill, text, spacing=0, anchor="start"):
    """Monospace text pinned to a computed width so layout never depends on the font."""
    n = len(text)
    length = n * (size * 0.60 + spacing) - spacing
    esc = text.replace("&", "&amp;").replace("<", "&lt;")
    return (f'  <text x="{x:.0f}" y="{y:.0f}" font-family="{MONO}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" textLength="{length:.0f}" '
            f'lengthAdjust="spacingAndGlyphs">{esc}</text>')


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{title}">\n  <title>{title}</title>\n'
            f'  <defs>{GRADS}  </defs>\n{body}\n</svg>\n')


# ================================================================ compositions
def build_icon():
    b = ['  <rect width="512" height="512" rx="116" fill="url(#bg)"/>',
         f'  <rect x="8" y="8" width="496" height="496" rx="110" fill="none" stroke="{CYAN}" '
         f'stroke-opacity=".38" stroke-width="3"/>',
         '  <circle cx="256" cy="200" r="196" fill="url(#halo)"/>',
         dragon(place(256, 194, 330)),
         prompt(225, 436, 68)]
    return svg(512, 512, "\n".join(b), "MUIOGO-AI headless mode")


def build_small():
    b = ['  <rect width="512" height="512" rx="116" fill="url(#bg)"/>',
         dragon(place(256, 254, 382), simple=True)]
    return svg(512, 512, "\n".join(b), "MUIOGO-AI headless mode (small)")


def build_lockup():
    W, H = 1400, 380
    x0 = 384
    wm, wmw = wordmark(BRAND, x0, 112, 100)
    b = [f'  <rect width="{W}" height="{H}" rx="44" fill="url(#bg)"/>',
         '  <circle cx="198" cy="186" r="168" fill="url(#halo)"/>',
         dragon(place(198, 184, 268)),
         wm,
         prompt(x0 + 6, 272, 52)]
    return svg(W, H, "\n".join(b), "MUIOGO-AI - headless mode")


def build_banner():
    W, H = 1400, 480
    wx, wy, ww, wh = 72, 138, 900, 288
    wm, wmw = wordmark(BRAND, wx + 8, 42, 48)
    b = [f'  <rect width="{W}" height="{H}" rx="40" fill="url(#bg)"/>',
         wm,
         # terminal window
         f'  <rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="20" fill="#0A1421" '
         f'stroke="{CYAN}" stroke-opacity=".32" stroke-width="2.5"/>',
         f'  <path d="M{wx},{wy + 20} a20,20 0 0 1 20,-20 h{ww - 40} a20,20 0 0 1 20,20 v28 '
         f'H{wx} Z" fill="#12243A"/>',
         f'  <line x1="{wx}" y1="{wy + 48}" x2="{wx + ww}" y2="{wy + 48}" stroke="{CYAN}" '
         f'stroke-opacity=".22" stroke-width="2"/>',
         f'  <circle cx="{wx + 30}" cy="{wy + 24}" r="6.5" fill="#FF6B6B"/>',
         f'  <circle cx="{wx + 52}" cy="{wy + 24}" r="6.5" fill="#FFC93C"/>',
         f'  <circle cx="{wx + 74}" cy="{wy + 24}" r="6.5" fill="#4ADE80"/>',
         # the session, as shapes rather than words
         caret(wx + 36, wy + 100, 24),
         bar(wx + 64, wy + 100, 404, "#DCEBFF"),
         f'  <path d="M{wx + 38},{wy + 146} l8,9 l17,-20" fill="none" stroke="#4ADE80" '
         f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
         bar(wx + 74, wy + 146, 232, "#4ADE80", 13, .95),
         bar(wx + 64, wy + 190, 322, "#6E8CAE", 13, .75),
         bar(wx + 400, wy + 190, 96, "#6E8CAE", 13, .5),
         caret(wx + 36, wy + 238, 24),
         f'  <rect x="{wx + 64}" y="{wy + 224}" width="15" height="27" rx="2" fill="{CYAN}">'
         f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
         f'repeatCount="indefinite"/></rect>',
         # dragon leaning in from the right
         f'  <g transform="rotate(-7 1168 252)">\n{dragon(place(1168, 250, 314))}\n  </g>']
    return svg(W, H, "\n".join(b), "MUIOGO-AI headless mode")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in {"muiogo-headless-icon.svg": build_icon(),
                       "muiogo-headless-icon-small.svg": build_small(),
                       "muiogo-headless-lockup.svg": build_lockup(),
                       "muiogo-headless-banner.svg": build_banner()}.items():
        (OUT / name).write_text(text)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
