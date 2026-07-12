---
name: bigid-shadowai-and-ai-risk
description: >
  Triages BigID DSPM security cases scoped to AI risk and Shadow AI -- credentials or
  regulated data sitting inside AI/LLM platforms, vector stores, model packages, and
  training datasets, plus AI assets exposed via open/external access. Use when the user
  asks about AI risk posture, Shadow AI, ungoverned AI/LLM usage, exposed AI models,
  vector database exposure, data flowing into ChatGPT/OpenAI/Azure OpenAI/Hugging
  Face/SageMaker/vector stores, "what AI risks do we have", "any shadow AI", "AI assets
  exposed", or wants to act on an AI-related DSPM case. Always ends with a concrete
  action -- a Jira/ServiceNow ticket, assignment, status change, or object-level
  remediation -- offering only connected/configured integrations. Pulls live data from
  BigID MCP Production (Security Posture cases + Data Catalog objects). Covers Security
  Posture / Actionable Insights cases scoped to AI -- NOT general (non-AI) security
  posture triage (use bigid-security-posture) and NOT privacy risk cases (use the
  privacy posture skill).
compatibility: "Requires: BigID MCP Production server only (Security Posture, Data Catalog, Delegated Remediation, get_tpa_ids tools), bash_tool for parsing large results. No npm/assets/other connectors."
---

# BigID AI Risk & Shadow AI Posture Skill

Reads live DSPM cases from BigID, narrows them to the AI-related surface (AI-native
policies, AI/LLM/vector-store data sources, and AI assets such as models/datasets/
vectors), ranks them by AI-specific risk, optionally drills into the objects behind a
case, and drives the user to a concrete remediation action.

## Tooling rule — BigID MCP only

This skill uses the **BigID MCP Production server exclusively**. Every read and every
action goes through: `BigID MCP Production:list_servers`, `:list_tools`, `:get_objects`
(reads), `:write_objects` (writes), and `:get_tpa_ids` (integration discovery).

Do **not** use web search, the browser, other connectors, or any non-BigID tool to get
posture data or take actions. Do **not** fabricate a REST call outside these MCP tools.
If a needed capability isn't exposed by a BigID MCP tool, say so plainly.

## When to use

Any time the user wants to understand or act on AI-specific data risk. Triggers:
- "what's our Shadow AI exposure?" / "any ungoverned AI usage?"
- "AI risk posture" / "AI security posture review"
- "is sensitive data going into ChatGPT / OpenAI / Azure OpenAI / Copilot / our LLMs?"
- "any exposed AI models or vector databases?"
- "credentials in our training data / model packages?"
- "which AI assets are open access?"
- "what should I fix first on the AI side?"
- "which objects/files are behind case X?" (→ Catalog drilldown, see Step 6)

This skill is a **scoped view of Security Posture / Actionable Insights cases** — the
same case store `bigid-security-posture` triages, filtered down to the AI-related
surface. It is NOT a separate AI inventory product and NOT privacy risk cases (those are
covered by the privacy posture skill). If the user wants general (non-AI) DSPM triage,
that's `bigid-security-posture`'s job — mention the handoff if asked for both.

## Important framing — "Shadow AI" here is inferred, not a native BigID label

BigID's case metadata has no dedicated `isShadowAI` flag. This skill infers Shadow-AI
risk from a heuristic combination of signals (below) — it does not claim BigID
natively certifies something as "shadow." Always present Shadow-AI flags as
**candidates for investigation**, not confirmed findings, and say so explicitly when
presenting them.

## Do not guess

- **Discover, don't assume, the AI surface.** The set of AI-related policy names,
  data-source types, and data-source names is tenant-specific and changes over time.
  Always rediscover it each session (Step 1) rather than hardcoding the examples in this
  file as exhaustive.
- **Discover, don't assume, server/tool names.** Call `list_servers` / `list_tools`
  first if unsure a tool exists.
- **Discover, don't assume, connected integrations.** Run `get_tpa_ids` and only offer
  ticketing/remediation channels that appear in the result.
- **Discover, don't assume, configured remediation actions.** Call the Remediation
  "list available actions" tool before offering tombstone/move/etc.
