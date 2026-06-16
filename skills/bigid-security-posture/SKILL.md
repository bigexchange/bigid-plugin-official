---
name: bigid-security-posture
description: >
  Triages BigID DSPM (Data Security Posture Management) security cases and surfaces the
  highest-risk ones to act on first — prioritizing credential-exposure cases (passwords,
  tokens, keys, secrets) above everything else. Use this skill whenever the user asks
  about their security posture, DSPM cases, "what should I fix first", "top security
  cases", "what's my biggest data risk", critical findings, exposed passwords/keys/secrets,
  open-access sensitive data, or wants to act on a security case. Always finish by
  proposing a concrete action: open a Jira or ServiceNow ticket, assign the case to a
  user, change case status (acknowledge/silence/resolve), Send to Cortex (XSOAR), or
  trigger object-level remediation (tombstone, archive/move) — choosing only from the
  integrations and actions that are actually connected/configured. Pulls live data from
  the BigID MCP Production server. If the user asks about specific objects/files/items
  behind a case, drill into the Data Catalog API.
compatibility: "Requires: BigID MCP Production server only (Security Posture, Data Catalog, Delegated Remediation, get_tpa_ids tools), bash_tool for parsing large results. No npm/assets/other connectors."
---

# BigID Security Posture Triage Skill

Reads live DSPM cases from BigID, ranks them by true risk (credential exposure first),
optionally drills into the specific objects behind a case, and drives the user to a
concrete remediation action.

## Tooling rule — BigID MCP only

This skill uses the **BigID MCP Production server exclusively**. Every read and every
action goes through these tools:
`BigID MCP Production:list_servers`, `:list_tools`, `:get_objects` (reads),
`:write_objects` (writes), and `:get_tpa_ids` (integration discovery).

Do **not** use web search, the browser, other connectors, or any non-BigID tool to get
posture data or take actions. Do **not** fabricate a REST call outside these MCP tools.
If a needed capability isn't exposed by a BigID MCP tool, say so plainly rather than
working around it.

## When to use

Any time the user wants to understand or act on their data security posture. Triggers:
- "what are the top cases to focus on / fix first?"
- "show me my critical security cases"
- "what's my biggest data risk right now?"
- "any exposed passwords / keys / secrets?"
- "triage my DSPM" / "security posture review"
- "what should I do about case X?"
- "which files/objects are in case X?" (→ Catalog drilldown, see Step 5)

This skill is for **Security Posture / Actionable Insights** cases (data-source policy
cases). It is NOT for privacy risk cases — those live in the Privacy Risk Cases API and
are covered by the `bigid-privacy-posture` skill.

## Do not guess

Confirm before asserting. Specifically:
- **Discover, don't assume, server/tool names.** If unsure a tool exists, call
  `list_servers` / `list_tools` first. Only reference tools that the server actually
  returns.
- **Discover, don't assume, connected integrations.** Run `get_tpa_ids` and only offer
  ticketing/SOAR/remediation channels that appear in the result. Never claim Jira,
  ServiceNow, or Cortex is available without confirming.
- **Discover, don't assume, configured remediation actions.** Call the Remediation
  "list available actions" tool before offering tombstone/move/etc. as options.
- **Don't invent IDs, counts, policy names, or assignees.** Read them from live results.
  Show the exact value returned; if a field is absent, say it's not present rather than
  filling it in.
- **Verify writes.** Report a ticket/assignment/remediation as successful only when the
  response confirms it (e.g. a real ticket URL). If the response shows a failure such as
  `"Creation Failed"`, say so and offer to retry.
- If a query returns nothing or errors, report that — do not substitute a plausible-
  looking answer.

---

## Core principle: risk-first ordering

BigID's own `severityLevel` and affected-object count are the starting point, but this
skill applies an explicit **credential-exposure-first** override. Live credentials are
the fastest path to lateral movement and breach, so they jump the queue regardless of
raw object count.

Priority tiers, highest first:

1. **Tier 1 — Credentials.** Policy/compliance name contains any of:
   `password`, `token`, `key`, `secret`, `credential`, `private key`. First, ordered
   among themselves by severity then affected-object count.
2. **Tier 2 — Open-access high-sensitivity data.** Policy name contains `open access`
   AND (`high sensitivity` OR `financial` OR `payment card` OR `pci` OR `unencrypted`).
3. **Tier 3 — Everything else**, ordered by severity (critical > high > medium > low)
   then affected-object count.

Within every tier, break ties by `numberOfAffectedObjects` descending. Full rubric and
keyword lists in `references/risk-ranking.md`.

---

## Workflow

Do the minimum queries needed. All calls below are `BigID MCP Production:get_objects`
unless stated, with `server_name` and `tool_name` set as shown.

