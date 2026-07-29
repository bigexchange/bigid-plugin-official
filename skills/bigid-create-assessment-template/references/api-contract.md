# BigID PIA Custom Template API Contract

This is the **only** authoritative schema for building a template payload. Never invent
fields, endpoints, or values not listed here. If something needed isn't in this doc,
either query the connected MCP tool's schema for it (see "Resolving the `type` enum"
below) or ask the user — never guess.

---

## Create a custom template

**Endpoint:** `POST /privacy-apps/pia/templates`
**Purpose:** Creates a new custom PIA template.

### Request body

```json
{
  "title": "string",
  "description": "string",
  "types": ["string"],
  "baseId": "string",
  "sections": [
    {
      "id": "string",
      "title": "string",
      "subSections": [
        {
          "id": "string",
          "title": { "value": "string", "isVisible": true },
          "isVisible": true,
          "fields": [
            {
              "id": "string",
              "title": "string",
              "type": "string",
              "placeholder": "string",
              "description": "string",
              "isMandatory": true,
              "isVisible": true,
              "isCreatable": true,
              "isExplanationNeeded": true,
              "isOtherAllowed": true,
              "isDataDrivenQuestion": true,
              "dataDrivenAttributes": {
                "sourceName": "legal entity",
                "streamlineValue": "standardized value"
              },
              "options": ["string"]
            }
          ]
        }
      ]
    }
  ],
  "conditions": [
    {
      "id": "string",
      "rules": [
        { "fieldId": "string", "value": ["string"], "operator": "Is" }
      ],
      "operator": "And",
      "affectedItems": [
        { "ids": ["string"], "type": "Question" }
      ]
    }
  ],
  "automations": [
    {
      "id": "string",
      "rules": [
        { "fieldId": "string", "value": ["string"], "operator": "Is" }
      ],
      "operator": "And",
      "suggestions": [
        {
          "id": "string",
          "text": "string",
          "hasAction": true,
          "type": "Conclusion",
          "applicationTemplateType": "pia",
          "templateId": "string",
          "riskId": "string",
          "impact": 42.0,
          "probability": 42.0,
          "riskLevel": 42.0,
          "matrixSize": 42.0
        }
      ]
    }
  ]
}
```

### Field notes

| Field | Required | Notes |
|---|---|---|
| `title` | **Yes** | Minimum length 1. Use the document's title/filename/H1 if present. |
| `description` | No | Short summary of the template's purpose, if derivable from the doc. |
| `types` | No | Assessment type(s) this template applies to. **Do not write the doc's raw label directly into this array.** Every existing template in the tenant stores a resolved type *ID* (e.g. `PIA-OOTB-TEMPLATE-TYPE-2`), never a bare name (e.g. `"PIA"`). Infer the intended type from explicit doc labels ("Assessment Type: ..."), then resolve it to the real ID — see "Resolving the `types` values" below. If it can't be resolved, ask the user; never guess. |
| `baseId` | No | ID of a base template to extend. Only set if the user names a base template explicitly; otherwise omit. |
| `sections[].id` | — | Generate a stable slug (see Naming Rules in SKILL.md). |
| `sections[].title` | — | From a top-level heading. |
| `subSections[].title.value` / `isVisible` | — | From a sub-heading. If the source doc has no sub-heading level, create one default subSection per section (confirm with user during preview — see SKILL.md). |
| `fields[].type` | **Yes** | **Do not hardcode.** Resolve dynamically — see "Resolving the `type` enum" below. |
| `fields[].isMandatory` | No | Set `true` only if the doc marks the field as required (e.g. asterisk, "Required" label); default `false`. |
| `fields[].options` | No | Only for choice-like fields (dropdown/checkbox-style) where the doc lists explicit options (e.g. a table column with a fixed value set, or a legend). Omit otherwise — never invent options. |
| `fields[].isDataDrivenQuestion` / `dataDrivenAttributes` | No | Only set if the doc explicitly ties a field to a live data source (e.g. "pull from Legal Entities list"). Otherwise omit entirely. |
| `fields[].description` | No | If the doc has explicit help text for that field, use it verbatim (paraphrased to fit). If not, generate a short, relevant one-sentence description based on the field's name/context. **Always set this key explicitly on every field — never omit it.** If nothing meaningful can be generated, use `description: ""` (empty string), not an omitted key: an omitted `description` has been observed to render as the literal text "undefined" in BigID's UI. Never write `null`, or the literal text `"undefined"` as the value — that string must never appear as an actual value in the payload. |
| `sections[].isVisible` / `subSections[].isVisible` / `fields[].isVisible` | — | **Always set explicitly to `true`** for every section, subSection, and field unless the document's own conditional logic explicitly hides that item (i.e. it only appears as a target in a `conditions[].affectedItems` entry). Do not omit this key assuming a default — an omitted `isVisible` has been observed to render as invisible in the BigID UI, producing a template that looks completely blank even though the payload itself was accepted. |
| `conditions[]` / `automations[]` | No | Only include when the doc has explicit conditional language (e.g. "If Country = X, then show/require Y", "If risk is High, suggest mitigation Z"). Never fabricate rules to fill out the schema. |

### Resolving the `type` enum

