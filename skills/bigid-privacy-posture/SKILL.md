---
name: bigid-privacy-posture
description: >
  Generates a BigID-branded NIST Privacy Framework compliance report (PPTX) by pulling
  live data from BigID — risk cases, privacy risks, controls, and framework status.
  Use this skill whenever the user asks to refresh, regenerate, update, or create
  their privacy posture report, NIST-P report, compliance deck, or privacy dashboard.
  Also trigger for: "update my privacy report", "refresh the posture deck",
  "how's our NIST-P score", "give me a compliance slide deck", "show me
  findings per control", or "break down the NIST controls in detail".
  The skill produces a ~35-slide detailed deck: executive summary, a dark section-header
  per NIST-P function, one drilldown slide per control listing every open risk case
  (case ID, data source, risk score, controls count), and a prioritized remediation
  roadmap — all sourced live from BigID.
compatibility: "Requires: BigID cloud MCP server (get_objects — Privacy Risk Cases API, Privacy Risks, Risk Controls, Regulations). bash_tool, present_files. npm: pptxgenjs. Assets: /mnt/skills/user/bigid-pptx/logo_h_transparent.png and gradient_bar.png."
---

# BigID Privacy Posture Report Skill

Generates a 10-slide BigID-branded NIST Privacy Framework posture deck from live BigID data.

## When to use

Any time the user wants a fresh view of their privacy compliance posture. Common triggers:
- "refresh my privacy posture report"
- "update the NIST-P deck"
- "how are we doing on privacy compliance?"
- "regenerate the compliance slide deck"
- "what's our privacy risk score?"

---

## Workflow

Follow these 4 steps in order.

### Step 1 — Pull live data from BigID

Make these API calls in parallel. Store all results for use in Step 2.

```
get_objects("Privacy Risk Cases API", "get_v1_privacy_risk_cases", {"limit": 200})
get_objects("Privacy Risks", "get_v1_privacy_risks", {"limit": 200})
get_objects("Risk Controls", "get_v1_controls", {})
```

Also call:
```
get_objects("Regulations", "get_v1_compliance_frameworks", {})
```
to get current framework enable/disable status (useful for noting newly enabled frameworks in the report).

**Parsing notes:**
- Risk cases: response is `{data: [...]}` — access as `response.data`. Each case has `caseId`, `caseLabel`, `privacyRisk` (object with `name`, `category`), `controls[]`, `riskLevel`, `probability`, `impact`, `source` (object with `name`).
- Privacy risks: response is `{rules: [...]}` — access as `response.rules` (NOT `response.data.rules`). Each rule has `name`, `category`, `probability`, `impact`, `mappedControls[]` (or `controls[]`).
- Controls: each has `id`, `name`, `category` (contains NIST-P function ID like "CT.DP-P1").
- Compliance frameworks: each has `framework_name`, `enabled`, and a list of controls.
- If any tool result is stored to a file (too large for context), use `bash_tool` to parse it with Python.

### Step 2 — Score the 5 NIST-P functions

Map the live data to NIST Privacy Framework functions using the scoring logic in `references/scoring.md`.

The 5 functions and their control mappings:

| Function | Controls |
|---|---|
| IDENTIFY-P (ID) | ID.IM-P1 through ID.IM-P4, ID.RA-P1 through ID.RA-P4 |
| GOVERN-P (GV) | GV.PO-P1 through GV.PO-P4 |
| CONTROL-P (CT) | CT.DP-P1 through CT.DP-P5 |
| COMMUNICATE-P (CM) | CM.CO-P1 through CM.CO-P4 |
| PROTECT-P (PR) | PR.DS-P1 through PR.DS-P5 |

For each control, assign status:
- **In Place** — control exists in BigID and no open risk cases target it → contributes full score
- **Partial** — control exists but open risk cases overlap with it → contributes half score  
- **Gap** — control exists but multiple high-impact cases are unresolved, or key capabilities are missing → contributes zero

Derive a percentage score per function based on how many controls are In Place / Partial / Gap.

See `references/scoring.md` for full scoring rubric and control-to-risk-case mapping logic.

### Step 3 — Generate the PPTX

Write a Node.js script to `/home/claude/privacy_posture_report.js` using the data from Step 1 and scores from Step 2. Then run it with `bash_tool`.

**Always use the BigID branding template** — see `references/pptx-template.md` for the full constants block and `applyBigIDBranding()` function. Copy it verbatim.

**Slide structure (~35 slides total):**

1. **Cover** — Title, date, overall score hero banner (dark navy, white text), function score strip at bottom
2. **Executive Summary** — 5 function score cards with In Place/Partial/Gap counts, new-case callout

For each of the 5 NIST-P functions (IDENTIFY, GOVERN, CONTROL, COMMUNICATE, PROTECT):
- **Section Header** (full dark navy) — function name, description, score, In Place/Partial/Gap pills, total open findings count
- **One slide per control** — dark header band with control ID pill, name, status badge; coloured assessment banner; findings table sorted by score showing Case ID / Risk / Data Source / Score badge / Controls-count badge. Controls with no cases get a green "No open risk cases" panel. Overflow (>9 rows) adds "+N additional" note.

