---
name: bigid-access-graph
description: >
  Build an interactive access graph from BigID Access Intelligence (ACI) data showing
  relationships between users, groups, permissions, and data resources. Use this skill whenever the
  user asks "who can access X", "what can user/group Y reach", "show me the access graph", "map
  permissions to resources", "show over-permissioned users", "open access risk", "external sharing
  risk", "access investigation", or any request combining BigID with identities, entitlements,
  permissions, RBAC, access relationships, or an access-graph visualization. Also trigger for casual
  phrasings like "who has write access to our sensitive files" or "graph out our data access".
  Output is a self-contained interactive HTML file with folder rollups, direct-vs-via-group grant
  paths, DSPM case links, and unused-access findings. Scope note: use this for org-wide or
  multi-resource access mapping; for a text-only deep dive on one named file/user/group, prefer
  the aci-effective-permissions skill if installed.
---

# BigID Access Graph

Build an interactive access graph (identities → permissions → resources) from live BigID ACI
data. The output answers two kinds of questions:

- **Access investigation**: "Who can access this resource?" / "What can this user or group reach?"
- **Risk reporting**: external identities, open-access resources, write/delete on sensitive data.

## Workflow overview

1. **Scope the question** — determine whether the user wants a specific resource/identity traced,
   a specific data source, or a whole-environment risk view. This decides your filters.
2. **Collect data** from the BigID MCP ACI tools into JSON files (see below).
3. **Build the graph** by running `scripts/build_graph.py` against those files.
4. **Deliver** the resulting HTML file to the user (present it so they can open it in a browser).

## Step 1 — Scope (folder/file level, guided)

**Never graph a whole data source.** DS-level maps are too large to render or compute — BigID
itself caps/samples results at that level, so the graph would silently show a subset and mislead.
Always narrow to folders, files, or an identity. If the user's request is broad ("show me our
access graph"), don't guess — suggest concrete choices:

1. Run `get_inventory_aggregation` (source aggregation, sort by docCount desc, limit 5) to get
   the top data sources by object count.
2. Offer those top 5 via AskUserQuestion (multiSelect) so the user picks the source(s).
3. Within the chosen source, sample `get_aci_data_manager` (limit ~40) and tally parent-folder
   paths from the FQNs; offer the top 5 folders by object count the same way. The user picks;
   that folder set is your scope.

Direct scope shortcuts, when the request already names a target:

- **Named folder or file pattern** → filter `get_aci_data_manager` by `objectName` (path regex)
  within the datasource.
- **Specific user or service account** ("what can svc-backup reach?") → collect objects from the
  identity's `dataSource` (from `get_aci_users`), fetch permissions, then keep only objects where
  that identity appears (directly or via a group per the derivation rules). Build the graph from
  that subset — it renders as the identity's reach, and the search box auto-centers on them.
  For a text-only answer with no visualization, the aci-effective-permissions skill is the
  better tool.
- **Risk view** → sensitive (`sensitivity` filter or `containsPI: true`) objects within the
  chosen folders, sorted toward high PII counts.

Keep 20–60 resources (folder rollups stretch how much ground that covers). More than ~100 nodes
per type gets cluttered and slow.

## Step 2 — Collect data

Call the BigID MCP tools and save the raw arrays as JSON files in a working directory.
All four files are expected by the build script (use empty arrays/objects if a call returns nothing).

| File | Tool | What to save |
|---|---|---|
| `users.json` | `get_aci_users` (paginate, limit 100) | the `data.users` array |
| `groups.json` | `get_aci_groups` (paginate, limit 100) | the `data.groups` array |
| `objects.json` | `get_aci_data_manager` (with filter) | the `data` array |
| `permissions.json` | `get_aci_data_manager_permissions` per object | dict: `fullyQualifiedName` → `data.permissions` array |
| `cases.json` | `get_security_cases` (caseStatus "open") | **flattened** array of `data.policies[].cases[]` |

`cases.json` powers the clickable risk findings: each risk in the graph shows related open DSPM
cases (same data source), with severity, affected-object counts, assignee, policy description, and
deep links. Flatten the nested policies→cases structure before saving — each element should be one
case object. Fetch enough pages to cover the data sources in scope.

**Optional files — include when the environment exposes the data, skip otherwise.** The build
script adapts automatically: missing files simply disable the corresponding graph features, and
it prints a note about what was skipped (mention that in your summary).

| File | Source | Enables |
|---|---|---|
| `enrichment.json` | `get_catalog_objects` (same filter scope as objects) | tag-based sensitivity + activity/staleness overlay |
| `memberships.json` | group→members data, if any tool exposes it | ground-truth membership edges and via-group paths |

`enrichment.json` is a dict of `fullyQualifiedName` → `{"sensitivity", "last_opened",
"lastAccessedBy", "modified_date"}`. Build it from `get_catalog_objects` results: sensitivity is
the tag value where `tagName` contains `sensitivityClassification` (values like Restricted,
Confidential, Internal Use, Public), and the activity fields come straight off the object. Many
environments leave `last_opened`/`lastAccessedBy` empty — include whatever is populated; if
nothing is, skip the file. When sensitivity tags are present they override the PII-count
heuristic; when activity is present, the graph gains a stale filter and "unused exposure"
findings (open/sensitive data untouched for 90+ days — prime revocation candidates).

