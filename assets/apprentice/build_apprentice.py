#!/usr/bin/env python3
"""Build the MUIOGO-AI "apprentice" asset set.

The metaphor for how MUIOGO-AI runs: the hat is the orchestrator and the brooms
are the workers it sends out.
Drawn from the public-domain source (Goethe 1797 / Dukas 1897) - original
artwork, no Disney characters or designs. See README.md.

Shares the palette and the wordmark with ../headless-logo/build_logo.py.

Run:  python3 build_apprentice.py [outdir]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "headless-logo"))
from build_logo import (BRAND, CYAN, GOLD, GRADS, INK, MONO, mono,  # noqa: E402
                        wordmark)

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else HERE)

VIOLET, GREEN = "#7C5CFF", "#4ADE80"

DEFS = GRADS + f"""
    <linearGradient id="cone" x1=".1" y1="0" x2=".9" y2="1">
      <stop offset="0" stop-color="#9B7DFF"/><stop offset=".55" stop-color="#5B3FD6"/><stop offset="1" stop-color="#31217A"/>
    </linearGradient>
    <linearGradient id="brim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4B35A8"/><stop offset="1" stop-color="#231764"/>
    </linearGradient>
    <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFE066"/><stop offset="1" stop-color="#E8890C"/>
    </linearGradient>
    <linearGradient id="wood" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#C98A46"/><stop offset="1" stop-color="#8B5A28"/>
    </linearGradient>
    <linearGradient id="straw" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F0CE7E"/><stop offset="1" stop-color="#C89339"/>
    </linearGradient>
    <radialGradient id="magic" cx=".5" cy=".5" r=".5">
      <stop offset="0" stop-color="#8B6BFF" stop-opacity=".42"/><stop offset="1" stop-color="#8B6BFF" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="cone-clip"><path d="{{CONE}}"/></clipPath>