### Step 1 — Get the candidate set efficiently

Start with the purpose-built dashboard tool (cheap, returns the 5 most critical open
cases with exactly the needed fields):

```
server_name = "Security Posture"
tool_name   = "get_actionable_insights_top_critical_cases"
arguments   = {}
```

For a broader sweep, pull a ranked page but request a **narrow field set** (case objects
carry large nested control blocks that otherwise truncate the response at ~150 KB):

```
server_name = "Security Posture"
tool_name   = "get_actionable_insights_all_cases"
arguments   = {
  "filter": "[{\"field\":\"caseStatus\",\"value\":\"open\",\"operator\":\"equals\"}]",
  "fields": "[\"caseId\",\"_id\",\"caseLabel\",\"severityLevel\",\"policyName\",\"compliance\",\"numberOfAffectedObjects\",\"dataSourceDisplayName\",\"assignee\",\"caseStatus\",\"ticketMetadata\"]",
  "sort": "[{\"field\":\"numberOfAffectedObjects\",\"desc\":true}]",
  "limit": 50,
  "requireTotalCount": true
}
```

Optional context tools (use only if asked for breakdowns/counts):
`get_actionable_insights_cases_by_severity`, `get_actionable_insights_cases_metadata`
(distinct values for every filterable field), `get_actionable_insights_cases_group_by_policy`.

**Parsing note:** results come back as a JSON string in `result`. If a call is stored to
`/mnt/user-data/tool_results/...` because it's too large, parse with `bash_tool` + Python
and extract only needed fields. See `references/efficient-queries.md`.

### Step 2 — Rank with the credential-first rule

Apply the three-tier ordering to the candidate set; produce the top 3 (or top N if asked).
For each case capture: caseId (friendly `SPC-###` if present, else `_id`), caseLabel,
severityLevel, numberOfAffectedObjects, dataSourceDisplayName, policyName, current
assignee, and whether a ticket already exists (`ticketMetadata` / `ticketUrl`). Flag any
`"Creation Failed"` ticket.

### Step 3 — Present the ranked list

Lead with why #1 is #1 (e.g. "credential exposure, critical, 370 objects"). Keep it
tight — a short ranked list, one or two sentences each. Note cross-cutting patterns (e.g.
one data source dominating). No raw JSON.

### Step 4 — Propose a concrete action (always)

Never end at a list. First discover what's available (do not guess):

```
tool_name = "get_tpa_ids"   (no server_name needed)
arguments = {}
```

Map result keys to channels:
- `ServiceNow IRM Integration`   → ServiceNow ticketing
- `XSOAR Cortex integration app` → "Send to Cortex"
- `Remediation`                  → object-level remediation (tombstone/move/etc.)

Jira is wired at the case-action level rather than always as a TPA — confirm via a case's
`ticketMetadata.ticketType` from Step 1, or offer it and verify on execution.

Then present a menu listing **only** the available channels — see "Action catalog" below.
Wait for the user to choose before executing (all are writes).

### Step 5 — Drill into specific objects/files (only when asked)

If the user asks which **objects / files / items / records** are behind a case or policy
("show me the files", "which objects", "list the items"), the case API gives counts, not
the objects. Use the **Data Catalog API** to enumerate them. The catalog can be filtered
by the same policy and data source that define the case, so you can scope precisely.

**Proven pattern** (verified against live data): query objects for a case's policy,
optionally scoped to its data source:

```
server_name = "Data Catalog"
tool_name   = "post_data_catalog"
arguments   = {
  "filter": "source = \"<dataSourceName>\" AND policy = \"<policyName>\"",
  "limit": 20,
  "requireTotalCount": "true"
}
```
- Use the case's `policyName` and `dataSourceName` (from Step 1) as the filter values.
- Filter grammar: logical `AND`/`OR`/`NOT`; operators `IN`, `=`, `STARTSWITH`, `EXISTS`.
  Filterable fields include `source`, `system`, `policy`, `attribute`, `objectType`,
  `owner`, `tags.{tagName}`, `total_pii_count`, `open_access`. Tag names with spaces use
  quotes, e.g. `tags.\"Access Type\" = \"Open Access\"`.
- Each result row includes `fullyQualifiedName`, `objectName`, `source`, `attribute`/
  `attribute_details` (the matched classifiers, e.g. "Explicit Password (Narrow)"),
  sensitivity/access `tags`, `owner`, and a `messageLink` (deep link to the file).
- Response tail carries `totalRowsCounter` and `estimatedCount` (total matching objects).

