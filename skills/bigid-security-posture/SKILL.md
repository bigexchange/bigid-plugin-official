---
name: bigid-security-posture
description: >
  Triages BigID DSPM security cases, ranking credential-exposure (passwords, tokens, keys,
  secrets) above everything else. Use when the user asks about security posture, DSPM
  cases, "what should I fix first", "top security cases", "biggest data risk", critical
  findings, exposed passwords/keys/secrets, open-access sensitive data, or wants to act on
  a case. Always ends with a concrete action -- a Jira/ServiceNow ticket, assignment,
  status change, or object-level remediation (tombstone/move) -- offering only
  connected/configured integrations. Pulls live data from BigID MCP Production; drills
  into the Data Catalog for objects/files behind a case. Covers Security Posture /
  Actionable Insights (data-source policy) cases ONLY -- NOT privacy risk cases (use
  bigid-privacy-posture instead).
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
  ticketing/remediation channels that appear in the result. Never claim Jira or
  ServiceNow is available without confirming.
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

## Licensing & permissions

Check these before doing any triage work — fail fast and clearly if a module isn't
available, rather than discovering it mid-workflow.

1. **DSPM / Actionable Insights license (required — this skill cannot run without it).**
   Confirm the `Security Posture` server and its case tools (e.g.
   `get_actionable_insights_top_critical_cases`) are present via `list_servers` /
   `list_tools` before Step 1. If the server or its case tools are absent, or a case
   query errors with a license/entitlement message, stop and tell the user plainly: this
   tenant doesn't appear to have the DSPM / Actionable Insights module enabled, so
   security posture triage isn't available. Do not fall back to a different data source.

2. **Remediation license/permission (optional — not every tenant or user has this).**
   Object-level remediation (tombstone, archive/move, and other Delegated Remediation
   actions) requires its own license and is not guaranteed just because Security Posture
   is available. Before ever mentioning tombstone/move/remediation as an option, call:
   ```
   server_name = "Delegated Remediation API - AI Agent"
   tool_name   = "get_proxy_tpa_api_Remediation_settings_actions"
   arguments   = { "Accept-version": "<as required>" }
   ```
   - If this call fails (auth/entitlement error) or returns no enabled actions, **do not
     offer object-level remediation at all.** Drop it from the action menu — the user
     still gets the full triage menu (ticket / assign / status change).
   - If the response is an unhelpful or garbled error (not a clear auth/entitlement
     message) and the user asks why remediation isn't available, don't try to interpret
     or repeat the raw error. Tell them it looks like the Remediation module/license may
     not be enabled for this tenant, and that if that's not the case, they should contact
     BigID support to check the integration.
   - If the user directly asks for remediation ("tombstone this", "move these files")
     and it isn't licensed/enabled for them, say so plainly and redirect to the closest
     available triage action (e.g. a ticket for someone else to remediate manually, or a
     status change).
   - When remediation *is* available, still gate each individual action on its own
     `isEnabled` flag and `dsSupportedTypes` match (see Field notes) — a license unlocks
     the category, not every action inside it.

3. **Ticketing integration required before suggesting a ticket.** Never suggest "open a
   Jira ticket" or "open a ServiceNow ticket" as if either is always available — each
   needs its own configured integration, checked independently:
   - **Jira** — confirm via a case's own `ticketMetadata.ticketType`, or by confirming a
     Jira channel on execution; don't assume it exists just because ServiceNow does.
   - **ServiceNow** — confirm `ServiceNow IRM Integration` appears in `get_tpa_ids`.
   - **If neither Jira nor ServiceNow is configured**, don't propose ticket creation at
     all. Fall back to what's always available on a DSPM case — a **case status change**
     (acknowledge / silence / resolve) and/or **assignment** to a user — so the user
     still leaves with a concrete next step.

---

## Core principle: risk-first ordering

