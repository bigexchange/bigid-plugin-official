# BigID PPTX Branding Template

Copy this constants block and `applyBigIDBranding()` function verbatim at the top of every generator script.

## Core Constants & Branding Function

```javascript
const pptxgen = require("pptxgenjs");

const SLIDE_W = 10;
const SLIDE_H = 5.625;
const BG_COLOR     = "F4F4F6";
const TEXT_DARK    = "2d2c31";   // titles, body text
const HEADLINE     = "3d3d3d";   // large stat numbers & display text (24pt+)
const ACCENT       = "8735ff";   // small labels only (≤14pt)
const GREY_TEXT    = "666666";   // subtitles, captions
const COLOR_PURPLE = "8735ff";
const COLOR_PINK   = "ff3592";
const COLOR_ORANGE = "ff6b35";
const DARK_NAVY    = "1e2133";

// Bundled with this skill — no dependency on any other skill. The generator
// script runs from /home/claude, so this must be an absolute path, not
// resolved relative to the script's own location.
const LOGO_PATH = "/mnt/skills/user/bigid-privacy-posture/assets/logo_white_h.png";

const FONT = "Montserrat";

const FOOTER_H = 0.07;
const FOOTER_Y = SLIDE_H - FOOTER_H;

// logo_white_h.png is 892x333px (~2.68:1). It's a white mark, so it needs a
// dark backing chip behind it to stay visible on both light (BG_COLOR) and
// dark-navy (section header / cover) slide backgrounds.
const LOGO_H   = 0.32;
const LOGO_W   = LOGO_H * (892 / 333);
const LOGO_PAD = 0.09;
const LOGO_CHIP_W = LOGO_W + LOGO_PAD * 2;
const LOGO_CHIP_H = LOGO_H + LOGO_PAD * 2;
const LOGO_CHIP_X = SLIDE_W - LOGO_CHIP_W - 0.2;
const LOGO_CHIP_Y = 0.15;
const LOGO_X = LOGO_CHIP_X + LOGO_PAD;
const LOGO_Y = LOGO_CHIP_Y + LOGO_PAD;

function applyBigIDBranding(slide) {
  slide.background = { color: BG_COLOR };

  // Dark chip behind the logo so the white mark reads on any background
  // (dark-navy section headers as well as the light BG_COLOR body slides).
  slide.addShape(pres.ShapeType.rect, {
    x: LOGO_CHIP_X, y: LOGO_CHIP_Y, w: LOGO_CHIP_W, h: LOGO_CHIP_H,
    fill: { color: DARK_NAVY }, line: { color: DARK_NAVY },
  });
  slide.addImage({ path: LOGO_PATH, x: LOGO_X, y: LOGO_Y, w: LOGO_W, h: LOGO_H });

  // Footer gradient bar — drawn as three bands (no image asset needed),
  // matching the BigID signature purple → pink → orange gradient.
  const band = SLIDE_W / 3;
  [COLOR_PURPLE, COLOR_PINK, COLOR_ORANGE].forEach((color, i) => {
    slide.addShape(pres.ShapeType.rect, {
      x: band * i, y: FOOTER_Y, w: band, h: FOOTER_H,
      fill: { color }, line: { color },
    });
  });
}
```

> **Note:** `applyBigIDBranding()` references the outer `pres` object (for `pres.ShapeType.rect`) via closure — declare `const pres = new pptxgen();` before the first slide is generated, as shown in "pres initialization" below. This is copied verbatim alongside the rest of this block, so as long as you don't reorder things, `pres` is already in scope by the time this function runs.

---

## Content Safe Zone

| Edge | Constraint |
|---|---|
| Top | y > 1.1" (clears logo) |
| Right | x + w < 8.3" (clears logo) |
| Bottom | y + h < 5.4" (clears gradient bar) |
| Left | x > 0.5" |

---

## Color Rules

- **TEXT_DARK** `#2d2c31` — All slide titles, body text, section headers
- **HEADLINE** `#3d3d3d` — Large display numbers (24pt+), subtitle lines on cover/closing slides
- **ACCENT** `#8735ff` — Small labels only (≤14pt): "Key Insight", control IDs, callout box borders, bullet dots
- **GREY_TEXT** `#666666` — Subtitles, labels, captions
- White `"ffffff"` — Text on dark backgrounds (navy, red, green, amber boxes)
- **Never use `#` prefix** — PptxGenJS corrupts on hex with hash

---

## Standard Title Helper

