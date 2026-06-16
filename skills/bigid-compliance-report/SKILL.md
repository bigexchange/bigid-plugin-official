---
name: bigid-compliance-report
description: >
  Generates a compliance evidence report (PDF) using live data from the BigID MCP,
  mapped against a chosen regulation. Use this skill whenever someone asks to produce,
  generate, prove, or document compliance using BigID — for any regulation including
  EO 14117, GDPR, HIPAA, or a custom org policy. Trigger phrases include: "compliance
  report", "prove we comply", "show compliance posture", "audit evidence from BigID",
  "data privacy compliance report", "generate a BigID report for [regulation]", or
  any mention of BigID alongside a regulation or compliance requirement. Always use
  this skill when BigID is connected and a compliance report or evidence document is
  the goal, even if the user doesn't name a specific regulation yet.
---

# BigID Compliance Report

Generates a regulation-specific compliance evidence PDF using live BigID MCP data.
Supports EO 14117, GDPR, HIPAA, OSFI B-13 (Canada), and custom org policies uploaded
by the user.

> **Tool naming:** Some long tool names are rendered with a double underscore — notably
> `get_data__categories` (Data Categories API). Call tools verbatim as written below. If
> a call returns an unknown-tool error, run `list_tools("<server>")` to confirm the name.

## Step 1 — Choose a regulation

If the user hasn't specified a regulation, ask:

> Which regulation should this report cover?
> - **EO 14117** — US Executive Order on Bulk Sensitive Data & Countries of Concern
> - **GDPR** — EU General Data Protection Regulation
> - **HIPAA** — US Health Insurance Portability and Accountability Act
> - **OSFI B-13** — Canada — OSFI Guideline B-13, Technology & Cyber Risk Management
> - **Upload your policy** — Upload your own policy document

Wait for their answer before continuing.

### Custom / uploaded policy — required handling

When the user picks **Upload your policy**, the report must still conform to the
Repeatability contract and the nine canonical sections (Step 5). A custom policy
changes the *content* of sections 3, 4, and 7 — never the structure. Follow these
guidelines exactly:

1. **Read the policy** — save the upload path and read it (use the file-reading skill
   for non-text formats: `extract-text` for docx/xlsx/pptx, the pdf-reading skill for
   PDFs). Do not skim — you need the actual obligations.
2. **Extract obligations into a normalized control list.** Convert the policy into a
   table with these exact columns, because this becomes the §7 controls skeleton:
   `Control area | Requirement ref | What it requires | Mapped BigID evidence`.
   - `Requirement ref` = the policy's own section/clause number (e.g. "§4.2"), so the
     report cites the source policy, not a regulation.
   - `Mapped BigID evidence` = which live pull demonstrates it (cases by policy,
     category coverage, framework status, ownership, etc.). If a requirement has no
     possible BigID evidence, mark it `Out of scope for BigID` — keep the row, don't
     silently drop it.
3. **Map each requirement to a data type** for the §4 Data Landscape table, using the
   same BigID categories the built-in references use.
4. **Confirm with the user before building.** Present the normalized control list back
   and ask them to confirm or correct it. Wait for confirmation. This is the only
   regulation path with a mandatory confirmation gate, because the requirements are
   user-supplied rather than from a vetted reference file.