BigID's own `severityLevel` and affected-object count are the starting point, but this
skill applies an explicit **credential-exposure-first** override. Live credentials are
the fastest path to lateral movement and breach, so they jump the queue regardless of
raw object count.

Priority tiers, highest first:

1. **Tier 1 — Credentials.** Policy/compliance name contains any of (case-insensitive
   substring match): `password`, `passwd`, `token`, `api key`, `apikey`, `access key`,
   `secret key`, `secret`, `credential`, `private key`, `ssh key`, `oauth token`,
   `aws access key`, `connection string`. Ordered among themselves by severity then
   affected-object count.
2. **Tier 2 — Open-access high-sensitivity data.** Policy name contains `open access`
   AND at least one of: `high sensitivity`, `financial`, `payment card`, `pci`,
   `unencrypted`, `ssn`, `social security`, `bank account`, `phi`, `medical`.
3. **Tier 3 — Everything else**, ordered by severity (critical > high > medium > low)
   then affected-object count.

Within every tier, break ties by `numberOfAffectedObjects` descending. The keyword lists
above are exhaustive for this skill — don't treat any other policy-name substring as a
Tier 1 or Tier 2 trigger, and don't invent additional keywords on the fly.

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

Optional context tools (use only if asked for breakdowns/counts) -- always pass
`caseStatus: "open"` so these counts stay scoped to the same open-case set used
everywhere else in this skill (calling them with no status filter returns counts across
*all* statuses, including acknowledged/resolved/silenced, which will not match the ranked
list or total count above):
`get_actionable_insights_cases_by_severity` (`arguments = {"caseStatus": "open"}`),
`get_actionable_insights_cases_metadata` (distinct values for every filterable field --
no status filter available; note this to the user if asked for exact counts),
`get_actionable_insights_cases_group_by_policy` (`arguments = {"filter": "[{\"field\":\"caseStatus\",\"value\":\"open\",\"operator\":\"equals\"}]"}`).

**Parsing note:** results come back as a JSON string in `result`. If a call is stored to
`/mnt/user-data/tool_results/...` because it's too large, parse with `bash_tool` + Python:
load the file, `json.loads` it, and immediately project down to only the fields you need
(the list in the `fields` argument above) before doing anything else with it — case
objects carry large nested control blocks that are irrelevant to triage and will blow the
context budget if echoed in full. Never paste the raw JSON into the conversation; extract,
summarize, then discard.

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
- `Remediation`                  → object-level remediation (tombstone/move/etc.)

Jira is wired at the case-action level rather than always as a TPA — confirm via a case's
`ticketMetadata.ticketType` from Step 1, or offer it and verify on execution.

Then present a menu listing **only** the available channels — see "Action catalog" below.
Wait for the user to choose before executing (all are writes).

**No integrations configured?** If `get_tpa_ids` shows no ServiceNow, the case has no
Jira `ticketMetadata`, and Remediation isn't licensed/enabled (see "Licensing &
permissions" above), the menu collapses to what's always available on a DSPM case:
**assign to a user** and **case status change** (acknowledge / silence / resolve). Present
these as the default suggestion rather than leaving the user with no action at all.

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

**Open a ticket (Jira / ServiceNow) or sync an existing one** — `write_objects`. This is
the literal, resolved tool name — the embedded `actionType` and escaped colon are exactly
how BigID registers this tool; it is not a placeholder to fill in:
```
server_name = "Security Posture"
tool_name   = "post_actionable_insights_cases_\\::actionType_by_caseid"
arguments   = {
  "caseId": "<_id>",
  "type": "jira" | "service_now",
  "subType": "createTicket" | "fetchTicketAndSync"
}
```
- `type` selects the channel — `jira` or `service_now` (underscore, not `servicenow`).
- `subType` selects the operation — `createTicket` for a new ticket, or
  `fetchTicketAndSync` to pull the status of one already linked to the case.