Just need the count, not the rows? Use `get_data_catalog_count` with the same `filter`.
Need details for one object? `get_data_catalog_object_details` (by `object_name`), and
`get_data_catalog_object_details_columns` / `_attributes` for column- and attribute-level
findings.

Present objects as a short table (name, path/link, matched classifier, sensitivity,
owner) — never paste raw JSON. These rows are also what feed object-level remediation in
the Action catalog (tombstone/move target the objects you just listed).

---

## Action catalog

Offer only what discovery (Step 4) confirmed is available. Two layers: **triage**
(case workflow) and **remediation** (changes the data — extra confirmation required).

### A) Triage actions — case level (Security Posture server)

**Assign to a user** — `write_objects`:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_cases_by_caseid"
arguments   = { "caseId": "<_id>", "assignee": "<email>" }
```

**Change case status** — `write_objects`. Valid statuses: `open`, `closed`, `resolved`,
`acknowledged`, `remediated`, `silenced` (silence = suppress). Use for acknowledge /
silence / resolve:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_case_status_by_caseid"
arguments   = { "caseId": "<_id>", "caseStatus": "acknowledged", "auditReason": "<why>" }
```

**Open a ticket (Jira / ServiceNow) or Send to Cortex** — `write_objects`. `actionType`
selects the channel (`jira` | `servicenow` | `cortex`), match the user's choice:
```
server_name = "Security Posture"
tool_name   = "post_actionable_insights_cases_\\::actionType_by_caseid"
arguments   = { "caseId": "<_id>", "actionType": "<jira|servicenow|cortex>" }
```
After executing, confirm and check for failure (`ticketUrl: "Creation Failed"` → tell the
user, offer retry or a different channel). Report success only when confirmed.

**Bulk action across a policy group** — `write_objects`:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_cases\\::actionType"
arguments   = {
  "type": "CasesDB", "subType": "updateCases",
  "additionalProperties": {
    "field": "assignee"|"caseStatus", "newValue": "<value>",
    "casesFilters": [{"filterField":"policyName","filterValues":["Passwords"]}],
    "auditReason": "<why>"
  }
}
```

### B) Remediation actions — object level (Delegated Remediation API - AI Agent server)

These **modify or relocate data**. Always: (1) confirm the integration/action is
configured via discovery, (2) show the user the affected objects (Step 5), (3) get
explicit confirmation, then execute.

**Discover configured actions first** — `get_objects`:
```
server_name = "Delegated Remediation API - AI Agent"
tool_name   = "get_proxy_tpa_api_Remediation_settings_actions"
arguments   = { "Accept-version": "<as required>" }
```
The remediation `actionType` enum includes: `ANNOTATION`, `USER`, `WORKFLOW`, `SYSTEM`,
`EXTERNAL`, `EXCEPTIONS`, `COLUMN`, `OBJECT`, `JIRA`, `ATTRIBUTE`.

> **Containment before destruction (credentials).** For credential-exposure cases, prefer
> non-destructive containment (Revoke External/Open Access, Move) first, then a ticket to
> rotate the secret, and only delete/tombstone after rotation is confirmed. Revoking access
> protects the file but does not invalidate a leaked key/password — rotation does.

**Available object-level actions** (confirm each is configured before offering):
- **Tombstone** — replace the object with a placeholder/tombstone. Supported via action
  rules (the rule body has a dedicated `tombstoneMessage` field).
- **Archive / move** — relocate objects to a target location (action-rule fields
  `targetDataSource` + `targetPath`).
- **Other configured actions** — masking/delete-type SYSTEM actions, annotations,
  attribute changes, etc., depending on tenant configuration and the listed integrations.

**Define an automated action rule (preset)** — `write_objects`:
```
server_name = "Delegated Remediation API - AI Agent"
tool_name   = "post_proxy_tpa_api_Remediation_settings_actions_rules"
arguments   = { "Accept-version": "<...>", "name": "...", "actionName": "...",
                "policies": ["<policyName>"], "tombstoneMessage": "<...>"   // for tombstone
                /* or */ "targetDataSource": "<...>", "targetPath": "<...>" // for move/archive
              }
```

**Execute a background remediation action** — `write_objects`:
```
server_name = "Delegated Remediation API - AI Agent"
tool_name   = "post_proxy_tpa_api_Remediation_execute"
arguments   = { "Accept-version": "<...>", "actionName": "<...>", "actionParams": [ ... ] }
```
Track status with `get_proxy_tpa_api_Remediation_settings_sync_audit_trail` /
`..._by_id` (using the returned `executionId`).

> Note: exact required headers/params for the Remediation proxy tools should be read from
> `list_tools` at runtime rather than assumed — do not guess version strings or auth.

---

## Field notes — confirmed-live patterns

These are verified against the live tenant. Prefer them over guessing; still re-discover
(`get_tpa_ids`, Remediation list-actions) each session in case configuration changed.

### Discovery calls that work (verbatim)

- **Top critical cases:** `Security Posture` / `get_actionable_insights_top_critical_cases`,
  `arguments = {}`. Returns the 5 most critical open cases with
  `caseId, amount, caseLabel, severityLevel, dataSourceName, policyName`. Note: this
  `caseId` is the Mongo `_id` (write endpoints want this); there is no `SPC-###` in this
  payload, so refer to cases by label.
