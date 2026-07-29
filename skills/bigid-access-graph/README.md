# Access Graph

Build an interactive access graph from **BigID Access Intelligence (ACI)** data — showing who (users, groups, sharing links) can reach what (folders, files), with which permissions, and *how* they got that access.

![Skill type](https://img.shields.io/badge/type-Claude%20skill-6b4eff) ![Data](https://img.shields.io/badge/data-BigID%20MCP-ff3e8a) ![Output](https://img.shields.io/badge/output-interactive%20HTML-ff8a3d)

## What it does

Ask things like:

- *"Who has write access to our sensitive SMB files?"*
- *"What can the svc-backup service account reach?"*
- *"Show our open access and external sharing risk as a graph I can click around in"*
- *"Run the weekly access graph and tell me what changed"*

The skill pulls live data through the BigID MCP and produces a **self-contained interactive HTML file** — no server, no dependencies, safe to email or open offline.

## The graph

Three columns: **identities → groups/links → resources**.

| Element | Meaning |
|---|---|
| Purple circles | Users (red ring = external) |
| Pink rectangles | Groups |
| Teal tags | Sharing links |
| Orange diamonds | Resources (double border = folder rollup; amber ring = open access) |
| Solid edge | Direct grant |
| Dashed edge | Access via group membership |
| Faint short-dash edge | Inherited from a parent folder |
| Teal edge | Sharing link |

Interactive features: search, per-access-level and grant-path filters, risk filters (external / open access / sensitive / stale), zoom + fit controls, filter reset, resizable detail panel, click-to-trace neighborhoods, and a **clickable risk findings panel** — each finding expands to related open DSPM cases (severity, affected objects, assignee) with links into BigID and Jira/ServiceNow tickets.

## How access is calculated

An identity reaches a file/folder one of four ways: **direct grant**, **sharing link**, **group membership**, or **inheritance from a parent folder**. BigID returns the already-expanded effective permission list; the skill labels each edge's grant path, in priority order:

1. Declared `grantType` (DIRECT / EXPLICIT / INHERITED) when the connector provides it
2. **Parent-folder ACL comparison** — an entry that also appears on the parent's ACL is inherited; a group whose grant is itself inherited transmits "inherited" to its members
3. Known group membership (when membership data is available)
4. Access-set inference — a group on the same resource holding equal-or-broader access

When only inference was available, the summary says so — labels are derived, not declared.

## Scoping rules

- **Never a whole data source** — BigID caps/samples DS-level results, so the graph scopes to folders, files, or a single identity.
- Broad requests trigger **guided scoping**: the skill suggests the top 5 data sources by object count, then the top 5 folders within your pick.
- 20–60 resources per graph; **folder rollup** collapses files sharing a folder + identical ACL into one node so a single graph covers large shares.

## Data collected (via BigID MCP)

| Data | Tool | Required |
|---|---|---|
| Users, groups | `get_aci_users`, `get_aci_groups` | Yes |
| Objects in scope | `get_aci_data_manager` | Yes |
| Effective permissions (objects **and parent folders**) | `get_aci_data_manager_permissions` | Yes |
| Open DSPM cases | `get_security_cases` | Optional — clickable case insight |
| Sensitivity tags + activity (`last_opened`) | `get_catalog_objects` | Optional — tag-based sensitivity, stale/unused findings |
| Group memberships | not exposed by the MCP today | Optional — ground-truth membership edges if supplied |

Optional data is used when the environment exposes it and **silently skipped when it doesn't** — the graph adapts (features and filters appear only when backed by real data).

## Options

| Flag | Default | Purpose |
|---|---|---|
| `--rollup N` | 3 | Collapse ≥N same-folder, same-ACL files into a folder node (0 disables) |
| `--snapshot-dir` | off | Save run snapshots; adds a "Changes since last run" panel (new/removed grants, newly open, new external) — pairs well with a scheduled weekly run |
| `--bigid-url` | off | Enables "Open case in BigID" deep links on risk findings |
| `--case-url-template` | `{base}/#/actionable-insights/case/{caseId}` | Adjust if your BigID version routes cases differently |

## Risk findings

Generated automatically: open access on data (with PII counts), WRITE/DELETE on sensitive data, external identities with write access, and — when activity data exists — **unused exposure** (open/sensitive data untouched for 90+ days: prime revocation candidates). Each finding highlights the affected node and links to related DSPM cases.

## Files

```
access-graph/
├── SKILL.md                    # workflow + BigID MCP collection guide
├── scripts/build_graph.py      # merges JSON exports → graph model → HTML
└── assets/graph_template.html  # Cytoscape.js template (single file, CDN-only)
```

## Requirements

- BigID MCP connection with Access Intelligence (ACI) enabled
- Sensitivity tags, activity fields, DSPM cases, and group memberships are all optional enhancers

## Known limitations

- Via-group and inherited labels fall back to inference in environments that flatten `grantType` to EFFECTIVE and expose no membership data
- Activity is object-level (`last_opened`) — per-identity usage isn't exposed by the MCP yet
- ~100 nodes per column is the practical rendering ceiling; scope tighter or raise `--rollup`