- This tool's live schema documents only `jira` and `service_now` as supported `type`
  values — Jira and ServiceNow are the only ticketing channels this skill offers.

After executing, confirm and check for failure (`ticketUrl: "Creation Failed"` → tell the
user, offer retry or a different channel). Report success only when confirmed.

**Bulk action across a policy group** — `write_objects`. Same naming pattern as above —
this is the literal registered tool name, not a template:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_cases\\::actionType"
arguments   = {
  "type": "CasesDB", "subType": "updateCases",
  "additionalProperties": {
    "field": "assignee"|"caseStatus", "newValue": "<value>",
    "casesFilters": [{"filterField":"policyName","filterValues":["Passwords"]}],
    "auditReason": "<why>",
    "allCases": false,
    "userName": "<acting user, if required>"
  }
}
```
`allCases` (apply to every case matching the filter, not just a listed set) and
`userName` (the acting user, for audit) are optional per the live schema — include them
only when relevant.

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

`get_tpa_ids` returned, among others: `ServiceNow IRM Integration`, `Remediation`,
`Actions App (Scanner Based)`. Mapped to enabled remediation actions:

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

## Troubleshooting

Centralized reference for when something doesn't go as expected. Where a topic is
covered in more depth elsewhere in this file, that's cross-referenced rather than
repeated in full.

**Empty results.** A case, policy, or data-source query returning zero rows is a valid
answer, not a failure — say so plainly ("no open critical cases right now") rather than
retrying with progressively looser filters, unless the user asks for a broader window.

**Large / oversized results.** `get_actionable_insights_all_cases` and Data Catalog
queries can exceed the response size limit without field projection and paging. Use the
narrow `fields` list and `limit`/`skip` shown in Step 1. If a result still lands in
`/mnt/user-data/tool_results/...`, parse it locally per the Step 1 "Parsing note" — never
paste raw JSON into the conversation.

**Missing fields.** If an expected field is absent (a friendly `SPC-###` case number,
`ticketMetadata`, `assignee`, etc.), say it's not present rather than filling in a
plausible-looking guess — see "Do not guess" above.

**API / gateway / connection errors, including transient failures.** If a tool call
errors or times out:
- Retry once if it looks transient (timeout, gateway error).
- If it fails again, report the failure plainly — tool name and what it was trying to do
  — rather than silently substituting a guess or a different data source.
- Don't blindly retry a *write* (assign, status change, ticket, remediation). A
  failed-looking response can sometimes have partially applied; confirm with the user
  before retrying a write.

**License / module gaps.** See "Licensing & permissions" above for the specific checks
(DSPM module, Remediation entitlement, ticketing integrations). In every case: stop
before promising an action the tenant isn't entitled to, say plainly what's missing, and
offer the closest available alternative — no Remediation license → triage-only menu; no
ticketing integration configured → status change / assignment instead.

**Ambiguous input.** If the user references a case without enough to identify it
uniquely ("fix that case", "the one from before" with nothing shown yet this
conversation), prefer re-running Step 1/Step 3 to surface a short, named candidate list
they can pick from over asking an open-ended question. Fall back to asking which case
only when no reasonable candidate set can be produced.

**Tool-name uncertainty.** A few registered tool names look unusual — e.g. the escaped
colon and embedded parameter name in `post_actionable_insights_cases_\::actionType_by_caseid`
and `patch_actionable_insights_cases\::actionType`. These are confirmed live (via
`list_tools`) as the literal, correct tool names — not placeholders to fill in. If a call
to any tool in this file ever fails with a "not found" or schema-mismatch error, re-run
`list_tools` for the relevant server and use its live-returned name/schema over what's
written here, since BigID's Actions Center configuration can add or change fields over
time — re-verify with `list_tools` whenever a call behaves unexpectedly.

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

All ranking rubric, query, and catalog-drilldown detail referenced above now lives
directly in this file (see "Core principle" and "Workflow" sections) — there are no
separate reference files to consult.
