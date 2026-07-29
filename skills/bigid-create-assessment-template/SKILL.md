---
name: bigid-create-assessment-template
description: Builds and creates a brand-new BigID PIA custom template (the reusable form definition) from an uploaded Word/Excel/PDF document, or by interviewing the user if none is provided. Parses headings, tables, and placeholders into a sections/subSections/fields payload, resolves field types dynamically against the connected BigID MCP tool's schema, detects conditional logic, previews with the user, and creates the template via the connected tool. Use this for turning a document (questionnaire, intake sheet, assessment outline) into a new BigID PIA template; mentions of "PIA template" or "custom template" for a privacy impact assessment; requests to convert/import/build a PIA template from Word/Excel/PDF, even without the word "template" (e.g. "set this questionnaire up in BigID as a PIA"). Do NOT use for RoPA/data-mapping templates (use create-businessprocess-templates instead); filling out an assessment instance for a specific vendor/project; or listing/viewing templates that already exist.
---

# Create Assessment Templates

Turns a source document into a real, created BigID PIA custom template — or builds one
from scratch through conversation when there's no document.

**Read `references/api-contract.md` before building any payload.** It's the single
source of truth for the target schema. Never invent a field, endpoint, or field-type
value that isn't confirmed there or dynamically from the connected MCP tool.

**How these tools are actually invoked (read this before Step 0):** every
`get_privacy_apps_pia_*` / `post_privacy_apps_pia_*` name in this skill is an endpoint
on the `PIA API` server — it is **not** a directly-callable top-level tool. Call it via:

1. Once per session, call `get_tpa_ids` first. BigID requires this before any call to a
   TPA-based API (PIA is one). Confirm the response includes a `"PIA"` key — if it's
   missing, the PIA module isn't installed/available for this tenant; stop and tell the
   user (see Step 0).
2. Use `get_objects` for `[READ]` endpoints and `write_objects` for `[WRITE]` endpoints,
   passing `server_name: "PIA API"` and `tool_name: "<the endpoint name from this
   skill>"` (e.g. `tool_name: "get_privacy_apps_pia_templates_types"`), plus `arguments`
   matching that endpoint's schema. Do **not** call `tool_search` expecting to find a
   standalone tool literally named `get_privacy_apps_pia_templates_types` — it will not
   turn up one; the name is a `tool_name` argument to `get_objects`/`write_objects`, not
   a tool name in its own right.
3. If you need to (re-)confirm the exact set of available endpoint names for this
   tenant, call `list_tools` with `server_name: "PIA API"`.

Every "call `get_privacy_apps_pia_...`" instruction elsewhere in this skill and in
`references/api-contract.md` means: do this, through `get_objects`/`write_objects`, per
the pattern above — not a direct call.

---

## Workflow

```text
Skill invoked
     │
     ▼
Confirm PIA-module license/permission is available (see Step 0) ──Fail──▶ Stop, tell user
     │Pass
     ▼
Document uploaded? ──No──▶ Interview user (see "No-Document Path")
     │Yes
     ▼
Read document (docx / xlsx / pdf)
     │
     ▼
Extract structure (headings, tables, placeholders, lists)
     │
     ▼
Resolve field `type` enum via connected MCP tool's schema (see api-contract.md)
     │
     ▼
Map structure → sections / subSections / fields
     │
     ▼
Detect conditional language → conditions[] / automations[] (only if explicit)
     │
     ▼
Infer `title` / `description` / `types` / `baseId`; ask if not confidently inferable
     │
     ▼
Build payload per api-contract.md
     │
     ▼
Present preview to user (ask case-by-case about ambiguous section/subSection splits)
     │
     ▼
User approves / corrects
     │
     ▼
Call connected BigID MCP tool to create the template
     │
     ▼
Report result (success + template id, or surface API error message) + suggest next steps
```

---

## Step 0: Confirm license / permission before doing anything else