The documented API schema lists `fields[].type` as a generic `string` — the real
allowed values (BigID's equivalents of Text/Dropdown/Date/Number/etc.) are not in this
doc, and **there is no confirmed, universal enum baked into this skill.** Every run must
re-derive or re-verify the real values for the connected tenant. Before generating any
payload:

1. This create endpoint's schema (below) already lists `fields[].type` as a generic
   `string` with no enum — so step 2 is required for every tenant.
2. Call `get_objects` with `server_name: "PIA API"`, `tool_name:
   "get_privacy_apps_pia_base_templates_metadata"` to list base templates and get an
   `id`, then `get_objects` again with `tool_name:
   "get_privacy_apps_pia_base_templates_by_id"`, `arguments: {"id": "<that id>"}` to
   reverse-engineer the real `type` strings this tenant accepts from an existing
   template's fields. If no base templates exist, try the same against an existing
   custom template via `get_privacy_apps_pia_templates_metadata` →
   `get_privacy_apps_pia_templates_by_id`. Present the discovered list to the user for
   confirmation before proceeding, rather than requiring them to enumerate valid values
   unaided.
3. **Provisional fallback baseline only** — if step 2's live sampling isn't possible
   (e.g. no existing templates exist yet in this tenant to sample), these values were
   observed directly in one prior tenant: `Text`, `Paragraph`, `Dropdown`,
   `MultiSelectDropdown`, `Option`, `DatePicker`, `CountriesStates`, `FileUpload`. Treat
   this list as **unverified for the current tenant** — explicitly tell the user these
   are a best-guess starting point from a different session, not a confirmed enum for
   their environment, and ask them to confirm before using any of them.
4. **Hard stop:** never write one of the Step 4 SKILL.md **concept labels**
   (`Short Text`, `Long/multiline text`, `Single-select`, `Multi-select`, `Signature`,
   `Image`, `Attachment`, `URL`, etc.) directly into `fields[].type` under any
   circumstance — including as a fallback when resolution fails or is skipped. Those
   words exist only to describe the *concept*; they are never valid BigID values. If no
   value has been confirmed via step 2, 3, or (with explicit user sign-off) step 3,
   **stop and ask the user** rather than submitting anything. A field with an unresolved
   type must not be included in the create call — surface it to the user as a blocking
   item in the Step 7 preview instead.
5. Never proceed to submission with a `type` value that hasn't been confirmed via step
   2 or 3.

### Resolving the `types` values

The doc-level `types` array uses tenant-specific type *IDs*, not the plain-language
label that shows up in a source document (e.g. a doc says "Assessment Type: PIA", but
the field must store `PIA-OOTB-TEMPLATE-TYPE-2`). Before finalizing the payload:

1. Call `get_objects` with `server_name: "PIA API"`, `tool_name:
   "get_privacy_apps_pia_templates_types"`, `arguments: {}` to get the tenant's real
   type list. If that's unavailable, fall back to `get_privacy_apps_pia_base_templates_by_id`
   (per the pattern in "Resolving the `type` enum" above) on an existing template as a
   secondary source for real `types` values actually in use in this tenant.
2. Call it and match the doc's plain-language label against the returned `name` values.
3. Use the corresponding `id` value in the payload's `types[]` array — never the `name`.
4. If no confident match is found, ask the user to pick from the returned list rather
   than guessing or falling back to the raw doc label.
5. Show the user both the doc's label and the resolved ID during preview (Step 7) so a
   silent mismatch isn't hidden by a preview that only shows the friendly name.

---

## List existing custom templates (for `baseId` lookups / duplicate checking)

**Endpoint:** `GET /privacy-apps/pia/templates/metadata`
**Purpose:** Retrieve all custom templates — useful for checking name collisions before
creating a new template, or finding a `baseId` the user references by name.

### Query parameters
- `limit` — max rows to return. **Always pass a small explicit `limit` (e.g. 20-50)**
  rather than an unbounded call — this endpoint is used for title-collision checks and
  `baseId` lookups, neither of which need the full template list. If checking for a
  specific title/id and the first page doesn't contain it, page with `skip` rather than
  requesting everything at once.
- `skip` — pagination offset. Use this to page through results incrementally if a
  specific title/id isn't found on the first page, instead of raising `limit` to an
  unbounded value.
- `requireTotalCount` — whether to return total count. Only set this `true` if you
  actually need to tell the user how many templates exist in total; leave it `false`/
  omitted for a simple existence check to keep the response smaller.

### Response (200)
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "createdBy": { "name": "string", "email": "string" },
      "status": "Draft",
      "created_at": "2026-05-04T09:42:00Z",
      "updated_at": "2026-05-04T09:42:00Z",
      "types": ["string"],
      "legalEntities": [{ "id": "string", "name": "string" }],
      "hasCollaboration": true
    }
  ],
  "totalCount": 42
}
```

Use this before creating a template if the user references an existing template by
name (for `baseId`), or to warn about a likely duplicate `title`.

---

## Error responses

Both endpoints can return:
- `400` — Bad Request (validation failure — check required fields, especially `title`)
- `409` — Conflict (likely a duplicate template title)
- `500` — Failed Operation

On any of these, don't assume the `message` field will be usable — see SKILL.md Step 8
for the full handling procedure (title-conflict check via the metadata endpoint before
relying on the error body, and payload disclosure to the user as a last resort).

**Known platform defect:** a payload combining a multi-section structure with both
`types` and `conditions[]` populated has been observed to be rejected with an empty,
non-diagnostic error (`{"error": "? ", "details": ""}`) even though `types` alone,
`conditions[]` alone, and multi-section structure alone each succeed independently.
SKILL.md Step 8 specifies a one-time retry without `types` for this case — do not
attempt further automatic retries beyond that.
