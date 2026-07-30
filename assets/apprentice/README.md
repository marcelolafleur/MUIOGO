# MUIOGO-AI apprentice — logo and illustration set

Iconography for how MUIOGO-AI runs: the hat is the orchestrator, the brooms are
the workers it sends out. Two shapes, nothing else — no text in any of the
files apart from the glyph sheet's own labels.

Same palette as [`../headless-logo/`](../headless-logo), with violet added for
the hat.

| file | canvas | use |
| --- | --- | --- |
| `apprentice-icon.svg` | 512×512 | app icon — the orchestrator and its workers |
| `apprentice-icon-small.svg` | 512×512 | hat alone, detail stripped; use below ~64 px |
| `apprentice-banner.svg` | 1400×420 | docs/README hero — hat and a row of workers |
| `apprentice-fanout.svg` | 1100×600 | one hat dispatching seven brooms; for docs figures |
| `apprentice-glyph-sheet.svg` | 950×270 | preview of the glyph set |
| `glyphs/*.svg` | 64×64 | UI state icons (see below) |
| `png/` | — | rasterised icons for places that cannot take SVG |

## Glyphs

Five 64×64 icons for run state. Strokes use `currentColor`, so they inherit the
surrounding text colour and work on light and dark alike; only the accents are
fixed (gold for the hat band, green for done).

| glyph | meaning |
| --- | --- |
| `hat` | the orchestrator |
| `broom` | a worker, queued |
| `broom-run` | a worker running |
| `brooms` | several workers in parallel |
| `broom-done` | a worker finished |

## On the source material and copyright

The imagery comes from the *story*, which is free to use, not from Disney's
film, which is not:

- Goethe's ballad *Der Zauberlehrling* (1797) and Paul Dukas's tone poem
  *L'apprenti sorcier* (1897) are both in the public domain.
- Disney's *Fantasia* (1940) is **still under copyright in the United States
  until 1 January 2036** (95 years from publication). That covers the
  Sorcerer's Apprentice segment, Sorcerer Mickey in his red robe and starry
  hat, and the film's broom designs.
- Separately, Mickey Mouse is a live Disney **trademark**, which does not
  expire. Even the 1928 *Steamboat Willie* design — in the public domain in
  the US since 1 January 2024 — cannot be used as a logo or brand identifier.

So nothing here is traced from or modelled on the film. These are original
drawings: a violet cone hat with a gold band and cyan sparks in the MUIOGO
palette, and plain brooms with no faces, arms or hands. Recheck the dates
before reusing any of this outside the project, and note the 2036 date applies
to US law — terms differ elsewhere.

Sources: [Duke Law, Center for the Study of the Public
Domain](https://web.law.duke.edu/cspd/mickey/) ·
[ABA](https://www.americanbar.org/groups/litigation/resources/newsletters/intellectual-property/mickey-mouse-public-domain/)

## Regenerating

```bash
python3 assets/apprentice/build_apprentice.py assets/apprentice
```

The hat's cone is generated as a tapering ribbon along a curved spine, and the
gold band and sparks are derived from that same spine — move the spine and they
follow. The wordmark and shared palette are imported from
`../headless-logo/build_logo.py`, so the brand only lives in one place.