- **Don't invent IDs, counts, policy names, or assignees.** Read them from live results.
- **Verify writes.** Report a ticket/assignment/remediation as successful only when the
  response confirms it.
- If a query returns nothing or errors, report that — do not substitute a plausible-
  looking answer.

---

## Licensing & permissions

Same gating as `bigid-security-posture` — check before doing any triage work:

1. **DSPM / Actionable Insights license (required).** Confirm the `Security Posture`
   server and its case tools are present via `list_servers` / `list_tools` before Step 1.
   If absent, or a case query errors with a license/entitlement message, stop and tell
   the user plainly: this tenant doesn't appear to have DSPM enabled, so AI risk posture
   isn't available. Do not fall back to a different data source.
2. **Remediation license/permission (optional).** Before ever mentioning tombstone/move
   as an option, call:
   ```
   server_name = "Delegated Remediation API - AI Agent"
   tool_name   = "get_proxy_tpa_api_Remediation_settings_actions"
   arguments   = { "Accept-version": "<as required>" }
   ```
   If this fails or returns no enabled actions, drop object-level remediation from the
   menu — the user still gets the full triage menu (ticket / assign / status change).
3. **Ticketing integration required before suggesting a ticket.** Check independently:
   - **Jira** — via a case's own `ticketMetadata.ticketType`, or confirm on execution.
   - **ServiceNow** — confirm `ServiceNow IRM Integration` appears in `get_tpa_ids`.
   - If neither is configured, fall back to case status change and/or assignment.

---

## Step 1 — Discover this session's AI surface (always do this first)

Never hardcode the AI surface. Pull it fresh every session:

```
server_name = "Security Posture"
tool_name   = "get_actionable_insights_cases_metadata"
arguments   = {}
```

This returns distinct values for `policyName`, `compliance`, `dataSourceName`, and
`dataSourceType` across all open cases. From the result, build three lists:

1. **AI-native policies** — any `policyName`/`compliance` value containing (case-
   insensitive) `ai `, `ai-`, `"ai"` as a whole word, `llm`, `model`, `vector`, or
   `genai`. Confirmed live examples to expect (not exhaustive, re-verify): `AI Assets`,
   `Open Access AI Models`, `AI Vector with Confidential Sensitive Data`.
2. **AI-platform data source types** — any `dataSourceType` that is a known AI/ML/vector
   platform. Confirmed live examples: `openai`, `azure-openai`, `hugging-face`,
   `amazon-sagemaker`, `atlas-vectorsearch`, `elastic-vector-search`. Treat ambiguous
   platforms that serve both AI and general data-engineering workloads (e.g.
   `databricks-v2`) as AI-adjacent, not confirmed AI, and say so if you include them.
3. **AI-flagged data source names on non-AI-typed sources** — `dataSourceName` values
   that read as AI/LLM usage even though their `dataSourceType` is ordinary
   infrastructure (S3, SMB, GDrive, etc.). Confirmed live examples: `AI Datasets`,
   `AI Code`, `In-House AI Applications`, `with LLM Supervision`, `without LLM
   Supervision`, `LLM Policies classification`. **This list is the strongest Shadow-AI
   signal** — it's AI activity that isn't even running on a recognized AI platform type,
   i.e. adopted outside the data sources that would normally get AI-specific governance.