- **Severity counts:** `Security Posture` / `get_actionable_insights_cases_by_severity`,
  `arguments = {}`. Returns `[{value, severityLevel}]` for critical/high/medium/low.
- **Files behind a case (Catalog drilldown):** `Data Catalog` / `post_data_catalog` with
  `filter = "source = \"<dataSourceName>\" AND policy = \"<policyName>\""`,
  `limit`, `requireTotalCount = "true"`. Each row carries `objectName`,
  `fullyQualifiedName`, `attribute_details` (matched classifiers + counts), sensitivity
  `tags`, `owner`, and a `messageLink` deep link. Response tail: `totalRowsCounter`
  (rows returned) and `estimatedCount` (total matching — use this as the true object
  count, it can differ from the case `amount`).
- **Configured remediation actions:** `Delegated Remediation API - AI Agent` /
  `get_proxy_tpa_api_Remediation_settings_actions`, `arguments = {"Accept-version": "2.0"}`.
  Returns `workflowActions` + `annotationActions`, each with an `isEnabled` flag —
  **only offer actions where `isEnabled` is true.**

### Action availability seen live (re-verify; `isEnabled` governs)

`get_tpa_ids` returned, among others: `ServiceNow IRM Integration`,
`XSOAR Cortex integration app`, `Remediation`, `Actions App (Scanner Based)`. Mapped
to enabled remediation actions:

- **enabled:** Assign, Create ServiceNow Ticket, Delete, False Positive, Move, Request
  Exception, Request Temporary Exception, Restore, Revoke External Access, Revoke Open
  Access, and annotation actions Archive / Encrypt / Mark for Deletion / Mask / Tombstone.
- **disabled (do NOT offer):** Revoke All Company (`isEnabled: false`).
- `Delete` / `Move` / `Revoke *` list `dsSupportedTypes` — check the case's data-source
  type (e.g. `gdrive-v2`, `sharepoint-online-v2`) is in that list before offering.

### Recommendation logic for credential-exposure cases (worked example)

For a Tier-1 credential case (tokens/keys/secrets/passwords), especially one whose
data source is a **breached / already-exposed** set, recommend in this order:

1. **Revoke external + open access first** — immediate containment that does not destroy
   the object, so it stays available for review and evidence. This is the "stop the
   bleeding" step.
2. **Open a ServiceNow ticket assigned to the data owner to ROTATE the credential.**
   Critical reasoning to convey to the user: revoking access protects the *file* but does
   **not** invalidate a leaked secret (e.g. an AWS Access Key ID, a plaintext password) —
   only rotation does. Rotation is a human task; track it in a ticket.
3. **Hold off on Delete / Tombstone until rotation is confirmed**, so exposure evidence
   isn't lost prematurely.

Watch for files carrying *multiple* sensitive classes (e.g. secrets **plus** medical
references or customer PII in the same spreadsheet) — flag these as highest-priority
within the case and another reason to contain rather than immediately delete.

### Presentation

When the user asks for a visual, a compact dashboard works well: severity metric cards
(open / critical / high / medium) + a horizontal bar of the top cases by affected-object
count + a ranked list with credential cases flagged. Keep all explanatory prose outside
the visual. Then offer 2–3 candidate cases for the user to pick from, and only after they
choose, drill into objects and present the action menu with one recommended action.

---

## Guardrails

- **BigID MCP only.** No web, browser, or other connectors for posture data or actions.
- **Read before write.** Rank and present (Steps 1-3) before proposing actions.
- **Discover before offering.** `get_tpa_ids` for channels; Remediation list-actions for
  remediation options. Offer only what's confirmed.
- **Confirm writes**, especially object-level remediation (it changes data). Get explicit
  user confirmation of the target case/objects and channel first.
- **Use the right caseId.** Write endpoints take the Mongo `_id`; show the friendly
  `SPC-###` to the user. Keep both straight.
- **Verify, don't assume.** Report success only when the response confirms it.

See `references/efficient-queries.md` (query/field details, catalog drilldown) and
`references/risk-ranking.md` (ranking rubric and keyword lists).
