---
name: bigid-regulations-and-frameworks
description: >
  Generates a compliance evidence report (PDF) using live BigID MCP data, mapped
  against a named regulation, law, executive order, or supervisory framework — or
  an uploaded custom policy. Trigger only when the user names a specific one
  alongside BigID (e.g. "EO 14117", "GDPR", "HIPAA", "OSFI B-13"), or explicitly
  wants their own uploaded policy document checked against BigID data — e.g.
  "generate a GDPR compliance report from BigID", "prove HIPAA compliance",
  "check us against OSFI B-13", "compliance report against this policy [upload]".
  Do NOT trigger on a generic ask like "give me a compliance report" or "how's our
  compliance posture" with nothing named — ask the user which one they mean before
  proceeding, rather than assuming one.
compatibility: "Requires: BigID cloud MCP server (Regulations, Policies API, Security Posture, Data Categories API, and for OSFI B-13 also Data Catalog + Data Sources API). pip: reportlab. Assets: bundled in ./assets/logo_gray_v.png — no other skill needed."
---

# BigID Regulations & Frameworks Compliance Report

Generates a compliance evidence PDF using live BigID MCP data, mapped against a
named regulation, law, executive order, or supervisory framework. Supports EO 14117,
GDPR, HIPAA, OSFI B-13 (Canada), and custom org policies uploaded by the user.

> **Terminology note:** these four aren't all the same kind of thing, and the report
> should reflect that rather than calling everything a "regulation": GDPR is an EU
> regulation (directly binding); HIPAA is a US federal statute (its enforceable
> requirements sit in the implementing regulations at 45 C.F.R. Parts 160 & 164);
> EO 14117 is a presidential executive order (DOJ's implementing rule is what
> actually binds); OSFI B-13 is a supervisory guideline, not a statute, though OSFI
> treats it as effectively mandatory for the institutions it covers. Use the
> reference file's own language for what to call it in the report; don't default to
> "regulation" everywhere.

> **Scope:** this skill produces evidence against a *named* regulation, law, or
> framework, or the user's own uploaded policy. If the user wants a general
> privacy/security posture score with nothing specific named, confirm what they mean
> before proceeding rather than assuming one.

> **Tool naming:** Some long tool names are rendered with a double underscore — notably
> `get_data__categories` (Data Categories API). Call tools verbatim as written below. If
> a call returns an unknown-tool error, run `list_tools("<server>")` to confirm the name.

## When to use

- "generate a GDPR compliance report from BigID"
- "prove we comply with HIPAA"
- "check us against OSFI B-13"
- "generate a BigID report for EO 14117"
- "compliance report against this policy" (with an uploaded document)

**Not for:** "give me a compliance report" / "how's our compliance posture" with
nothing named — ask the user what they mean rather than assuming one.

## Step 1 — Choose a regulation, law, or framework

If the user hasn't specified one, ask:

> Which of these should this report cover?
> - **EO 14117** — US Executive Order on Bulk Sensitive Data & Countries of Concern
> - **GDPR** — EU General Data Protection Regulation
> - **HIPAA** — US Health Insurance Portability and Accountability Act
> - **OSFI B-13** — Canada — OSFI Guideline B-13, Technology & Cyber Risk Management
> - **Upload your policy** — Upload your own policy document

Wait for their answer before continuing.

### Named regulation not in the built-in list

The user's own ask may already name a regulation this skill doesn't have a built-in
reference file for (e.g. CCPA/CPRA, SOC 2, ISO 27001, PIPEDA, DORA). Don't silently
decline and don't silently force it through the uploaded-policy path — that path
assumes they *have* a document to upload, which usually isn't true for "generate a
CCPA report." Instead:

> "I don't have a built-in reference file for [NAMED REGULATION] yet — I support
> EO 14117, GDPR, HIPAA, and OSFI B-13 out of the box. I can still build you a report
> against [NAMED REGULATION] using public information about its requirements (via a
> web search, since there's no vetted reference file for it), following the same
> nine-section structure — I'll mark it as unofficial/best-effort rather than
> pulled from a vetted reference. Or, if you have your own internal policy document
> for it, I can use the Upload-your-policy path instead. Which would you prefer?"

If they choose the best-effort path:
- Treat Step 3h's web search as **required, not gap-driven**, for this regulation
  specifically — there's no reference file to fall back on, so this is the one case
  where the default-off rule in Step 3h doesn't apply.
- Skip Step 4 (no reference file to load); build the Regulatory Overview (§3) and
  Controls Compliance Mapping (§7) content directly from what the search returns,
  using the same category-mapping approach the built-in reference files use as a
  model.
- Label the report clearly, in the Executive Summary and in a footer note, as
  **"Best-effort mapping — not from a BigID-vetted reference file."** This is
  different from the custom-policy path's confirmation gate (Step 1's uploaded-policy
  handling) — there's no control list to confirm back to the user first, since it's
  built from public sources rather than their own document, so the caveat lives in
  the report itself instead.
- Everything else (status vocabulary, table shapes, nine-section structure, filename
  pattern) still follows the Repeatability contract unchanged.