Tell the user up front which policies/sources you identified as "AI" this session so the
scoping is transparent (e.g. "Scoping to N AI-related policies and M AI-related data
sources found in this tenant right now").

## Core principle: AI-risk-first ordering

Within the AI-scoped case set, apply this tier order (highest risk first):

1. **Tier 1 — Credentials/secrets on AI infrastructure.** `policyName` is a credential-
   class policy (`Tokens, Keys and Secrets`, `Passwords`, `Security - Passwords`,
   `Security - Private Keys`, or any name containing `password`/`token`/`secret`/`key`/
   `credential`) **AND** the case's `dataSourceType` or `dataSourceName` is in the AI
   surface from Step 1. This is the worst combination: a leaked key inside training
   data, a fine-tuning dataset, or a model package can propagate into every model
   trained on it, and a credential embedded in a vector index may not be fully purgeable
   by deleting the source file alone.
2. **Tier 2 — AI-native policy hits.** `policyName` is one of the AI-native policies
   identified in Step 1 (e.g. `AI Assets`, `Open Access AI Models`, `AI Vector with
   Confidential Sensitive Data`) — over-permissioned or exposed models, vectors, or
   AI-tagged assets.
3. **Tier 3 — Regulated/sensitive data flowing into AI, especially ungoverned AI.**
   `policyName` is a privacy/compliance/high-sensitivity policy (PII, PHI, PCI,
   financial, GDPR-family, HIPAA, regional privacy laws, etc.) **AND** the data source
   is in the AI surface from Step 1. **Flag as a Shadow-AI candidate** (see framing note
   above) when the `dataSourceName` is one of the "AI-flagged name on non-AI-typed
   source" signals (e.g. `without LLM Supervision`) rather than a formally provisioned
   AI-platform type — that combination is sensitive data moving through AI usage that
   isn't running through a recognized, governed AI connector.
4. **Tier 4 — Everything else on an AI-related data source** (misconfigurations,
   stale-data, access-logging-disabled, etc.), ordered by severity then affected-object
   count.

Within every tier, break ties by `numberOfAffectedObjects` descending, then severity.

---

## Workflow

### Step 2 — Pull the AI-scoped case set

Use the lists built in Step 1 to filter. Prefer filtering on `policyName` or
`dataSourceType`/`dataSourceName` (`in` operator), request a narrow field set (case
objects carry large nested control blocks that otherwise truncate large responses):

```
server_name = "Security Posture"
tool_name   = "get_actionable_insights_all_cases"
arguments   = {
  "filter": "[{\"field\":\"caseStatus\",\"value\":\"open\",\"operator\":\"equals\"},{\"field\":\"dataSourceType\",\"value\":[\"openai\",\"azure-openai\",\"hugging-face\",\"amazon-sagemaker\",\"atlas-vectorsearch\",\"elastic-vector-search\"],\"operator\":\"in\"}]",
  "fields": "[\"caseId\",\"_id\",\"caseLabel\",\"severityLevel\",\"policyName\",\"compliance\",\"numberOfAffectedObjects\",\"dataSourceName\",\"dataSourceType\",\"dataSourceDisplayName\",\"assignee\",\"caseStatus\",\"ticketMetadata\"]",
  "sort": "[{\"field\":\"numberOfAffectedObjects\",\"desc\":true}]",
  "limit": 50,
  "requireTotalCount": true
}
```

Run a second pass (or a combined `OR`-style pair of calls) for cases whose
`policyName` is AI-native or whose `dataSourceName` matches the "AI-flagged name on
non-AI-typed source" list from Step 1, since those won't be caught by the
`dataSourceType` filter above:

```
"filter": "[{\"field\":\"caseStatus\",\"value\":\"open\",\"operator\":\"equals\"},{\"field\":\"policyName\",\"value\":[\"AI Assets\",\"Open Access AI Models\",\"AI Vector with Confidential Sensitive Data\"],\"operator\":\"in\"}]"
```
```
"filter": "[{\"field\":\"caseStatus\",\"value\":\"open\",\"operator\":\"equals\"},{\"field\":\"dataSourceName\",\"value\":[\"AI Datasets\",\"AI Code\",\"In-House AI Applications\",\"with LLM Supervision\",\"without LLM Supervision\",\"LLM Policies classification\"],\"operator\":\"in\"}]"
```

Merge and de-duplicate by `caseId`/`_id` before ranking.

**Parsing note:** results come back as a JSON string in `result`. If stored to
`/mnt/user-data/tool_results/...` because it's large, parse with `bash_tool` + Python:
load, `json.loads`, project down to only the needed fields immediately. Never paste raw
JSON into the conversation.

### Step 3 — Rank with the AI-risk-first rule

Apply the four-tier ordering above to the merged, de-duplicated set; produce the top 3
(or top N if asked). For each case capture: caseId (friendly `SPC-###` if present, else
`_id`), caseLabel, severityLevel, numberOfAffectedObjects, dataSourceDisplayName /
dataSourceType, policyName, current assignee, ticket status, and whether it's flagged as
a Shadow-AI candidate (Tier 3 rule above).

### Step 4 — Present the ranked list

Lead with why #1 is #1 (e.g. "credentials detected inside a SageMaker model package —
critical, 7 objects"). Keep it tight. Call out cross-cutting patterns (e.g. one AI
platform dominating, or a cluster of Shadow-AI-candidate cases on the same
ungoverned-sounding data source). Clearly label any Shadow-AI flags as inferred, not a
native BigID classification. No raw JSON.