Before reading a document or starting the No-Document interview, confirm the PIA
module is available and this user has access — this catches a missing license or
insufficient permission early, rather than after the user has already uploaded a
document or answered several interview questions.

1. Call `get_tpa_ids` (no arguments). Check the response for a `"PIA"` key. If it's
   **absent**, the PIA module/app isn't installed or licensed for this tenant — tell
   the user directly and stop here; don't proceed to Step 1.
2. Call `get_objects` with `server_name: "PIA API"`, `tool_name:
   "get_privacy_apps_pia_permissions"`, `arguments: {}`. This returns the real
   permission set for the current user/connector, e.g. `{"isAdmin": true/false,
   "permissions": {"permission.xxx.read": [...], ...}}`.
   - If `isAdmin` is `true`, proceed — full access is confirmed.
   - If `isAdmin` is `false`, look for permission keys that plausibly cover PIA
     templates/assessments (naming varies by tenant — look for keys containing
     "pia", "privacyImpactAssessment", "template", or similar). If you find a relevant
     permission present, proceed. If you find relevant-looking permissions explicitly
     **absent** (i.e. other similar categories appear in the list but nothing PIA/
     template-related does), tell the user they may lack the needed BigID permission
     and suggest checking with their BigID admin — don't proceed to Step 1.
   - If the permission set is genuinely ambiguous (no clearly relevant key either way,
     nothing to confirm or deny access), **don't block on ambiguity** — proceed
     normally and let a real 401/403 from a later call be the actual signal of a
     permission problem. A missing/unclear permission key is not by itself proof of a
     lack of access, and incorrectly blocking a user who does have access is worse than
     occasionally deferring the failure to a later, more concrete error.
3. If step 1 or 2 fails outright (call errors, not just an unfavorable result — e.g.
   `get_tpa_ids` itself errors, or `get_objects` returns an auth failure rather than a
   permissions payload), that itself is the signal: tell the user the BigID connection
   couldn't be verified and stop, rather than treating a failed check as silent
   permission.
4. Only continue to document reading / interview once this check has run and hasn't
   produced a clear block per steps 1-3.

---

## Step 1: Read the document

- **.docx** — use the docx skill's reading approach for structure (headings, paragraphs, tables, lists, bookmarks).
- **.xlsx** — use the xlsx skill's reading approach (worksheets, header rows, named ranges, merged cells).
- **.pdf** — use the pdf-reading skill; extract text and tables the same way, with OCR fallback for scanned pages. Treat extracted structure identically to docx/xlsx once you have headings/tables/text blocks.

If the document is empty, corrupted, password-protected, or has no extractable content, stop and tell the user which of these it is — don't attempt a partial mapping.

---

## Step 2: Detect structure

### Headings → sections / subSections
The target schema is **sections → subSections → fields** (not a flat sections/fields
list). Map heading levels accordingly:
- Top-level headings (H1 or doc title) → `sections[]`
- Next heading level (H2) → `subSections[]`
- If the document only has one heading level (flat structure), **don't guess** whether
  to split it into sections vs. a single section with one default subSection — flag
  this ambiguity in the preview and ask the user directly, presenting the concrete
  choice rather than an open-ended question, e.g.: "Option A: one section
  ('General') containing all N fields as a single subSection. Option B: split into
  N separate sections, one per heading. Which do you want?"

