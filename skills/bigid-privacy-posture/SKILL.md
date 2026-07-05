---
name: bigid-privacy-posture
description: >
  Generates a BigID-branded NIST Privacy Framework (NIST-P) posture report (PPTX) by
  pulling live data from BigID — risk cases, privacy risks, and controls. Use this
  skill whenever the user asks to refresh, regenerate, update, or create their
  privacy posture report, NIST-P report, or NIST-P score/deck. Also trigger for:
  "update my privacy report", "refresh the posture deck", "how's our NIST-P score",
  "show me findings per control", or "break down the NIST controls in detail".
  Do NOT trigger for a compliance report or dashboard against a named regulation,
  law, or framework (GDPR, HIPAA, EO 14117, OSFI B-13, SOC 2, ISO 27001, etc.) —
  that belongs to a different skill; confirm which the user means if it's unclear.
  The skill produces a ~35-slide detailed deck: executive summary, a dark section-header
  per NIST-P function, one drilldown slide per control listing every open risk case
  (case ID, data source, risk score, controls count), and a prioritized remediation
  roadmap — all sourced live from BigID.
compatibility: "Requires: BigID cloud MCP server (get_objects — Privacy Risk Cases API: get_privacy_risk_cases; Privacy Risks: get_privacy_risks; Risk Controls: get_controls), and the Privacy Risk module licensed on the tenant. The compliance-frameworks enrichment call has no confirmed working server/tool in this environment as of 2026-07-05 — see Step 2 note. bash_tool, present_files. npm: pptxgenjs. Assets: bundled in ./assets/logo_white_h.png — no other skill needed."
---

# BigID Privacy Posture Report Skill

Generates a ~35-slide BigID-branded NIST Privacy Framework posture deck (cover, executive summary, one section-header + one drilldown slide per control, remediation roadmap, closing) from live BigID data.

> **Scope (also stated in the frontmatter description, which is what actually drives triggering — kept here too for humans reading this file):** this skill is specifically the NIST Privacy Framework (NIST-P) posture deck. If the user asks for compliance evidence against a named regulation (GDPR, HIPAA, EO 14117, OSFI B-13, etc.) rather than a NIST-P score/deck, confirm which they mean before proceeding rather than assuming this skill applies.

## When to use

Any time the user wants a fresh view of their NIST-P privacy posture, with no named regulation involved. Common triggers:
- "refresh my privacy posture report"
- "update the NIST-P deck"
- "how are we doing on privacy compliance?" (in the NIST-P sense, not a named regulation)
- "what's our privacy risk score?"
- "break down the NIST controls in detail"

**Not for:** a compliance report or dashboard against a named regulation, law, or framework (GDPR, HIPAA, EO 14117, OSFI B-13, SOC 2, ISO 27001, etc.) — confirm which the user means if it's unclear, rather than assuming this skill applies.

---

## Workflow

Follow these steps in order.

### Step 1 — Confirm license / permissions

Before pulling the rest of the data, confirm the tenant has the Privacy Risk module enabled and the calling user has access to it:

```
get_objects("Privacy Risks", "get_privacy_risks", {"limit": 1})
```

If this call fails with an auth/license/permission error (403, "module not licensed", "insufficient permissions", or similar), **stop immediately** and tell the user plainly, e.g.:

> "I can't generate this report — the Privacy Risk module isn't licensed (or isn't accessible with your current role) on this BigID tenant. Ask your BigID admin to enable Privacy Risk access before I can pull this data."

If it instead fails with an "Unknown server"/"Unknown tool" error, that's a different problem — see Troubleshooting's "Unknown server / unknown tool error" entry; don't treat it as a license failure.

Do not fall back to a partial or cached report in this case. If the call succeeds, you can skip re-fetching the first page in Step 2 and just pull the rest.

### Step 2 — Pull live data from BigID

Make these API calls in parallel. Store all results for use in Step 3.

```
get_objects("Privacy Risk Cases API", "get_privacy_risk_cases", {"limit": 200})
get_objects("Privacy Risks", "get_privacy_risks", {"limit": 200})
get_objects("Risk Controls", "get_controls", {})
```