"""

# ======================================================================== hat
# 200x200 grid; visual bounds x 22..190, y 6..174.
SPINE = [(100.0, 150.0), (98.0, 108.0), (104.0, 58.0), (130.0, 18.0)]
W_BASE, W_TIP, TAPER, SAMPLES = 43.0, 2.4, 0.72, 18


def _bez(P, t):
    u = 1 - t
    return tuple(u ** 3 * P[0][i] + 3 * u ** 2 * t * P[1][i] + 3 * u * t ** 2 * P[2][i]
                 + t ** 3 * P[3][i] for i in range(2))


def _tan(P, t):
    u = 1 - t
    return tuple(3 * u ** 2 * (P[1][i] - P[0][i]) + 6 * u * t * (P[2][i] - P[1][i])
                 + 3 * t ** 2 * (P[3][i] - P[2][i]) for i in range(2))


def spine_pt(t, off=0.0):
    """Point on the cone axis at t, optionally offset across the axis."""
    x, y = _bez(SPINE, t)
    tx, ty = _tan(SPINE, t)
    n = (tx * tx + ty * ty) ** .5 or 1.0
    return (x - ty / n * off, y + tx / n * off)


def band_path(t=0.46, half=52.0, thick=14.0, bow=7.0):
    """A band wrapping the cone at height t - bowed, so the cone reads as round."""
    x, y = _bez(SPINE, t)
    tx, ty = _tan(SPINE, t)
    n = (tx * tx + ty * ty) ** .5 or 1.0
    ux, uy = tx / n, ty / n          # along the axis (points up)
    nx, ny = -uy, ux                 # across the axis
    def pt(a, b):
        return (x + nx * a + ux * b, y + ny * a + uy * b)
    tl, tr = pt(-half, -thick), pt(half, -thick)
    bl, br = pt(-half, thick), pt(half, thick)
    ct, cb = pt(0, -thick + bow), pt(0, thick + bow)
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    return (f"M{f(tl)} Q{f(ct)} {f(tr)} L{f(br)} Q{f(cb)} {f(bl)} Z")


def cone_path():
    """A cone as a ribbon tapering along a curved spine - reads as a hat, not a fin."""
    left, right = [], []
    for i in range(SAMPLES + 1):
        t = i / SAMPLES
        x, y = _bez(SPINE, t)
        tx, ty = _tan(SPINE, t)
        n = (tx * tx + ty * ty) ** .5 or 1.0
        nx, ny = -ty / n, tx / n
        w = W_TIP + (W_BASE - W_TIP) * (1 - t) ** TAPER
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    pts = left + right[::-1]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


CONE = cone_path()
HAT_BOX = (22, 6, 190, 174)


def spark(x, y, r, fill=CYAN, op=1.0):
    """Four-point sparkle."""
    return (f'<path d="M{x},{y - r} Q{x + r * .17},{y - r * .17} {x + r},{y} '
            f'Q{x + r * .17},{y + r * .17} {x},{y + r} Q{x - r * .17},{y + r * .17} '
            f'{x - r},{y} Q{x - r * .17},{y - r * .17} {x},{y - r} Z" fill="{fill}" '
            f'fill-opacity="{op}" stroke="none"/>')


def hat(transform, simple=False, sparks=True):
    k = 1.3 if simple else 1.0
    p = [f'  <g transform="{transform}" stroke="{INK}" stroke-linejoin="round" stroke-linecap="round">',
         f'    <path d="{CONE}" fill="url(#cone)" stroke-width="{4.5 * k:.1f}"/>',
         '    <g clip-path="url(#cone-clip)">',
         # gold band, perpendicular-ish to the cone axis at its base
         f'      <path d="{band_path()}" '
         f'fill="url(#band)" stroke="{INK}" stroke-width="{3.2 * k:.1f}"/>']
    if not simple:
        p += [f'      {spark(*[round(v, 1) for v in spine_pt(.30, -9)], 11, "#FFE066", .95)}',
              f'      {spark(*[round(v, 1) for v in spine_pt(.60, 5)], 7, "#FFE066", .8)}',
              f'      {spark(*[round(v, 1) for v in spine_pt(.12, 14)], 6, "#FFE066", .55)}']
    p += ['    </g>',
          f'    <path d="{CONE}" fill="none" stroke-width="{4.5 * k:.1f}"/>',
          f'    <ellipse cx="100" cy="150" rx="76" ry="22" fill="url(#brim)" '
          f'stroke-width="{4.5 * k:.1f}"/>']
    if not simple:
        p.append('    <path d="M34,146 C48,136 72,131 100,131 C128,131 152,136 166,146" '
                 'fill="none" stroke="#6B51C9" stroke-width="3.4" stroke-opacity=".9"/>')
    if sparks:
        p += [f'    {spark(172, 38, 9, CYAN)}', f'    {spark(186, 66, 6, CYAN, .8)}',
              f'    {spark(158, 12, 5.5, "#FFE066", .9)}']
    p.append('  </g>')
    return "\n".join(p)


# ===================================================================== broom
# 64x64 grid; visual bounds x 12..60, y 3..61.
BROOM_BOX = (12, 3, 60, 61)


def broom(transform, simple=False, ink="currentColor", tint=None):
    """A broom worker. tint=None keeps it monochrome (UI glyph); otherwise painted."""
    bristle = tint and "url(#straw)" or ink
    op = "" if tint else ' fill-opacity=".16"'
    p = [f'  <g transform="{transform}" stroke="{ink}" stroke-linejoin="round" '
         f'stroke-linecap="round" fill="none">',
         f'    <path d="M44,3 L30,33" stroke-width="4.6" stroke="{tint and "url(#wood)" or ink}"/>',
         f'    <path d="M25,31 L36,34 L45,55 L15,59 Z" fill="{bristle}"{op} stroke-width="3.4"/>',
         '    <path d="M24,37 L34,39" stroke-width="3"/>']
    if not simple:
        p += ['    <path d="M28,41 L23,56" stroke-width="2.4" stroke-opacity=".75"/>',
              '    <path d="M34,42 L36,54" stroke-width="2.4" stroke-opacity=".75"/>']
    p.append('  </g>')
    return "\n".join(p)


# ==================================================================== extras
def tick(cx, cy, s, colour=GREEN):
    return (f'  <path d="M{cx - s * .8:.0f},{cy} L{cx - s * .15:.0f},{cy + s * .6:.0f} '
            f'L{cx + s * .85:.0f},{cy - s * .7:.0f}" fill="none" stroke="{colour}" '
            f'stroke-width="{s * .22:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


def place(box, cx, cy, height):
    x0, y0, x1, y1 = box
    s = height / (y1 - y0)
    return (f"translate({cx - (x0 + x1) / 2 * s:.2f},{cy - (y0 + y1) / 2 * s:.2f}) "
            f"scale({s:.4f})")


def svg(w, h, body, title, defs=True):
    d = f'  <defs>{DEFS.replace("{CONE}", CONE)}  </defs>\n' if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
            f'height="{h}" role="img" aria-label="{title}">\n  <title>{title}</title>\n'
            f'{d}{body}\n</svg>\n')


# ============================================================== compositions
def build_icon():
    b = ['  <rect width="512" height="512" rx="116" fill="url(#bg)"/>',
         f'  <rect x="8" y="8" width="496" height="496" rx="110" fill="none" stroke="{CYAN}" '
         f'stroke-opacity=".38" stroke-width="3"/>',
         '  <circle cx="256" cy="238" r="205" fill="url(#magic)"/>',
         hat(place(HAT_BOX, 256, 226, 330)),
         # three brooms below, the workers it spawns
         broom(place(BROOM_BOX, 158, 416, 124), tint=1, ink=INK),
         broom(place(BROOM_BOX, 252, 422, 138), tint=1, ink=INK),
         broom(place(BROOM_BOX, 354, 416, 124), tint=1, ink=INK)]
    return svg(512, 512, "\n".join(b), "MUIOGO-AI apprentice mark")


def build_hat_only():
    b = ['  <rect width="512" height="512" rx="116" fill="url(#bg)"/>',
         '  <circle cx="256" cy="250" r="200" fill="url(#magic)"/>',
         hat(place(HAT_BOX, 256, 252, 400), simple=True)]
    return svg(512, 512, "\n".join(b), "MUIOGO-AI apprentice mark (small)")


def build_banner():
    W, H = 1400, 420
    wm, wmw = wordmark(BRAND, 76, 40, 46)
    base = 372
    b = [f'  <rect width="{W}" height="{H}" rx="40" fill="url(#bg)"/>',
         wm,
         '  <circle cx="208" cy="248" r="158" fill="url(#magic)"/>',
         hat(place(HAT_BOX, 208, 240, 232))]
    lean = [-4, 3, -2, 4, -3, 2]
    for i in range(6):
        x, cy = 470 + i * 142, 300 if i % 2 == 0 else 294
        b.append(broom(f"rotate({lean[i]} {x} {cy}) "
                       + place(BROOM_BOX, x, cy, 138 if i % 2 == 0 else 130),
                       tint=1, ink=INK))
    b.append(f'  <path d="M404,{base} L1290,{base}" stroke="{CYAN}" stroke-opacity=".20" '
             f'stroke-width="3" stroke-linecap="round"/>')
    return svg(W, H, "\n".join(b), "MUIOGO-AI apprentice banner")


def build_fanout():
    """One hat, many brooms - the dispatch figure. No words at all."""
    W, H = 1100, 600
    bx = [150 + i * 133.3 for i in range(7)]
    b = [f'  <rect width="{W}" height="{H}" rx="36" fill="url(#bg)"/>',
         '  <circle cx="550" cy="176" r="176" fill="url(#magic)"/>',
         hat(place(HAT_BOX, 550, 168, 228))]
    for i, x in enumerate(bx):
        off = abs(x - 550) / 400.0
        b.append(f'  <path d="M550,296 Q{(550 + x) / 2:.0f},{330 + off * 26:.0f} {x:.0f},400" '
                 f'fill="none" stroke="{CYAN}" stroke-opacity="{.40 - off * .12:.2f}" '
                 f'stroke-width="2.8" stroke-dasharray="9 10" stroke-linecap="round"/>')
    for x in bx:                                    # splayed outward, like a fan
        b.append(broom(f"rotate({(x - 550) / 400 * 8:.1f} {x:.0f} 470) "
                       + place(BROOM_BOX, x, 470, 150), tint=1, ink=INK))
    return svg(W, H, "\n".join(b), "MUIOGO-AI apprentice fan-out")


# ======================================================================= glyphs
GLYPH_DEFS = f"""
    <clipPath id="cone-clip"><path d="{CONE}"/></clipPath>