`memberships.json` is a dict of group name/email → array of member names/emails. The BigID MCP
does not currently expose group members, so this usually doesn't exist — do NOT burn calls
hunting for it. If provided (e.g. from an IdP export or a future MCP tool), membership becomes
ground truth for direct-vs-via-group instead of the access-set inference, and dotted member
edges appear in the graph.

Notes that save time:

- `get_aci_data_manager_permissions` takes `itemPath` = the object's `fullyQualifiedName`, and
  returns effective permissions: `{name, email, access: ["READ","WRITE","EXECUTE","DELETE"],
  type: "user"|"group"|"link", grantType}`. This is the highest-quality edge data — fetch it for
  every object you include (it's one call per object, so this is the main reason to keep object
  count moderate). If a permissions call fails for an object, skip it; the build script falls
  back to the object's `annotations.sharedWith` / `sharedWithGroup`.
- **Also fetch permissions for each unique parent folder** of your scoped objects (folder paths
  work as `itemPath` too) and include them in `permissions.json` under the folder's path. Files
  cluster in few folders, so this adds only a handful of calls — and it's what enables true
  Direct-vs-Inherited labeling (see the effective-permission model below).
- Objects carry risk context in `annotations` (`openAccess`, `sharedWithGroup`) and
  `objectDetails` (`total_pii_count`, `attribute` classifier list, `sizeInBytes`).
- Users and groups carry `external` (bool), `dataSource`, `sharedObjectsCount`, and for groups
  sometimes `membersCount`. The build script matches these to permission entries by email/name to
  flag external identities in the graph — so always fetch users/groups even for a single-resource
  question.
- Not every identity in permissions appears in the ACI users list (e.g. local Windows SIDs).
  That's expected; they still become graph nodes.
- **The effective-permission model**: an identity reaches a file/folder one of four ways —
  (1) a direct grant, (2) a sharing link (collaboration platforms), (3) group membership, or
  (4) inheritance from a parent folder (direct or via group on the parent). BigID's permissions
  endpoint returns the already-expanded effective list; the build script labels each edge's
  path, in priority order: declared `grantType` (DIRECT/EXPLICIT/INHERITED) when present →
  **parent-folder ACL comparison** (an entry that also appears on the parent's ACL with covering
  access is `inherited`, tagged with the folder or granting group) → known membership from
  `memberships.json` (grant on the object → `via-group`; on the parent → `inherited`) →
  access-set inference (a group with same-or-broader access on the object → `via-group`; on the
  parent → `inherited`) → otherwise `direct`. Entries of type `link` are `sharing`. Solid edges
  = direct, dashed = via group, faint short-dash = inherited, teal = sharing link; the detail
  panel names the folder/group behind every non-direct edge. When only inference was available
  (no grantType, no parent ACLs, no memberships), say so in your summary so users know the
  labels are derived rather than declared.

## Step 3 — Build

```bash
python3 <skill_dir>/scripts/build_graph.py \
  --data-dir <dir with the 4 json files> \
  --template <skill_dir>/assets/graph_template.html \
  --out <outputs>/access_graph.html \
  --title "Access Graph — <scope description>" \
  --bigid-url "https://<customer>.bigid.cloud" \
  --snapshot-dir <stable dir, e.g. next to the output>/snapshots
```

Two more options worth knowing:

- `--rollup N` (default 3): files sharing the same folder AND identical ACL collapse into a
  single folder node with a file count — this is what lets one graph cover big shares without
  clutter. Pass `--rollup 0` only if the user explicitly wants every file as its own node.
- `--snapshot-dir`: saves a state snapshot each run and, when a previous snapshot exists, adds a
  "Changes since last run" panel (new grants, removed grants, newly open-access resources, new
  external identities). Use a stable directory so recurring runs diff against each other — this
  pairs well with a scheduled weekly run. Include notable changes in your summary.

`--bigid-url` enables "Open case in BigID" deep links on risk findings. If you don't know the
user's BigID portal URL, ask them once (it's worth it — clickable cases are a key feature). Links
use the pattern `{base}/#/actionable-insights/case/{caseId}`; if their BigID version routes cases
differently they can tell you and you can pass `--case-url-template`. Cases with Jira/ServiceNow
tickets also get a ticket link automatically (from `ticketUrl`), which works even without
`--bigid-url`.

The script merges everything into a node/edge model, computes risk flags (external identity,
open access, write-or-delete on sensitive data), and injects it into the template. It prints a
summary (node/edge counts, top risks) — use that in your reply to the user.

## Step 4 — Deliver

Present the HTML file. In your summary, lead with findings, not mechanics: name the riskiest
resources (open access + high PII), any external identities with write access, and the biggest
access hubs. If the user asked an investigation question ("who can access X"), answer it directly
in text as well — the graph supports the answer, it doesn't replace it.

## The graph itself

The template renders a Cytoscape.js graph in a three-column **layered layout**
(users → groups → resources, left to right; columns re-pack automatically as filters change).
Features: type-colored nodes, access-level edges, search, filters (external only, open access
only, per-access-level), a reset-filters button, zoom in/out/fit controls, click-to-inspect
detail panel, neighborhood tracing (background click returns to full view), and a **clickable
risk findings panel** — each finding expands to show related open DSPM cases with severity,
affected objects, assignee, and links into BigID / ticketing. Everything is client-side and
self-contained — safe to email or open offline.

If the user asks for changes (different colors, extra filters, another layout), edit the generated
HTML directly rather than the template.