### Tables → fields
Each table column becomes a field (per the doc's original convention); each row can be
noted as optional sample/reference data but does not itself become a field.

**Exception — fixed role/category row tables:** if a table's row labels are a small,
fixed set of roles or categories rather than free/sample entries (e.g. a sign-off block
with rows "Respondent," "Reviewer," "Approver" and columns "Name," "Signature," "Date"),
applying the column-only rule literally collapses each column into one generic field
(a single "Name" field) and loses which role it belongs to. In this case, generate one
field per (row × column) pair instead, scoped to its role — e.g. `respondentName`,
`respondentSignature`, `respondentDate`, `reviewerName`, `reviewerSignature`, etc. —
rather than one undifferentiated `name`/`signature`/`date` field shared across roles.
Flag this interpretation in the preview (Step 7) so the user can confirm or ask for the
plain column-only mapping instead.

### Repeated label patterns → fields
Lines like `Customer Name:`, `Invoice Number:`, `Phone:` become fields when they look
like user-entry prompts rather than static content.

### Existing placeholders → fields
Recognize and extract:
```
{{FieldName}}   <<FieldName>>   ${FieldName}   [FieldName]   %FieldName%
```

### Everything else → static text
Plain paragraphs and lists with no placeholder or field-like pattern are not converted
into fields — leave them out of the payload rather than inventing a field for them.

---

## Step 3: Field naming

Generated `id`/`title` values should:
- Remove special characters, collapse whitespace
- Use camelCase for `id`, human-readable original text for `title`
- Avoid duplicate ids within the same template — if a collision would occur, suffix
  with a number (`phoneNumber2`)

Example: `Invoice Date` → `id: invoiceDate`, `title: "Invoice Date"`

**Every section, subSection, and field must explicitly set `isVisible: true`** in the
payload unless it's a target of a `conditions[].affectedItems` entry (i.e. the doc says
it should only appear when some other answer triggers it) — never omit this key or
leave it to an assumed default. An omitted `isVisible` can cause the entire created
template to render blank in the BigID UI even though the create call succeeded.

**`fields[].description`** — if the document has explicit help text for that specific
field, use it. If not, **generate a short, relevant one-sentence description** in your
own words based on the field's name and surrounding context (e.g. for a field titled
"Data Retention Period" with no doc help text, write something like "How long this
data will be retained before deletion or review."). **Always include the `description`
key on every field, with an explicit value — never omit the key.** If nothing
meaningful can be generated, set `description: ""` (empty string) rather than leaving
the key out. **Known platform defect: an omitted `description` key has been observed
to render as the literal text "undefined" in BigID's UI**, which is worse than an empty
field — so omission is not a safe fallback here despite being technically valid against
the schema. **Never** write `null`, and never write the literal text `"undefined"` as
the *value* — that string must never appear as a value anywhere in the payload. If you
generate a description, make sure it's genuinely useful and specific to that field, not
generic filler repeated across fields.

---

## Step 4: Field type inference

**This step is mandatory and blocking. Do not build or add a single field to the
payload before completing it.**

### Step 4a — Resolve the tenant's real type values FIRST, before mapping any field

1. `post_privacy_apps_pia_templates`'s schema is already documented in
   `references/api-contract.md` — its `fields[].type` is a generic `string` with no
   enum listed, so this tenant's schema alone won't tell you valid values. Step 2 below
   is required.
2. Call `get_objects` with `server_name: "PIA API"`, `tool_name:
   "get_privacy_apps_pia_base_templates_metadata"`, `arguments: {}` to list base
   templates and get an `id`. Then call `get_objects` again with `tool_name:
   "get_privacy_apps_pia_base_templates_by_id"`, `arguments: {"id": "<that id>"}` to
   inspect a real template's fields and collect the actual `type` strings in use in
   **this** tenant. If none exist, try the same against an existing **custom** template
   via `get_privacy_apps_pia_templates_metadata` → `get_privacy_apps_pia_templates_by_id`
   instead. Do this even if you already know values from a different tenant or a prior
   session — those are not valid here until confirmed against this tenant.
3. Build one explicit list of the concepts this specific document actually needs
   (e.g. "this doc needs: short text, long text, single-select, date, attachment") and
   resolve each concept to a real value from step 2 **before** touching Step 4b.
   Any concept you can't confidently resolve this way must be asked about now, up
   front — not discovered later per-field while building the payload.
4. Show the user the full resolved concept→value table as part of this step (not
   buried later) so they can catch a wrong mapping before any field is built on it.

### Step 4b — Apply the resolved table to every field