"""


def glyph(body, title):
    """64x64 UI glyph: strokes inherit currentColor, accents stay branded."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" '
            f'height="64" fill="none" role="img" aria-label="{title}">\n'
            f'  <title>{title}</title>\n{body}\n</svg>\n')


def g_hat():
    b = ['  <g stroke="currentColor" stroke-width="3.4" stroke-linejoin="round" '
         'stroke-linecap="round">',
         '    <path d="M19,45 C19,33 21,21 27,12 C30,7 37,3 42,6 C38,12 36,20 35,28 '
         'C34,38 37,45 45,47 Z"/>',
         '    <path d="M10,46 C10,41 20,38 32,38 C44,38 54,41 54,46 C54,51 44,54 32,54 '
         'C20,54 10,51 10,46 Z"/>',
         f'    <path d="M20,36 C25,40 32,40 36,35" stroke="{GOLD}"/>',
         '  </g>',
         f'  {spark(55, 15, 5, GOLD)}',
         f'  {spark(59, 27, 3.4, CYAN)}']
    return glyph("\n".join(b), "the hat - the orchestrator")


def g_broom(title=""):
    return glyph(broom("translate(0,0)"), title)


def g_run():
    b = [broom(place(BROOM_BOX, 26, 32, 54), simple=True),
         '  <g stroke="currentColor" stroke-width="2.8" stroke-linecap="round" fill="none" '
         'stroke-opacity=".6">',
         '    <path d="M46,26 Q54,33 50,41"/>',
         '    <path d="M53,21 Q62,32 56,45"/>',
         '  </g>']
    return glyph("\n".join(b), "a worker running")