If they choose the upload path instead, follow "Custom / uploaded policy — required
handling" below as normal.

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
   the fixed nine).
6. **Status vocabulary and all table shapes are unchanged** — a custom policy uses the
   same closed status set and the same fixed columns as every other report.
7. **Filename:** slugify the policy title → `<PolicySlug>_Compliance_Report.pdf`
   (e.g. "Acme Data Handling Standard" → `Acme_Data_Handling_Standard_Compliance_Report.pdf`).

If the uploaded file is not actually a policy (e.g. it has no obligations/requirements),
say so and ask the user for a policy document rather than fabricating controls.

## Step 2 — Confirm license / module access

Before pulling any data, make sure the BigID modules this report depends on are
actually licensed and accessible to the calling user. Required modules depend on
the chosen regulation:

| Data pull (Step 3) | BigID module required |
|---|---|
| 3a. Compliance frameworks | Regulations / Compliance Frameworks |
| 3b. Policy compliance summary | Policies |
| 3c–3e. Security-posture case data | Security Posture (DSPM / Actionable Insights) |
| 3f. Data categories | Data Catalog |
| 3g. Coverage ratio & ownership (OSFI B-13 only) | Data Catalog (counts) + Data Sources |

Run the 3a call (`get_compliance_frameworks`) first as a combined connectivity/auth
check — it's needed anyway. If it fails with a 403, "module not licensed",
"insufficient permissions", or a clearly permissions-shaped message:

> **Stop immediately.** Tell the user plainly which module is inaccessible, e.g.:
> "I can't generate this report — the Regulations module isn't licensed (or isn't
> accessible with your current role) on this BigID tenant. Ask your BigID admin to
> enable it before I can pull this data."

**This license check is distinct from an "Unknown server"/"Unknown tool" error.**
The latter means the tool/server name itself is wrong or stale, not that access is
denied — don't treat it as a license failure and don't apply the stop-immediately
message above to it. See Troubleshooting's "Unknown server / unknown tool error"
entry for the correct handling.

Continue into Step 3. If any *individual* pull in Step 3 fails the same way (license
or permission error, not a transient/empty-result error, and not an unknown-tool
error), stop generation entirely and name the specific module — do not silently
render that section as "Data unavailable" (that fallback is reserved for
transient/empty results, see Troubleshooting). A missing module is a hard blocker,
not a soft gap.

## Step 3 — Pull live data from BigID

Run all of these calls. Use `BigID MCP Production:get_objects` for every read.

### 3a. Compliance frameworks
```
server_name: "Regulations"
tool_name:   "get_compliance_frameworks"
arguments:   {}
```
Find the framework matching the chosen regulation (see reference file for name).
Note its `id` and enabled status. (Also serves as the Step 2 license/connectivity check.)

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

**Parsing notes:** large responses may be saved to disk rather than returned inline —
see Troubleshooting for how to parse them.

### 3h. Optional — regulatory-currency check (gap-driven only, off by default)

The four built-in regulations (EO 14117, GDPR, HIPAA, OSFI B-13) already have a
vetted, structured reference file with hardcoded regulatory facts — **do not web
search by default for these.** A web search only runs when:

- The regulation is a **custom/uploaded policy** that itself cites an external law,
  standard, or framework not covered by any built-in reference file, and you need
  a fact to correctly describe that external reference — or
- The user **explicitly asks** for the latest/recent developments ("what's changed
  recently", "any new enforcement action") rather than just "generate the report."

When you do run it, keep it to one search:
```
"[REGULATION OR STANDARD NAME] compliance updates 2025 2026 enforcement"
```
Pull the top findings and clearly label them in the Executive Summary as
externally-sourced context (not BigID evidence) — e.g. "Note (external, via web
search): ...". Never let a web result silently read as if it came from BigID.

If you don't run this check, don't mention it in the report — the reference file's
hardcoded facts stand on their own without a "last verified" caveat.

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

**BigID branding — always apply.** See `references/branding.md` for the full
constants block and `draw_header_footer()` function. Copy it verbatim and wire it
into `doc.build(..., onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)`.
This gives every report the BigID logo (top-right, every page) and the purple→pink→orange
footer band. Functional status colors (Met/Partial/Not-met) stay as defined in
`branding.md` — do not substitute brand accent colors for status colors or vice versa.

**Every report must include these sections** (regulation-specific content comes
from the reference file):

1. **Cover page** — regulation name, org name (if known), report date, data source
   (BigID MCP), confidentiality notice
