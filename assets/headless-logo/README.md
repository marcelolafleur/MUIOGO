# MUIOGO-AI headless mode — logo set

A goofy gold dragon head plus a terminal prompt: MUIOGO with no browser and no
clicks. Drawn in the same palette as `assets/MUIOGO_Logo.png` (navy background,
cyan-to-violet cool gradient, gold warm gradient).

| file | canvas | use |
| --- | --- | --- |
| `muiogo-headless-icon.svg` | 512×512 | app icon / avatar — dragon over a `>_` prompt |
| `muiogo-headless-icon-small.svg` | 512×512 | same icon with fine detail stripped; use below ~64 px |
| `muiogo-headless-lockup.svg` | 1400×380 | horizontal lockup — mark, wordmark, prompt |
| `muiogo-headless-banner.svg` | 1400×480 | README / docs hero — terminal window with the dragon leaning in |
| `png/` | — | rasterised icons for places that cannot take SVG |

There is no text anywhere in these files. The wordmark is drawn as paths, and
the banner's terminal session is drawn as bars and a chevron rather than words,
so nothing depends on a font being installed and nothing needs translating. The
banner's block cursor blinks where SMIL animation is supported and simply stays
visible where it is not.

## Palette

| role | value |
| --- | --- |
| ink / outline | `#0E1B2E` |
| background | `#132540` → `#060D18` |
| dragon gold | `#FFE985` → `#FFC02E` → `#E8890C` |
| mane | `#E29A12` → `#B06103` |
| tongue | `#FF8FAE` → `#E2456F` |
| cool (MUIO) | `#8AE7FF` → `#4FA8FF` → `#9B6BFF` |
| warm (GO) | `#FFE066` → `#FFB01F` → `#FF7A00` |
| terminal cyan | `#38BDF8` |

## Regenerating

All four files come from one source definition:

```bash
python3 assets/headless-logo/build_logo.py assets/headless-logo
```

Edit the dragon paths, the glyph table, or a composition function in
`build_logo.py` and re-run — nothing is hand-maintained across files. PNGs were
exported with `qlmanage -t -s <size> -o png muiogo-headless-icon.svg`.