def g_brooms():
    b = [broom(place(BROOM_BOX, 18, 38, 40), simple=True),
         broom(place(BROOM_BOX, 34, 34, 48), simple=True),
         broom(place(BROOM_BOX, 50, 38, 40), simple=True)]
    return glyph("\n".join(b), "workers running in parallel")


def g_done():
    b = [broom(place(BROOM_BOX, 26, 30, 46), simple=True),
         tick(48, 46, 10)]
    return glyph("\n".join(b), "worker finished")


def build_glyph_sheet(glyphs):
    """One preview sheet of the glyph set, on the brand plate."""
    cols, cell = len(glyphs), 190
    b = [f'  <rect width="{cols * cell}" height="270" rx="32" fill="url(#bg)"/>']
    for i, (name, _) in enumerate(glyphs):
        x = i * cell + cell / 2
        b.append(f'  <g transform="translate({x - 44},70) scale(1.375)" color="#DCEBFF">')
        b.append(GLYPH_BODIES[name])
        b.append('  </g>')
        b.append(mono(x, 214, 17, "#6E8CAE", name, anchor="middle"))
    return svg(cols * cell, 270, "\n".join(b), "apprentice glyph set")


GLYPH_BODIES = {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "glyphs").mkdir(exist_ok=True)

    glyphs = [("hat", g_hat()),
              ("broom", g_broom("a worker, queued")),
              ("broom-run", g_run()),
              ("brooms", g_brooms()),
              ("broom-done", g_done())]
    for name, text in glyphs:
        (OUT / "glyphs" / f"{name}.svg").write_text(text)
        inner = text.split("</title>", 1)[1].rsplit("</svg>", 1)[0].strip()
        GLYPH_BODIES[name] = inner
        print("wrote", OUT / "glyphs" / f"{name}.svg")

    for name, text in {"apprentice-icon.svg": build_icon(),
                       "apprentice-icon-small.svg": build_hat_only(),
                       "apprentice-banner.svg": build_banner(),
                       "apprentice-fanout.svg": build_fanout(),
                       "apprentice-glyph-sheet.svg": build_glyph_sheet(glyphs)}.items():
        (OUT / name).write_text(text)
        print("wrote", OUT / name)


if __name__ == "__main__":
    main()