2. **Executive Summary** — 2–3 paragraphs: what the regulation requires, how BigID
   operationalises compliance, overall status. Include any Step 3h currency-check
   findings, clearly labeled as external context, only if that check was run.
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
- **Missing data is stated, never invented:** if a pull is empty/errored transiently,
  render the section with "Data unavailable at time of report generation" — do not
  drop the section and do not estimate. (A license/permission error is different —
  see Step 2 — that stops the whole run, it doesn't get this fallback text.)
- **Filename is fixed:** `[REGULATION]_Compliance_Report.pdf` (custom policies use a
  slugged policy name — see Step 1).

**ReportLab patterns to follow:**
- Use `SimpleDocTemplate` + `Platypus` flowables (Paragraph, Table, Spacer, PageBreak)
- Tables: use `TableStyle` with `BACKGROUND`, `TEXTCOLOR`, `GRID`, `FONTNAME`,
  `FONTSIZE`, `ROWBACKGROUNDS` for alternating rows
- Never use Unicode subscript/superscript characters — they render as black boxes
- Status cells: use coloured text (not background fill) for pass/fail labels to
  avoid contrast issues in print

## Step 6 — Follow-up actions

Once the report content (Step 5) is finalized, offer the user a follow-up by default,
before final delivery:

> "Want me to also open a Jira ticket for the top Immediate-priority remediation item,
> or post the executive summary to a Slack channel — or just the PDF?"

- **Jira** — `Atlassian:createJiraIssue`, pre-filled with the single highest-priority
  (§8 "Immediate") item: action, linked finding, and timeframe.
- **Slack** — `Slack:slack_send_message`, posting the overall status plus the biggest
  gap from the Executive Summary.

Never create the ticket or send the message without the user's explicit confirmation
of which option (if any) they want. If neither Slack nor Jira is connected, skip this
offer silently and just deliver the PDF.

## Step 7 — Write and present output

```python
doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
# output path:
output_path = "/mnt/user-data/outputs/[REGULATION]_Compliance_Report.pdf"
```

Then call `present_files` with the output path.

## Troubleshooting

- **BigID MCP unavailable** — tell the user and stop; do not generate a report with
  stale data.
- **License/permission error on any Step 3 pull** — stop immediately per Step 2;
  name the specific module; never fall back to a partial report for a licensing gap.
- **Unknown server / unknown tool error** (e.g. `{"error":"Unknown server"}` or
  `{"error":"Unknown tool '...'"}`) — this is a **different failure than a license
  gap or a transient error, and it is not covered by either of those fallbacks.**
  It means the tool/server name in this SKILL.md no longer matches what the
  connected BigID MCP actually exposes (a naming drift or a bug in this file, not a
  tenant permissions issue and not something a retry will fix). Handle it like this:
  1. **Do not retry it** — retrying an unknown-tool error wastes calls; it will
     never succeed.
  2. **Do not silently treat it as "Data unavailable at time of report
     generation"** — that fallback is reserved for transient/empty results (see
     below) and would misrepresent a broken skill reference as a normal data gap.
  3. **Run `list_servers()` and, if the server does exist under a different name,
     `list_tools("<server>")`** to check whether the right tool exists under a
     slightly different name (renamed, recased, or moved to another server).
  4. **If you find the correct name, use it for this run** and flag the mismatch
     to the user plainly, e.g.: "Note: this report used `<correct_tool>` on
     `<server>` instead of the `<old_tool>` on `<old_server>` named in this skill —
     the skill's reference is stale and should be updated."
  5. **If no equivalent tool can be found**, stop and tell the user which specific
     pull is broken and why (unknown server/tool, not a permissions issue), rather
     than producing a report with that section silently degraded. A broken tool
     reference is a skill bug to flag, not a data gap to paper over.
- **Empty result** (e.g. zero open cases, zero frameworks enabled) — this is a valid
  result, not an error. Render the section normally with the true (zero) counts and
  say so plainly in the Executive Summary — don't treat it as a fetch failure.
- **Large/oversized tool result** — it will be stored to a file path instead of
  returned inline. Parse it with:
  ```bash
  python3 -c "
  import json
  with open('/mnt/user-data/tool_results/<filename>.json') as f:
      raw = json.load(f)
  # result is usually raw[0]['text'] or raw.get('result') — a JSON string, parse again
  "
  ```
- **Missing/unexpected fields** on a returned object — treat as unknown rather than
  failing the whole run: show "—" in that cell, keep the row, and note the gap rather
  than fabricating a value.
- **API/gateway errors (502, timeouts, connection resets)** — these are transient.
  Retry the single failed call once; if it fails again, mark that section "Data
  unavailable at time of report generation" and continue with the rest of the report.
- **Ambiguous ask** (user says "compliance report" with no regulation and no upload) —
  go to Step 1's regulation picker; don't guess a regulation and don't silently
  default to any one framework.
- **Named regulation not in the built-in list** (e.g. "generate a CCPA report") —
  don't decline and don't silently force the upload-policy path; see Step 1's
  "Named regulation not in the built-in list" for the best-effort-vs-upload choice
  to offer the user.
- **Uploaded file isn't actually a policy** (no obligations/requirements in it) — say
  so and ask for a real policy document rather than fabricating controls.

## Reference files

- `references/eo14117.md`, `references/gdpr.md`, `references/hipaa.md`,
  `references/osfi-b13.md` — regulation-specific facts, category mappings, and
  controls skeletons, each conforming to the Step 5 Repeatability contract
- `references/branding.md` — BigID PDF branding constants and `draw_header_footer()`;
  copy verbatim into every generator script
- `assets/logo_gray_v.png` — Bundled BigID logo used by `draw_header_footer()`; no
  external skill dependency