5. **Treat the confirmed control list as the reference file** — it supplies exactly
   what `references/*.md` supplies for built-in regulations (regulatory facts → the
   policy's own scope/purpose; category mapping; controls skeleton; section outline =
   the fixed nine). Skip the Step 2 web search (it's an internal policy, not public law)
   and say so in the Executive Summary.
6. **Status vocabulary and all table shapes are unchanged** — a custom policy uses the
   same closed status set and the same fixed columns as every other report.
7. **Filename:** slugify the policy title → `<PolicySlug>_Compliance_Report.pdf`
   (e.g. "Acme Data Handling Standard" → `Acme_Data_Handling_Standard_Compliance_Report.pdf`).

If the uploaded file is not actually a policy (e.g. it has no obligations/requirements),
say so and ask the user for a policy document rather than fabricating controls.

## Step 2 — Research regulatory updates (web search)

Before pulling BigID data, do a quick web search to surface any significant
enforcement changes or regulatory updates from the last 6 months that should be
reflected in the report. Use a query like:

```
"[REGULATION NAME] compliance updates 2025 2026 enforcement"
```

Keep this brief — one search, pull the top findings, and note anything material
(new deadlines, amended articles, recent enforcement actions) in the report's
Executive Summary. Skip this for uploaded policies.

## Step 3 — Pull live data from BigID

Run all of these calls. Use `BigID MCP Production:get_objects` for every read.

### 3a. Compliance frameworks
```
server_name: "Regulations"
tool_name:   "get_compliance_frameworks"
arguments:   {}
```
Find the framework matching the chosen regulation (see reference file for name).
Note its `id` and enabled status.

### 3b. Policy compliance summary
```
server_name: "Policies API"
tool_name:   "get_complianceSummaries"
arguments:   {}
```
Returns pass / fail / assigned counts across all active policies.

### 3c. Security cases by severity
```
server_name: "Security Posture"
tool_name:   "get_actionable_insights_cases_by_severity"
arguments:   {}
```

### 3d. Top critical cases
```
server_name: "Security Posture"
tool_name:   "get_actionable_insights_top_critical_cases"
arguments:   {}
```

### 3e. Open cases grouped by policy
```
server_name: "Security Posture"
tool_name:   "get_actionable_insights_cases_group_by_policy"
arguments:   { "caseStatus": "open" }
```

### 3f. Data categories
```
server_name: "Data Categories API"
tool_name:   "get_data__categories"
arguments:   {}
```

### 3g. OSFI B-13 only — coverage ratio & data-source ownership

These feed B-13's Governance domain (data classification coverage and IT ownership).
Run only when the chosen regulation is OSFI B-13.

**Sensitive-data coverage ratio** — two counts from the Data Catalog:
```
server_name: "Data Catalog"
tool_name:   "get_data_catalog_count"
arguments:   {}                                   # total objects
```
```
server_name: "Data Catalog"
tool_name:   "get_data_catalog_count"
arguments:   { "filter": "total_pii_count > 0" }  # objects with findings
```
Compute `(with findings / total) * 100` as the sensitive-data coverage percentage.

**Data-source ownership** (optional enrichment) — the data-sources read is a POST with
body filters:
```
server_name: "Data Sources API"
tool_name:   "post_ds_connections"
arguments:   { "query": { "limit": 200 } }
```
Check whether `owners_v2` is populated per source. Missing IT ownership is itself a
B-13 Governance gap (Principle 2 / 6) — call it out in the report.

**Large responses** may be saved to disk rather than returned inline. Parse them with:
```bash
python3 -c "
import json
with open('/mnt/user-data/tool_results/<filename>.json') as f:
    raw = json.load(f)
# result is usually raw[0]['text'] or raw.get('result') — a JSON string, parse again
"
```

**502 / empty responses**: note the failure, continue with available data, and mark
the affected section as "Data unavailable at time of report generation."

## Step 4 — Load the regulation reference file

Read the appropriate reference file **before** building the report:

| Regulation | Reference file |
|---|---|
| EO 14117 | `references/eo14117.md` |
| GDPR | `references/gdpr.md` |
| HIPAA | `references/hipaa.md` |
| OSFI B-13 | `references/osfi-b13.md` |
| Upload your policy | No reference file — use the requirements you extracted in Step 1 |

The reference file contains: the controls mapping skeleton, relevant BigID category
mappings, hardcoded regulatory facts, and the report section outline specific to
that regulation.

> **Reference-file contract:** every `references/*.md` must conform to the Step 5
> Repeatability contract — it may define section *content* but must map onto the fixed
> nine canonical headings without merging, renaming, or renumbering them, and must use
> the closed status vocabulary and fixed table column sets. If you add or edit a
> reference file, align it to the contract.

## Step 5 — Generate the PDF

Install dependencies:
```bash
pip install reportlab --break-system-packages -q
```

**Design system** — use consistently across all reports:

| Element | Value |
|---|---|
| Page size | A4 |
| Margins | 2 cm all sides |
| Primary color | `#1F3864` (dark navy) |
| Accent color | `#2E5090` (mid blue) |
| Pass / Met | `#1A7A2E` (green) |
| In Progress / Monitored | `#E07B00` (amber) |
| Fail / Critical | `#C0392B` (red) |
| Font (body) | Helvetica |
| Font (headings) | Helvetica-Bold |

**Every report must include these sections** (regulation-specific content comes
from the reference file):

1. **Cover page** — regulation name, org name (if known), report date, data source
   (BigID MCP), confidentiality notice
2. **Executive Summary** — 2–3 paragraphs: what the regulation requires, how BigID
   operationalises compliance, overall status. Include any regulatory updates from
   Step 2.
3. **Regulatory Overview** — key requirements, penalties/scope, relevant dates.
   Pull from the reference file.
4. **Data Landscape** — BigID data categories mapped to the regulation's data types
   (from the reference file's category mapping table)
5. **Compliance Frameworks Active** — table of BigID frameworks, their control counts,
   and enabled status from Step 3a
6. **Policy & Security Posture** — policy pass/fail summary (Step 3b), cases by
   severity (Step 3c), top critical cases table (Step 3d)
7. **Controls Compliance Mapping** — the regulation's specific controls mapped to
   BigID evidence and status (from reference file)
8. **Open Items & Remediation Plan** — derived from Step 3e open cases
9. **Conclusion & Attestation** — numbered attestation list with live data cited

### Repeatability contract (applies to EVERY report, all regulations and custom policies)

The section *list* above is fixed, but to make reports genuinely repeatable in content
and structure, the following are also invariant. Do not improvise around them.

- **Section count, order, headings, and numbering are exactly the nine above.** Never
  merge, split, reorder, rename, or add sections. A regulation needing more depth puts
  it *inside* section 7, not in a new top-level section. (The reference file may
  describe section content, but must not change the nine canonical headings.)
- **Heading text is verbatim** — use the exact titles above (e.g. "Open Items &
  Remediation Plan"), not paraphrases.
- **Status vocabulary is a closed set.** Use only these labels, mapped to the design
  colours; never invent synonyms:
  - Control/requirement level: `Met` (green) / `Partially met` (amber) / `Not met` (red).
  - Domain/section rollup: `Compliant` / `Partially compliant` / `Non-compliant`.
  - Case/finding severity: `Critical` / `High` / `Medium` / `Low`.
- **Fixed table shapes** (same columns, same order, every run):
  - Frameworks (§5): `Framework | Controls | Enabled`
  - Cases by severity (§6): `Severity | Open cases | Key exposure`
  - Top critical cases (§6): `Case | Severity | Affected objects | Data source`
  - Controls mapping (§7): `Control area | Requirement ref | BigID evidence | Status`
  - Remediation (§8): `Priority | Action | Linked finding | Timeframe`
  - Risk/attestation rollup (§9): `Domain/Area | Status | Key gap`
- **Fixed length budget** (keep reports comparable, not sprawling): Executive Summary
  2–3 paragraphs; Regulatory Overview ≤1 page; each prose gap-analysis entry in §7
  2–4 sentences. Tables are unbounded by row count but fixed in columns.
- **Remediation timeframe buckets are fixed:** Immediate (0–30 days), Short-term
  (30–90 days), Medium-term (90–180 days). Every action lands in exactly one.
- **Determinism:** sort every table by a stable key (severity desc then affected-object
  count desc for cases; control area order as listed in the reference file for §7).
  Given the same BigID data, two runs must produce the same ordering.
- **Missing data is stated, never invented:** if a pull is empty/errored, render the
  section with "Data unavailable at time of report generation" — do not drop the
  section and do not estimate.
- **Filename is fixed:** `[REGULATION]_Compliance_Report.pdf` (custom policies use a
  slugged policy name — see Step 1).

**ReportLab patterns to follow:**
- Use `SimpleDocTemplate` + `Platypus` flowables (Paragraph, Table, Spacer, PageBreak)
- Tables: use `TableStyle` with `BACKGROUND`, `TEXTCOLOR`, `GRID`, `FONTNAME`,
  `FONTSIZE`, `ROWBACKGROUNDS` for alternating rows
- Never use Unicode subscript/superscript characters — they render as black boxes
- Status cells: use coloured text (not background fill) for pass/fail labels to
  avoid contrast issues in print

## Step 6 — Write and present output

```python
doc.build(story)
# output path:
output_path = "/mnt/user-data/outputs/[REGULATION]_Compliance_Report.pdf"
```

Then call `present_files` with the output path.