**Final slides:**
- **Priority Remediation Roadmap** — 4-column P1/P2/P3/P4 layout
- **Closing** — score summary recap panel on right

**Status badge colors:**
- In Place → `"2E7D32"` (green)
- Partial → `"F57F17"` (amber)
- Gap → `"C62828"` (red)

**Risk score badge colors:**
- score ≥ 12 → `"C62828"` (red)
- score 8–11 → `"F57F17"` (amber)  
- score < 8 → `"2E7D32"` (green)

**Controls count badge:**
- 0 controls → `"C62828"` (red — uncontrolled)
- > 0 controls → `"F57F17"` (amber)

Output file: `/mnt/user-data/outputs/BigID_NIST_Privacy_Posture_Detailed.pptx`

### Step 4 — Deduplicate images (REQUIRED for Claude preview)

PptxGenJS embeds a separate copy of the logo and gradient bar into every slide. With 35 slides this bloats the file to ~1.5 MB, which exceeds the Claude interface's PPTX preview limit. This step collapses all identical images to a single shared copy, shrinking the file to ~150 KB so it renders in the preview panel.

Run this immediately after generating the PPTX, before QA:

```python
import zipfile, shutil, hashlib, os
from pathlib import Path

SRC = DST = "/mnt/user-data/outputs/BigID_NIST_Privacy_Posture_Detailed.pptx"
TMP = "/tmp/pptx_dedupe"

if os.path.exists(TMP): shutil.rmtree(TMP)
os.makedirs(TMP)
with zipfile.ZipFile(SRC, 'r') as z:
    z.extractall(TMP)

media_dir = Path(TMP) / "ppt" / "media"
hash_to_canonical, remap = {}, {}
for f in sorted(media_dir.iterdir()):
    if not f.is_file(): continue
    h = hashlib.md5(f.read_bytes()).hexdigest()
    if h not in hash_to_canonical:
        hash_to_canonical[h] = f.name
    else:
        canonical = hash_to_canonical[h]
        if f.name != canonical:
            remap[f.name] = canonical
            f.unlink()

rels_root = Path(TMP) / "ppt" / "slides" / "_rels"
for rels_file in rels_root.glob("*.rels"):
    content = rels_file.read_text()
    for old, new in remap.items():
        content = content.replace(f"../media/{old}", f"../media/{new}")
    rels_file.write_text(content)

os.unlink(DST)
with zipfile.ZipFile(DST, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, files in os.walk(TMP):
        for file in files:
            full = os.path.join(root, file)
            z.write(full, os.path.relpath(full, TMP))

print(f"Done: {os.path.getsize(DST)/1024:.0f} KB (was ~1500 KB)")
```

Save this as `/home/claude/dedupe_images.py` and run with `python3 /home/claude/dedupe_images.py`. The output should be under 200 KB.

### Step 5 — QA and deliver

```bash
cp /mnt/user-data/outputs/BigID_NIST_Privacy_Posture_Detailed.pptx /home/claude/
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf /home/claude/BigID_NIST_Privacy_Posture_Detailed.pptx
mv /BigID_NIST_Privacy_Posture_Detailed.pdf /home/claude/ 2>/dev/null || true
pdftoppm -jpeg -r 120 /home/claude/BigID_NIST_Privacy_Posture_Detailed.pdf /home/claude/qa_slide
```

Check slides 1, 2, one dark section header, and one control drilldown. Confirm logo and gradient bar are visible (dedup preserves both). LibreOffice may wrap bold titles slightly differently than PowerPoint — this is expected.

Then call `present_files` with the PPTX path and give a brief summary of what changed vs the previous report (if the user mentioned a prior one), or a headline summary of key findings.

---

## Output summary format

After presenting the file, give a 4-line summary:

```
Overall score: XX% (▲/▼ vs last run if known)
Biggest gap: [function name] at XX% — [one-line reason]
Most urgent risk: [risk name] on [data source] — score XX, X controls
Next action: [single most important P1 item]
```

---

## Error handling

- If the BigID cloud MCP is unavailable, tell the user and stop — do not generate a report with stale data.
- If a tool result is too large, it will be stored to a file path — use `bash_tool` with Python to parse it (see Step 1 parsing notes).
- If `pptxgenjs` is not installed, run `npm install -g pptxgenjs` before proceeding.
- If the gradient bar or logo assets are missing at the expected paths, see the regeneration instructions in `/mnt/skills/user/bigid-pptx/SKILL.md`.

---

## Reference files

- `references/scoring.md` — Full NIST-P scoring rubric: how to map risk cases to controls, how to assign In Place / Partial / Gap status, and how to compute function-level percentages
- `references/pptx-template.md` — Complete BigID branding constants and `applyBigIDBranding()` function; copy verbatim into every generator script