### Step 5 — Propose a concrete action (always)

Never end at a list. Discover what's available first:

```
tool_name = "get_tpa_ids"   (no server_name needed)
arguments = {}
```

Map result keys to channels: `ServiceNow IRM Integration` → ServiceNow ticketing;
`Remediation` → object-level remediation. Jira is wired at the case-action level —
confirm via `ticketMetadata.ticketType` or offer and verify on execution.

Present a menu of **only** the available channels (see "Action catalog" below). Wait for
the user to choose before executing (all are writes).

**No integrations configured?** Menu collapses to what's always available: assign to a
user, and case status change (acknowledge / silence / resolve).

**AI-specific caveat to surface for Tier 1 (credentials found in AI artifacts) before
recommending destructive remediation:** revoking access or even deleting the source file
does **not** retroactively remove a secret from a model that was already trained/
fine-tuned on it, nor from a vector already embedded in an index. Say this plainly —
rotating the credential is still necessary, and purging it from the model/vector store
itself is a separate action for the AI/ML platform team, outside what BigID remediation
can execute. Don't imply BigID's remediation actions clean the model or vector store.

### Step 6 — Drill into specific AI objects/files (only when asked)

If the user asks which objects are behind a case ("show me the models", "which
datasets", "list the vectors"), use the Data Catalog, scoped to the case's data source
and policy, and optionally to AI object types:

```
server_name = "Data Catalog"
tool_name   = "post_data_catalog"
arguments   = {
  "filter": "source = \"<dataSourceName>\" AND policy = \"<policyName>\"",
  "limit": 20,
  "requireTotalCount": "true"
}
```

To look at AI-native artifact types directly (confirmed live values: `model`, `dataset`,
`vector` — re-verify, as new object types can appear), filter on `objectType`:

```
"filter": "objectType IN (\"model\",\"dataset\",\"vector\") AND source = \"<dataSourceName>\""
```

Each result row carries `objectName`, `fullyQualifiedName`, `attribute`/
`attribute_details` (matched classifiers, e.g. `Tokens, Keys and Secrets (Narrow)`),
sensitivity `tags` (confirmed tag name: `system.sensitivityClassification.Sensitivity`,
e.g. value `Confidential`/`Restricted` — filter with
`tags."system.sensitivityClassification.Sensitivity" = "Confidential"`), `owner`, and a
`messageLink`. Response tail carries `totalRowsCounter` and `estimatedCount` (the true
total — can be large; e.g. a single AI-platform sample query returned an
`estimatedCount` in the thousands, so always page with `limit`/`skip` rather than
pulling everything).

Just need the count? Use `get_data_catalog_count` with the same filter. Need one
object's detail? `get_data_catalog_object_details` (by `object_name`), and
`get_data_catalog_object_details_columns` / `_attributes` for column/attribute-level
findings.

Present objects as a short table (name, object type, matched classifier, sensitivity,
owner) — never paste raw JSON.

---

## Action catalog

Offer only what discovery (Step 5) confirmed is available. Identical mechanics to
`bigid-security-posture` — reproduced here so this skill is self-contained.

### A) Triage actions — case level (Security Posture server)

**Assign to a user** — `write_objects`:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_cases_by_caseid"
arguments   = { "caseId": "<_id>", "assignee": "<email>" }
```

**Change case status** — `write_objects`. Valid statuses: `open`, `closed`, `resolved`,
`acknowledged`, `remediated`, `silenced`:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_case_status_by_caseid"
arguments   = { "caseId": "<_id>", "caseStatus": "acknowledged", "auditReason": "<why>" }
```

**Open a ticket (Jira / ServiceNow) or sync an existing one** — `write_objects`. This is
the literal, resolved tool name — the embedded `actionType` and escaped colon are exactly
how BigID registers this tool:
```
server_name = "Security Posture"
tool_name   = "post_actionable_insights_cases_\\::actionType_by_caseid"
arguments   = {
  "caseId": "<_id>",
  "type": "jira" | "service_now",
  "subType": "createTicket" | "fetchTicketAndSync"
}
```
After executing, confirm and check for failure (`ticketUrl: "Creation Failed"` → tell
the user, offer retry or a different channel).

**Bulk action across a policy group** — `write_objects` (literal registered tool name).
This mutates every case matching `casesFilters` in one call, so treat it with the same
care as object-level remediation: (1) first run the matching read query (Step 2's filter
shape) to get the actual count of cases the filter will hit, (2) state that count to the
user explicitly ("this will update N cases matching policy `AI Assets`"), (3) get
explicit confirmation of the field/value and filter before executing, and (4) prefer a
narrower filter or a single-case action over `allCases: true` where one will do:
```
server_name = "Security Posture"
tool_name   = "patch_actionable_insights_cases\\::actionType"
arguments   = {
  "type": "CasesDB", "subType": "updateCases",
  "additionalProperties": {
    "field": "assignee"|"caseStatus", "newValue": "<value>",
    "casesFilters": [{"filterField":"policyName","filterValues":["AI Assets"]}],
    "auditReason": "<why>",
    "allCases": false,
    "userName": "<acting user, if required>"
  }
}
```

### B) Remediation actions — object level (Delegated Remediation API - AI Agent server)

These **modify or relocate data**. Always: (1) confirm the action is configured via
discovery, (2) show the user the affected objects (Step 6), (3) get explicit
confirmation, then execute.

**Discover configured actions first:**
```
server_name = "Delegated Remediation API - AI Agent"
tool_name   = "get_proxy_tpa_api_Remediation_settings_actions"
arguments   = { "Accept-version": "<as required>" }
```

> **Containment before destruction, and mind the AI-specific caveat above.** For
> credential-exposure-on-AI-infrastructure cases, prefer non-destructive containment
> (Revoke External/Open Access, Move) first, then a ticket to rotate the secret. Only
> consider delete/tombstone of the source object after rotation is confirmed — and even
> then, tell the user that removing the source file does not purge a model or vector
> index already built from it; that's a separate action for the AI/ML platform owner.

**Available object-level actions** (confirm each is configured and each `isEnabled`
before offering): Tombstone, Archive/Move, and other configured actions depending on
tenant configuration.

**Execute a background remediation action** — `write_objects`:
```
server_name = "Delegated Remediation API - AI Agent"
tool_name   = "post_proxy_tpa_api_Remediation_execute"
arguments   = { "Accept-version": "<...>", "actionName": "<...>", "actionParams": [ ... ] }
```
Track status with `get_proxy_tpa_api_Remediation_settings_sync_audit_trail` /
`..._by_id` (using the returned `executionId`).

---

## Field notes — confirmed-live patterns

Verified against the live tenant at the time this skill was written. Prefer them over
guessing; still re-discover each session (Step 1, plus `get_tpa_ids` and Remediation
list-actions) in case tenant configuration or the AI surface has changed.

- **AI-native policies seen live:** `AI Assets`, `Open Access AI Models`, `AI Vector
  with Confidential Sensitive Data`.
- **AI-platform `dataSourceType` values seen live:** `openai`, `azure-openai`,
  `hugging-face`, `amazon-sagemaker`, `atlas-vectorsearch`, `elastic-vector-search`.
- **Shadow-AI-flavored `dataSourceName` values seen live (on ordinary infra types like
  `s3-v2`/`smb_v2`, not an AI-typed data source):** `AI Datasets`, `AI Code`, `In-House
  AI Applications`, `with LLM Supervision`, `without LLM Supervision`, `LLM Policies
  classification`.
- **Catalog `objectType` values seen live for AI assets:** `model` (e.g. a SageMaker
  `ModelPackage`), `dataset` (e.g. a SageMaker training-data file), `vector` (e.g. an
  Elastic/Atlas vector-search entry). `extendedObjectType` mirrors `objectType` for
  these.
- **Sensitivity tag seen live:** `tagName = "system.sensitivityClassification.Sensitivity"`
  with values including `Confidential` and `Restricted`.
- **Worked real example (Tier 1):** a live case, `Tokens, Keys and Secrets detected on
  Amazon SageMaker` (critical, 7 affected objects), corresponded to catalog objects of
  `objectType: "model"` and `objectType: "dataset"` on `amazon-sagemaker`, each carrying
  a `classifier.Tokens, Keys and Secrets (Narrow)` finding — i.e. a credential embedded
  directly in a model package and its training dataset. This is the canonical Tier-1
  pattern this skill is built to surface first.
- **Volume caution:** a single `post_data_catalog` query scoped to six AI-platform
  sources returned an `estimatedCount` in the low thousands from a handful of sample
  rows — always page (`limit`/`skip`) rather than requesting everything at once.

---

## Troubleshooting

**Empty AI surface.** If Step 1's metadata call returns no policy/data-source values
matching the AI patterns, say so plainly ("no AI-related cases or data sources detected
in this tenant right now") rather than forcing a result — this is a valid, good answer.

**Empty results on a scoped query.** A filtered case or catalog query returning zero
rows is a valid answer, not a failure.

**Large / oversized results.** `get_actionable_insights_all_cases` and Data Catalog
queries can exceed response size limits without field projection and paging. Use the
narrow `fields` list and `limit`/`skip` shown above. If a result lands in
`/mnt/user-data/tool_results/...`, parse it locally with `bash_tool` + Python and
project down immediately — never paste raw JSON into the conversation.

**Missing fields.** If an expected field is absent, say it's not present rather than
filling in a plausible-looking guess.

**API / gateway / connection errors, including transient failures.** Retry once if it
looks transient. If it fails again, report the failure plainly (tool name, what it was
trying to do). Don't blindly retry a write; confirm with the user first if a prior
attempt may have partially applied.

**License / module gaps.** See "Licensing & permissions" above. Stop before promising an
action the tenant isn't entitled to; offer the closest available alternative.

**Ambiguous input.** If the user references a case without enough to identify it
("fix that AI case", "the one from before"), prefer re-running Step 2/3 to surface a
short, named candidate list over asking an open-ended question.

**Tool-name uncertainty.** `post_actionable_insights_cases_\::actionType_by_caseid` and
`patch_actionable_insights_cases\::actionType` are confirmed live, literal tool names
(escaped colon and embedded parameter name included) — not placeholders. If a call to
any tool in this file fails with a "not found" or schema-mismatch error, re-run
`list_tools` for the relevant server and use its live-returned name/schema over what's
written here.

**"Is this really Shadow AI?"** This skill's Shadow-AI flag is a heuristic (Tier 3 rule
above), not a BigID-native classification. If the user pushes on confidence, say plainly
that it's inferred from data-source naming and policy combinations, and that confirming
it as genuinely unsanctioned usage requires human review (e.g. checking with the data
source owner or the team that provisioned it).

---

## Guardrails

- **BigID MCP only.** No web, browser, or other connectors for posture data or actions.
- **Rediscover the AI surface every session.** Never treat the examples in this file as
  an exhaustive, permanent list — the tenant's actual AI-related policies and data
  sources can change (Step 1).
- **Read before write.** Rank and present (Steps 2-4) before proposing actions.
- **Discover before offering.** `get_tpa_ids` for channels; Remediation list-actions for
  remediation options. Offer only what's confirmed.
- **Confirm writes**, especially object-level remediation. Get explicit user
  confirmation of the target case/objects and channel first.
- **Use the right caseId.** Write endpoints take the Mongo `_id`; show the friendly
  `SPC-###` to the user.
- **Never overclaim remediation scope.** BigID actions operate on the source object —
  they do not retrain a model or purge a vector index. Say so when relevant (Step 5).
- **Label Shadow-AI flags as inferred**, not confirmed, every time they're presented.
- **Verify, don't assume.** Report success only when the response confirms it.