**Optional enrichment — compliance framework enable/disable status.** This would be
useful for noting newly enabled frameworks in the report, but **there is currently no
confirmed working server/tool for this in the connected BigID MCP** — `Regulations` /
`get_v1_compliance_frameworks` (the names previously written here) do not exist. If
you have a working replacement (check `list_servers()` / `list_tools()` for something
compliance-framework-shaped), use it and treat it as enrichment only. Otherwise, skip
this pull entirely and don't block report generation on it — it was never load-bearing
for the NIST-P scores themselves (see Step 3), only for a "newly enabled framework"
callout. **This is a known gap the skill owner should resolve** — see `compatibility`
in the frontmatter.

**Parsing notes:**
- Risk cases: response is `{riskCases: [...]}` — access as `response.riskCases` (**not** `response.data` — the field is `riskCases`, confirmed against a live call). Each case has `caseId`, `caseLabel`, `privacyRisk` (object with `name`, `category`), `controls[]`, `riskLevel`, `probability`, `impact`, `source` (object with `name`).
- Privacy risks: response is `{rules: [...]}` — access as `response.rules` (NOT `response.data.rules`). Each rule has `name`, `category`, `probability`, `impact`, `mappedControls[]` (or `controls[]`). In practice `mappedControls` is often empty — expect to lean on the category-based fallback mapping in `references/scoring.md` rather than `mappedControls` alone.
- Controls: each has `id`, `name`, `category`. **Verify before scoring** that `category` actually contains a NIST-P function ID pattern like `CT.DP-P1` — on at least one observed tenant, `get_controls` returned only controls from an unrelated framework (e.g. "Zero Trust Architecture") with no NIST-P-pattern entries at all, and this call takes no filter parameter to scope it. See Step 3's required pre-check before assuming this data is usable.
- If any tool result is stored to a file (too large for context), use `bash_tool` to parse it with Python.

### Step 3 — Score the 5 NIST-P functions

**Required pre-check before scoring anything:** confirm that the `controls` data from
Step 2 actually contains entries whose `category` matches the NIST-P ID pattern (e.g.
`CT.DP-P1`, `ID.IM-P1`). If **zero** returned controls match this pattern across the
entire result set:

> **Stop and tell the user, rather than scoring.** This is not the same as "every
> control is a Gap" — it means the NIST Privacy Framework doesn't appear to be
> configured on this BigID tenant (or `get_controls` needs a filter this skill
> doesn't currently know about), and generating scores anyway would silently imply a
> catastrophic privacy posture that may just be a missing setup. Say something like:
> "I can't score this report — none of the controls returned from BigID match the
> NIST Privacy Framework's ID pattern. Either the NIST-P framework isn't configured
> on this tenant, or I'm missing a filter to scope the controls call correctly. Can
> you confirm the NIST-P framework is enabled in BigID, or point me to the right
> control set?"

Only proceed to scoring if at least some controls match the expected pattern. If only
*some* functions have matching controls and others don't, score the functions that
have data normally and flag the ones that don't as "not configured" rather than
scoring them as 0%/Gap.

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

### Step 4 — Generate the PPTX

Write a Node.js script to `/home/claude/privacy_posture_report.js` using the data from Step 2 and scores from Step 3. Then run it with `bash_tool`.

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

### Step 5 — Deduplicate images (REQUIRED for Claude preview)

PptxGenJS embeds a separate copy of the logo image into every slide (the footer bar is drawn with shapes, not an image, so it isn't affected). With 35 slides this bloats the file to ~1.5 MB, which exceeds the Claude interface's PPTX preview limit. This step collapses all identical logo copies to a single shared copy, shrinking the file to well under 200 KB so it renders in the preview panel.

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

### Step 6 — QA and deliver

```bash
cp /mnt/user-data/outputs/BigID_NIST_Privacy_Posture_Detailed.pptx /home/claude/
python3 /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf /home/claude/BigID_NIST_Privacy_Posture_Detailed.pptx
mv /BigID_NIST_Privacy_Posture_Detailed.pdf /home/claude/ 2>/dev/null || true
pdftoppm -jpeg -r 120 /home/claude/BigID_NIST_Privacy_Posture_Detailed.pdf /home/claude/qa_slide
```

Check slides 1, 2, one dark section header, and one control drilldown. Confirm the logo is visible on both light and dark backgrounds and the footer gradient bar renders as a clean purple→pink→orange band. LibreOffice may wrap bold titles slightly differently than PowerPoint — this is expected.

Then call `present_files` with the PPTX path and give a brief summary of what changed vs the previous report (if the user mentioned a prior one), or a headline summary of key findings.

---

## Follow-up actions

After presenting the file, offer one relevant next step based on what's actually connected — don't just list all of these:

- **Slack connected** — offer to post the headline summary (score, biggest gap, most urgent risk) to a channel via `Slack:slack_send_message`.
- **Atlassian/Jira connected** — offer to open a Jira issue for the single most urgent P1 remediation item via `Atlassian:createJiraIssue`, pre-filled with the risk name, data source, and score.
- **Neither connected** — just offer to re-run the report later or drill into a specific function/control in chat.

Never create the Slack post or Jira issue without the user confirming first.

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

## Error handling / troubleshooting

- **BigID MCP unavailable** — tell the user and stop; do not generate a report with stale data.
- **License/permission error on Step 1** — stop immediately per Step 1; never fall back to a partial report.
- **Unknown server / unknown tool error** (e.g. `{"error":"Unknown server"}` or
  `{"error":"Unknown tool '...'"}`) — **different from a license gap or a transient
  error; don't treat it as either.** It means a tool/server name in this SKILL.md is
  stale or wrong, not that access is denied, and retrying won't help.
  1. Don't retry it.
  2. Don't silently render the section as "Data unavailable" — that fallback is for
     transient/empty results, and would misrepresent a broken skill reference as a
     normal data gap.
  3. Run `list_servers()` and, if needed, `list_tools("<server>")` to check for a
     renamed/correct equivalent.
  4. If found, use it for this run and tell the user the skill's reference is stale
     and should be updated.
  5. If not found (this currently applies to the compliance-frameworks enrichment
     pull — see Step 2), skip that specific piece if it's non-essential (as that one
     is), or stop and name the broken pull if it's essential (Steps 1-2's core three
     calls are essential).
- **NIST-P framework not configured / no matching controls** — see Step 3's required
  pre-check. Stop and ask the user to confirm the framework is enabled, rather than
  scoring every function as a Gap.
- **Tool result too large** — it will be stored to a file path; use `bash_tool` with Python to parse it (see Step 2 parsing notes).
- **`pptxgenjs` not installed** — run `npm install -g pptxgenjs` before proceeding.
- **Logo or footer-bar rendering looks wrong** — the logo lives at `./assets/logo_white_h.png`, bundled with this skill (no other skill needed). The footer bar is drawn as three colored rectangles in `applyBigIDBranding()`, not an image — if it's missing, check the function was copied verbatim from `references/pptx-template.md`.
- **Zero open risk cases across the board** — this is a valid (good) result, not an error. Score every control "In Place", show the green "No open risk cases" panel on every control slide, and say so explicitly in the Executive Summary and the 4-line output summary — don't treat an empty result set as a fetch failure.
- **Missing or unexpected fields on a case/rule** (e.g. no `riskLevel`, no `controls[]`) — treat the field as unknown rather than failing the whole run: skip that case from scoring impact but still list it in the relevant findings table with a "—" placeholder, and note the gap in your summary to the user.
- **Ambiguous ask** (e.g. user says "how's compliance" with no NIST-P mention) — if the user has previously used this skill or explicitly says "NIST-P"/"posture deck", proceed; otherwise briefly confirm whether they want the NIST-P posture deck or a regulation-specific compliance report before generating anything.

---

## Reference files

- `references/scoring.md` — Full NIST-P scoring rubric: how to map risk cases to controls, how to assign In Place / Partial / Gap status, and how to compute function-level percentages
- `references/pptx-template.md` — Complete BigID branding constants and `applyBigIDBranding()` function; copy verbatim into every generator script
- `assets/logo_white_h.png` — Bundled BigID logo used by `applyBigIDBranding()`; no external skill dependency