```javascript
function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.5, y: 0.22, w: 8.3, h: 0.55,
    fontSize: 24, bold: true, color: TEXT_DARK, fontFace: FONT,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.78, w: 8.3, h: 0.28,
      fontSize: 11, color: GREY_TEXT, fontFace: FONT,
    });
  }
}
```

---

## Key Layout Patterns

### Hero Banner (dark background + big number)
```javascript
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: 0.9, w: 9.0, h: 1.35,
  fill: { color: "1e2133" }, line: { color: "1e2133" },
});
s.addText("Label", { x: 0.75, y: 0.97, w: 4, h: 0.3,
  fontSize: 11, color: "aaaaaa", fontFace: FONT });
s.addText("53%", { x: 0.75, y: 1.22, w: 2.5, h: 0.85,
  fontSize: 52, bold: true, color: "ffffff", fontFace: FONT });
```

### Stat Cards (function score cards)
```javascript
// Outline only — white fill, colored border
s.addShape(pres.ShapeType.rect, {
  x, y: 1.1, w: 1.65, h: 1.55,
  fill: { color: "ffffff" }, line: { color: outlineColor, width: 1.5 },
});
// Large score → HEADLINE color (not ACCENT)
s.addText("68%", { x, y: 1.45, w: 1.65, h: 0.65,
  fontSize: 34, bold: true, color: HEADLINE, fontFace: FONT, align: "center" });
```

### Data Table (dark header + alternating rows)
```javascript
// Header
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: 1.1, w: 9.0, h: 0.34,
  fill: { color: "1e2133" }, line: { color: "1e2133" },
});
// Row (alternating white / light grey)
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: rowY, w: 9.0, h: rowH,
  fill: { color: i % 2 === 0 ? "ffffff" : "f7f7fa" },
  line: { color: "e5e7eb", width: 0.5 },
});
```

### Status Badge
```javascript
const statusColors = { "In Place": "2E7D32", "Partial": "F57F17", "Gap": "C62828" };
s.addShape(pres.ShapeType.rect, {
  x: badgeX, y: rowY + 0.09, w: 1.1, h: 0.26,
  fill: { color: statusColors[status] }, line: { color: statusColors[status] },
});
s.addText(status, { x: badgeX, y: rowY + 0.10, w: 1.1, h: 0.24,
  fontSize: 8, bold: true, color: "ffffff", fontFace: FONT, align: "center" });
```

### Callout / Insight Box
```javascript
// Key Insight box (neutral grey bg, purple accent bar)
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: 3.98, w: 9.0, h: 1.18,
  fill: { color: "f0f0f5" }, line: { color: COLOR_PURPLE, width: 1.5 },
});
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: 3.98, w: 0.06, h: 1.18,
  fill: { color: COLOR_PURPLE }, line: { color: COLOR_PURPLE },
});
s.addText("Key Insight", { x: 0.72, y: 4.05, w: 8.5, h: 0.28,
  fontSize: 12, bold: true, color: ACCENT, fontFace: FONT });
s.addText("Body copy here.", { x: 0.72, y: 4.32, w: 8.5, h: 0.75,
  fontSize: 11.5, color: TEXT_DARK, fontFace: FONT });
```

### Warning / Critical Alert
```javascript
// Orange warning
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: alertY, w: 9.0, h: 0.62,
  fill: { color: "fff3e0" }, line: { color: COLOR_ORANGE, width: 1.5 },
});
// Red critical
s.addShape(pres.ShapeType.rect, {
  x: 0.5, y: alertY, w: 9.0, h: 0.62,
  fill: { color: "fce4e4" }, line: { color: "C62828", width: 1.5 },
});
```

---

## Common Pitfalls

- **Never use `#` with hex colors** — breaks PptxGenJS silently
- **Never reuse options objects** — PptxGenJS mutates them in-place
- **Never use colored box backgrounds** — outlines only, fills stay white or neutral grey
- **Large text on dark backgrounds** → always white `"ffffff"`, never HEADLINE or ACCENT
- **Large purple text on light bg** → avoid; use HEADLINE (charcoal) for display-size text
- **Score numbers at 24pt+** → use HEADLINE, not ACCENT
- **Card titles wrapping in LibreOffice preview** → expected; renders correctly in PowerPoint

---

## pres initialization

```javascript
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
// ... add slides ...
pres.writeFile({ fileName: "/mnt/user-data/outputs/BigID_NIST_Privacy_Posture_Detailed.pptx" })
  .then(() => console.log("✅ PPTX generated successfully."))
  .catch(e => { console.error(e); process.exit(1); });
```