Only after Step 4a is complete, map each field's concept using this **conceptual**
guide, translating the left-hand concept onto the tenant-confirmed value from 4a:

| Signal in document | Concept |
|---|---|
| Name, Title, generic label | Short text |
| Description, Notes, Comments | Long/multiline text |
| Email | Email |
| Phone, Mobile | Phone |
| Date, Due Date | Date |
| Amount, Price, Cost | Currency |
| Quantity, Count | Number |
| Percentage, Rate | Decimal |
| Status, Country, State, City, or any field where the doc indicates only **one** option can be chosen (radio buttons, single dropdown, "select one") | Single-select (populate `options[]` from the doc's actual list) |
| Categories of data, checkboxes, "select all that apply," or any field where the doc indicates **multiple** options can be chosen at once | Multi-select (populate `options[]` from the doc's actual list) |
| Signature | Signature |
| Image, Photo | Image |
| File, Attachment | Attachment |
| URL, Link | URL |
| Anything unclear | Short text (safest default) |

**Hard rule: a field may not be added to the payload with a `type` value that isn't in
the Step 4a resolved table.** If a field's concept has no resolved match:
- Do not guess, do not leave it off `type` entirely, and do not fall back to writing
  the concept label itself (`"Short text"`, `"Single-select"`, etc.) — none of these
  are real BigID values.
- Stop and ask the user for that one concept specifically, before continuing to build
  the rest of the payload — present the actual resolved list from Step 4a as concrete
  options (e.g. "This tenant's available types are: Text, Paragraph, Dropdown,
  MultiSelectDropdown, DatePicker, FileUpload. Which should 'Vendor Risk Category' use?")
  rather than an open-ended "what type should this be?"
- Never reach Step 7 (preview) with any field's type still unresolved. An unresolved
  type is a blocker, not a preview footnote.

---

## Step 5: Conditions & automations (only if explicit)

Only populate `conditions[]` / `automations[]` when the document contains explicit
conditional language, e.g.:
- "If Country = EU, then [field] is required" → `conditions[]`
- "If risk level is High, suggest [mitigation text]" → `automations[]`

Map the referenced field name to its generated `fieldId`. If a condition references a
field that wasn't otherwise extracted, flag this to the user rather than silently
dropping or inventing the reference.

If there's no explicit conditional language anywhere in the doc, omit both arrays
entirely — don't include empty placeholder logic.

---

## Step 6: Top-level metadata

- **`title`** — from document title / filename / first H1. If none is clear, ask.
- **`description`** — only if the doc has an explicit intro/summary paragraph describing its purpose; otherwise omit.
- **`types`** — only set from explicit labels in the doc (e.g. "Assessment Type: RoPA"). **Never write the raw doc label into the payload.** Resolve it to the tenant's real type ID via the connected MCP tool (see api-contract.md, "Resolving the `types` values") before including it. If ambiguous or unresolvable, ask the user; don't default to a guess or to the unresolved label.
- **`baseId`** — only set if the user names an existing template to extend. Call `get_objects` with `server_name: "PIA API"`, `tool_name: "get_privacy_apps_pia_templates_metadata"`, and a bounded `limit`/`skip` (see api-contract.md's paging guidance) to look up its id by title if needed. If that lookup returns `null` or an empty result, tell the user the named template wasn't found rather than silently omitting `baseId` or guessing an id (see Step 8's note on `null`/empty lookup responses).

---

## Step 7: Preview and confirm

Before calling the create endpoint, show the user a summary, e.g.:

```
Template Name: Employee Onboarding
Sections: 3
Subsections: 6
Detected Fields: 18
Conditions: 2
Automations: 1
Static Text Blocks (excluded from payload): 11
```

Then flag anything that needs a decision:
- Ambiguous section/subSection splits
- Any field type that couldn't be confidently resolved against the enum
- Any inferred `types`/`title`/`description` the user should confirm — for `types`, show
  both the doc's plain-language label and the resolved type ID (e.g. "PIA" →
  `PIA-OOTB-TEMPLATE-TYPE-2`) so a resolution mismatch is visible, not hidden behind a
  friendly name

Ask if they want to rename the template, remove/add fields, change field types, or
rearrange sections before proceeding.

**Before calling create, do a final pass over the built payload** and confirm every
section, subSection, and field has `isVisible` explicitly set (`true`, unless it's a
conditional target per the doc), and that **every field has a `description` key present
with an explicit value** — either real doc-sourced help text, a genuinely relevant
generated one-sentence description, or an explicit empty string `""` if nothing
meaningful can be said. Never omit the `description` key (it renders as the literal
text "undefined" in BigID's UI — a known platform defect) and never let its value be
`null` or the literal text `"undefined"`. Also confirm every `fields[].type` value came
from the Step 4a resolved table —
if any field's type is still unresolved or is one of Step 4's concept labels
(`Short Text`, `Single-select`, etc.), stop here; this should not be possible if Step 4a
was actually completed before fields were built, but check anyway. This is a cheap
final check against the blank-template / unrendered-field failure modes described in
`references/api-contract.md`.

**Before proceeding to Step 8, confirm the write is intended.** Template creation via
the connected BigID MCP tool is **not reversible from within this skill** — there is no
delete/archive endpoint for templates in the available toolset (only for assessment
*instances*), so a template created by mistake or for testing will remain permanently in
that tenant's template list. As part of this confirmation:
- Make clear to the user that clicking "yes, create it" will permanently add this
  template to whatever BigID tenant/environment the connected tool is pointed at, and
  that it cannot be deleted or archived through this skill afterward.
- If the user is testing, exploring, or unsure whether they want this to be permanent,
  say so explicitly and let them decide whether to proceed, ask their BigID admin to
  remove it manually afterward if needed, or stop here and just deliver the payload
  JSON instead (see Step 8's fallback) without calling the create endpoint at all.
- Do not treat a generic "looks good" as sufficient confirmation for the write itself —
  the preview approval and the create-it confirmation can be the same message from the
  user, but the irreversibility should have been stated to them before they gave it.

---

## Step 8: Create the template

Once approved:
1. Call `write_objects` with `server_name: "PIA API"`, `tool_name:
   "post_privacy_apps_pia_templates"`, and `arguments` set to the finalized payload.
2. On success (`201`), report the returned `id` and confirm the template was created.
   Then offer concrete next steps rather than ending the turn — pick whichever are
   actually relevant:
   - Assign the new template to a legal entity, business unit, or vendor category (if
     `list_tools` for `server_name: "PIA API"` shows an assignment-related endpoint).
   - Open/view the created template in BigID directly, if a UI link/id is available to
     share.
   - Build a related template next — e.g. if this was a PIA template, ask if they also
     want a matching RoPA template (`create-businessprocess-templates`) for the same
     process.
   - Run an actual assessment off this template (create an instance), if that's a
     separate connected capability.
   Don't force all of these — offer the 1-3 that make sense given what the user was
   trying to accomplish, and skip this if the user has clearly indicated they just
   wanted the template and nothing else.
3. **Known platform issue:** if the payload includes **both** `types` and
   `conditions[]` alongside a multi-section structure, the live API has been observed to
   reject this exact combination with an empty, non-diagnostic error (`{"error": "? ",
   "details": ""}`) even though each element works fine individually. If a create call
   fails with an empty/unhelpful error immediately after submitting a payload with both
   `types` and `conditions[]` present, **retry the create once with `types` omitted**.
   If the retry succeeds, tell the user plainly that `types` was dropped due to a known
   platform issue and that they may want to add it back manually in BigID's UI or check
   with the platform team. If the retry also fails, treat it as a genuine failure (below)
   rather than retrying further.
4. On `400`/`409`/`500` (or any other failure, including the empty-error shape above
   after the retry in step 3 has already been tried): **don't assume a usable `message`
   field will be present** — in practice this connector frequently returns an empty or
   non-diagnostic body (`{"error": "? ", "details": ""}`) even for real, distinct failure
   causes. First, distinguish a plain transient failure from a real one:
   a. If the failure looks transient (timeout, connection error, or a `500` with no
      diagnostic content and no title conflict — i.e. not the known `types`+`conditions[]`
      case from step 3, and not an auth/permission error which Step 0 should have
      already caught) — **retry the exact same payload once, unmodified.** If the retry
      succeeds, proceed normally. If it fails again, treat it as a genuine failure below
      rather than retrying further; don't loop.
   b. Otherwise (or once the one transient retry has failed), diagnose properly: call
      `get_objects` with `server_name: "PIA API"`, `tool_name:
      "get_privacy_apps_pia_templates_metadata"`, and a bounded `limit` argument (see
      api-contract.md's paging guidance, don't request an unbounded list) and check
      whether a template with the same `title` already exists — this disambiguates a
      likely `409` title conflict from a `400`/`500` without relying on the error body
      at all.
   c. If a title conflict is confirmed, tell the user directly and offer to rename.
   d. If no title conflict is found and the error body has no usable `message`, tell the
      user plainly that the platform returned an error with no diagnostic detail, and
      show them the exact payload that was attempted so they can escalate to the
      platform team themselves rather than guessing at the cause.
   e. Never silently retry with guessed changes beyond the one transient retry (a) and
      the single documented `types` retry in step 3.

**Lookup calls (metadata search, `by_id`, types lookup) can also return a bare `null` or
an empty `200` body instead of a proper 404** when nothing matches. Don't treat that as
silent success or as "nothing to report" — if a lookup you depend on (e.g. the title-
conflict check in Step 8, item 4b above, or a `baseId` lookup) comes back `null`/empty,
treat it the same as "not found": tell the user directly rather than proceeding as if
the check passed or silently skipping the step.

If no BigID MCP tool for this endpoint is connected, tell the user directly and offer
to output the finished JSON payload instead so they can submit it themselves once a
tool is connected.

---

## No-Document Path

If the skill is invoked with no document uploaded, build the template through
conversation instead of parsing a file:
1. Ask what the template is for (title/purpose) and, if relevant, its assessment `types`.
2. Ask the user to describe sections and the fields within each — one section at a time is easier than asking for everything at once.
3. For each field, confirm its type against the resolved enum (Step 4/api-contract.md) rather than assuming.
4. Ask about any conditional logic explicitly (don't assume none exists).
5. Proceed to Step 7 (preview) and Step 8 (create) as normal.

---

## Validation — reject or warn before building a payload

**Reject and stop** if the document is:
- Empty or has no readable content
- Corrupted or unreadable
- Password-protected without a provided password

**Warn but proceed** if:
- Duplicate placeholder/field names are detected (auto-dedupe per Step 3, but tell the user)
- A field's type can't be confidently resolved (ask, per Step 4)
- Placeholder syntax is inconsistent across the doc (mixed `{{}}`/`[]`/etc. — note it, extract anyway)
- The document is very large and produces a very large field count (rough guideline:
  50+ fields or 10+ sections). Don't silently truncate — tell the user the scale you
  detected and confirm they want the full structure built and previewed before
  proceeding, since a preview of that size is harder to sanity-check in one pass. Offer
  to preview section-by-section instead of all at once if they'd prefer.

**Stop and report clearly, don't retry silently,** if:
- Step 0's license/permission check fails (missing PIA-module license, or a
  permission/auth error on a basic read call) — this is a tenant/access issue, not
  something a retry or a different payload shape will fix.

---

## Troubleshooting — Edge Cases

This section collects edge cases that don't fit cleanly into a single workflow step
above, or that combine failure modes from several steps. Check here if something odd
happens that isn't a straightforward license/permission failure (Step 0) or a create-call
error (Step 8).

**Unsupported file type uploaded (e.g. `.txt`, `.pptx`, `.csv`, image-only file with no
OCR-able text).** Only .docx, .xlsx, and .pdf are supported source formats. Tell the user
directly which formats are supported and ask them to re-upload, or offer the No-Document
Path (interview) instead if they'd rather not convert the file.

**Multiple documents uploaded at once.** Don't silently merge them into one template or
silently pick one and ignore the rest. Ask the user whether they want: (a) one combined
template built from all documents, (b) separate templates per document, or (c) only one
of them used — and confirm which before reading further.

**Document is in a language other than English.** Extract structure (headings, tables,
placeholders) the same way, and keep generated `id`/`title`/`description` values in the
document's original language rather than translating — translating risks introducing a
field name or description that doesn't match what the user or their org actually uses.
If you're not confident you've correctly identified a heading vs. body text in an
unfamiliar language, flag that specific spot in the preview rather than guessing.

**Nested or merged-cell tables that don't fit the simple column-only or row×column
patterns in Step 2.** If a table's structure is genuinely ambiguous (e.g. multi-level
column headers, cells merged across an irregular pattern), don't force it into either
pattern — describe the ambiguity concretely to the user (e.g. "this table has merged
header cells spanning columns 2-4, I can't tell if that's one field or three") and ask
which interpretation they want, the same way Step 2 asks about flat heading structure.

**Same field name/label repeated in genuinely different sections (not the role-table
case in Step 2).** Auto-dedupe per Step 3's numeric-suffix rule (`phoneNumber`,
`phoneNumber2`), but call this out in the preview so the user can rename either occurrence
if the auto-generated suffix isn't meaningful to them.

**The document and the user's chat instructions disagree** (e.g. the doc's title says
"Vendor Risk Assessment" but the user says "call it Third-Party Risk Review", or the doc
implies single-select but the user says multi-select for the same field). Chat
instructions from the current conversation take precedence over the document — but say so
explicitly in the preview (Step 7) rather than quietly overriding the doc, so the user
can catch a mishearing.

**`references/api-contract.md` appears stale against what the connected MCP tool actually
returns** (e.g. `list_tools` shows an endpoint name, or a real response shows a field,
that isn't documented there). Trust the live tool schema over the reference file for
that specific mismatch, proceed using the live schema, and mention to the user that the
reference doc may need a refresh — don't block the whole workflow on a documentation gap.

**Template created successfully, but a requested follow-on action fails** (e.g. the
create call succeeds but the user also asked to assign the template to a business unit
and that assignment call fails). Don't let the follow-on failure make the overall result
look like a failure — clearly separate the two: report the template creation as a
success (with its id), then separately report the follow-on failure and what the user
can do about it (retry, do it manually in BigID's UI, etc.).

**User asks to edit or fix a template *after* it's already been created in this same
conversation.** This skill only covers creation, and (per Step 7's confirmation) template
creation isn't reversible or editable from within this skill — there's no update
endpoint in the available toolset. Tell the user the change needs to be made directly in
BigID's UI, or, if they want, build a *new* corrected template and let them deal with the
old one manually (don't attempt to overwrite/reuse the old template's id).

**Session interrupted mid-workflow (e.g. user comes back after Step 4a's type resolution
but before Step 7's preview).** Don't re-run completed steps' MCP calls speculatively —
re-confirm with the user what was already resolved (the concept→value table from 4a,
any interview answers from the No-Document Path) before continuing, since assuming stale
state matches current intent is itself a source of a wrong payload.

---

## Core principles

- Never invent a field, section, condition, or field-type value not grounded in either the source document or the real API schema in `references/api-contract.md`.
- Prefer asking over guessing whenever a mapping decision is ambiguous (section splits, field types, `types`/`baseId`).
- Preserve the source document's ordering and hierarchy.
- Static text (plain paragraphs/lists with no placeholder) is never turned into a field.
- The `references/api-contract.md` schema is the only source of truth for the payload shape — not the general field-type conventions used for other document types.
