# BigID PDF Branding Template

Copy this constants block and `draw_header_footer()` function verbatim into every
generator script. This makes every compliance report visually identifiable as a
BigID-sourced document, consistent with other BigID reporting skills.

## Core Constants & Branding Function

```python
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm

# --- BigID brand identity (canonical values) ---
# Used for the logo backdrop, small accents, and the footer band only.
COLOR_PURPLE = HexColor("#8735FF")
COLOR_PINK   = HexColor("#FF3592")
COLOR_ORANGE = HexColor("#FF6B35")
BRAND_DARK   = HexColor("#2E2D32")   # headings, primary text
BRAND_GREY   = HexColor("#666666")   # captions, subtitles

# --- Functional status colors (semantic — unrelated to brand identity, do not change) ---
COLOR_MET      = HexColor("#1A7A2E")  # Pass / Met / Compliant
COLOR_PARTIAL  = HexColor("#E07B00")  # In Progress / Monitored / Partially compliant
COLOR_NOT_MET  = HexColor("#C0392B")  # Fail / Critical / Non-compliant

# --- Logo (bundled with this skill — no other skill needed) ---
LOGO_PATH = "/mnt/skills/user/bigid-regulations-and-frameworks/assets/logo_gray_v.png"
# logo_gray_v.png is 925x1304px (portrait mark). It's a dark/grey mark, so it
# reads fine directly on the plain white page background — no backing chip needed.
LOGO_W = 1.3 * cm
LOGO_H = LOGO_W * (1304 / 925)

def draw_header_footer(canvas, doc):
    """Pass as onFirstPage / onLaterPages to SimpleDocTemplate.build()."""
    canvas.saveState()

    # Logo — top-right corner of every page.
    page_w, page_h = doc.pagesize
    canvas.drawImage(
        LOGO_PATH,
        page_w - LOGO_W - 1.3 * cm,
        page_h - LOGO_H - 1.0 * cm,
        width=LOGO_W, height=LOGO_H,
        mask="auto", preserveAspectRatio=True,
    )

    # Footer gradient bar — three bands, no image asset needed.
    band_w = page_w / 3
    bar_h = 0.18 * cm
    for i, color in enumerate([COLOR_PURPLE, COLOR_PINK, COLOR_ORANGE]):
        canvas.setFillColor(color)
        canvas.rect(band_w * i, 0, band_w, bar_h, stroke=0, fill=1)

    canvas.restoreState()
```

## Wiring it into the document build

```python
doc = SimpleDocTemplate(output_path, pagesize=A4,
                         leftMargin=2*cm, rightMargin=2*cm,
                         topMargin=2*cm, bottomMargin=2*cm)
doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
```

## Color usage rules

- **BRAND_DARK** `#2E2D32` — section headings, body text (replaces any ad-hoc navy/blue).
- **COLOR_PURPLE** `#8735FF` — small accents only: section-heading underlines, table
  header backgrounds, callout borders. Not for large text blocks or body copy.
- **BRAND_GREY** `#666666` — captions, footnotes, the confidentiality notice.
- **COLOR_MET / COLOR_PARTIAL / COLOR_NOT_MET** — reserved for status labels only
  (Met/Partially met/Not met, Compliant/Partially compliant/Non-compliant,
  Critical/High/Medium/Low). Never repurpose these for brand accents or vice versa —
  keeping semantic status color separate from brand color avoids a reader confusing
  "this is BigID's color" with "this finding is critical."

## Common pitfalls

- ReportLab's `HexColor` wants the `#` prefix (opposite of PptxGenJS) — don't strip it.
- `drawImage` needs `mask="auto"` for a transparent-background PNG, or the logo will
  render with a white box behind it.
- Draw the footer bar bottom-anchored at `y=0`, not `bottomMargin` — the printable
  content area already respects `bottomMargin`; the brand bar lives in the true
  page margin below it.
