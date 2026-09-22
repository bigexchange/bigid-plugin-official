# BigID Plugin

The BigID Plugin connects your AI agent directly to your BigID environment. Get full visibility into your data security posture across DSPM, privacy, and compliance — all in natural language. Manage regulatory risk, automate compliance assessments, and detect policy violations in real time.

## Skills

Skills are context-aware instruction sets that activate automatically when relevant. When you ask about security cases, compliance evidence, or AI risk, the right skill kicks in — no slash commands needed. Each skill knows which BigID APIs to call, how to interpret the results, and what remediation actions are available.

## MCP Server

> **Early Adopters Program**
> The BigID MCP Server is currently available as part of an Early Adopters Program. To join the program and get access, contact BigID support or reach out at [mcp@bigid.com](mailto:mcp@bigid.com).

The plugin connects to the BigID MCP Server, which provides live API access to your BigID environment. Configure your BigID URL and credentials in the MCP server before installing the plugin.

### Available MCP Tools

BigID's capabilities are grouped into 19 tools. Each is marked `[READ]` or `[WRITE]` — `[WRITE]` tools can make changes as well as read.

| Tool | Access | Ask it about |
|---|---|---|
| [`catalog`](#catalog) | `[WRITE]` | which files/tables/objects contain X, show me this object |
| [`data_overview`](#data_overview) | `[READ]` | how many, break it down by, dashboards |
| [`data_security_posture`](#data_security_posture) | `[WRITE]` | what should we fix first, critical findings, security posture |
| [`data_access_intelligence`](#data_access_intelligence) | `[WRITE]` | who has access to X, over-permissioned users, external sharing |
| [`data_activity_monitoring`](#data_activity_monitoring) | `[WRITE]` | what happened to this file, alert timeline, AI/LLM activity |
| [`remediation`](#remediation) | `[WRITE]` | who fixes this, remediation progress, deadlines |
| [`data_deletion`](#data_deletion) | `[WRITE]` | delete this data, deletion queue, minimization |
| [`data_retention`](#data_retention) | `[WRITE]` | what is past its retention period, disposition |
| [`results_review_refine`](#results_review_refine) | `[WRITE]` | too many false positives, review progress |
| [`classification_management`](#classification_management) | `[WRITE]` | classifiers, detection rules, exclusion lists |
| [`data_discovery_management`](#data_discovery_management) | `[WRITE]` | is the scan done, scan this source, how much did we scan |
| [`data_source_connectivity`](#data_source_connectivity) | `[WRITE]` | what are we connected to, onboard a source |
| [`policy_management`](#policy_management) | `[WRITE]` | what policies do we have, enable a framework |
| [`risk_controls_management`](#risk_controls_management) | `[WRITE]` | privacy risk posture, risk case triage, mitigation |
| [`privacy_assessment_management`](#privacy_assessment_management) | `[WRITE]` | PIA, DPIA, RoPA, records of processing |
| [`dsar_case_management`](#dsar_case_management) | `[WRITE]` | what data do we hold on this person, request status |
| [`assets_management`](#assets_management) | `[WRITE]` | which applications do we have |
| [`audit_compliance_logs`](#audit_compliance_logs) | `[READ]` | who changed this in BigID, audit evidence |
| [`system_administration`](#system_administration) | `[WRITE]` | how do I…, users, roles, access |

Three supporting tools back the rest:

| Tool | Access | Use it for |
|---|---|---|
| `get_tool_schema` | `[READ]` | Showing what information a particular operation needs before it runs |
| `get_tpa_ids` | `[READ]` | Identifying the add-on applications installed in your environment — needed by the tools that sit on top of them, such as Data Retention, Remediation and the assessment tools |
| `read_large_response` | `[READ]` | Retrieving a result that was too large to return in one piece, a section at a time |

### Tool reference

#### `catalog`

`[WRITE]` — The inventory of everything BigID has scanned: every file, table, model and dataset, along with the sensitive data found inside it, who owns it, how it is tagged, which policies apply to it, and whether it is openly accessible. Search and filter that inventory, narrow it down in plain language, open a single object to see its columns and what was found in each one, export the results, and add or remove tags. Reach for this whenever the question is which files or tables contain something, or what exactly is inside a particular one. For totals and breakdowns rather than the objects themselves, `data_overview` is faster.

#### `data_overview`

`[READ]` — Counts and breakdowns across the whole estate rather than individual objects: how much data you have, where it lives, how sensitive it is, what format it is in, and how it is tagged. Also covers the health and freshness of the search behind it. Start here for "how many" and "break it down by" questions and for dashboards, then move to `catalog` when you need the actual objects behind a number.

#### `data_security_posture`

`[WRITE]` — The security findings BigID raises when data is exposed: open access, credentials and secrets left in the open, sensitive data somewhere it should not be. Browse and filter those cases, see how they break down by severity or by the policy that raised them, and pull the most critical open ones for a dashboard. You can also work them — change a case's status, hand it to someone, or apply the same change to a whole batch at once. Privacy risk cases live in `risk_controls_management`, and the workflow for actually fixing findings is in `remediation`.

#### `data_access_intelligence`

`[WRITE]` — Who can reach what. Users and groups with the access they hold, the permissions on an individual file, group membership, and what has been shared internally or externally, plus insights that surface the most over-shared people and groups. It also covers sensitivity labeling: the label providers you have connected, the sensitivity levels in use, how much of the estate is labeled, and starting or pausing the labeling process. Reach for this for "who has access to this", over-permissioned accounts, external sharing risk, and labeling coverage.

#### `data_activity_monitoring`

`[WRITE]` — What people and AI tools are actually doing with your data, and the alerts raised when that activity breaks a rule. Look at activity across the estate or the full history of a single file, see who did what and when, and count activity over a period. For an alert you get the timeline of events behind it, the objects it touched, who things were shared with, and — for AI alerts — the sessions involved and the kinds of violation found. You can also move alerts through triage and manage which data sources are being watched. For changes made inside BigID itself, use `audit_compliance_logs`.

#### `remediation`

`[WRITE]` — The workflow for getting findings fixed by the people who own the data. See the objects that need attention along with their owner, what was found in them, and any ticket already raised; see each data source's open and resolved counts and its deadline; and leave comments so the discussion stays with the finding. It also covers the setup behind the workflow: which actions are offered — move a file, revoke access, delete it, raise a ticket, mark a false positive, request an exception — which of those run automatically, the deadlines that apply per policy, and keeping all of it in step with the rest of BigID. Triage the underlying findings in `data_security_posture`; delete data in `data_deletion`.

#### `data_deletion`

`[WRITE]` — The queue of data slated for deletion, and the act of deleting it. See what is queued, what is finished and what failed, which requests it came from, and which data sources can be cleaned up automatically. You decide what happens to each object — delete it automatically, delete it by hand, keep it, or strip the sensitive values out of it — and then run the deletion. **Destructive:** deleting is permanent and cannot be undone, so always check how many objects will be affected and confirm before running it.

#### `data_retention`

`[WRITE]` — The rules for how long data should be kept, and finding the data that has outlived them. Covers the retention policies themselves and the different ways of describing what each one applies to, the data they have flagged, and the disposition work that follows. You can run a policy to see what it catches, try a definition out before committing to it, put evaluations on a schedule, and import or export policies in bulk. Use this for "what is past its retention period". Compliance and security rules live in `policy_management`, and actually removing the data happens in `data_deletion`.

#### `results_review_refine`

`[WRITE]` — Checking BigID's findings and telling it which ones are right. Work through what the classifiers found, see sample values for context, and mark each as correct or a false positive, then track how much of the review is done — broken down by the type of data, the field, or the data source. Reach for this when there are too many false positives, or when you want to confirm that classification is producing the right answers. To change the rule rather than judge its output, use `classification_management`.

#### `classification_management`

`[WRITE]` — The rules BigID uses to recognise sensitive data. See the classifiers in use, create your own — matching patterns, lists of terms, named entities, machine-learning models, or lookups against known records — and update or copy an existing one. It also covers exclusion lists, so values you know are false matches stop being reported. To judge the findings a classifier produced, use `results_review_refine`; to see where the data it found lives, use `catalog`.

#### `data_discovery_management`

`[WRITE]` — Scanning. Start a scan, pause, resume or cancel one, and follow its progress along with everything it covered and found. It also covers the reusable scan setups and templates that decide what gets scanned and how, and statistics on how much was scanned over a given period, by data source or by kind of connector. Use this for "is the scan finished", "scan this source" and "how much did we scan". What the scans found lives in `catalog` and `results_review_refine`.

#### `data_source_connectivity`

`[WRITE]` — The data sources BigID is connected to. Browse and filter the inventory, see every kind of system BigID can connect to and what each one needs in order to connect, add a new source, and update details across many sources at once, including your own custom fields. Reach for this for "what are we connected to" and for onboarding a new system. What was found inside those sources is in `catalog`; scanning them is in `data_discovery_management`.

#### `policy_management`

`[WRITE]` — The rules themselves, rather than what they catch. Covers compliance policies — browse them, create and update them, and test one to see whether it is being broken — along with compliance frameworks and their controls, which you can switch on, extend with your own, or map policies onto. It also covers regulations and the rules behind access-related alerting. The findings a security policy raises are in `data_security_posture`, and retention rules are in `data_retention`.

#### `risk_controls_management`

`[WRITE]` — Privacy risk: the library of risks you track, the controls that address them, and the open cases against them. Browse and group cases by asset, owner, vendor or the assessment they came from, open one to see the full picture and its history, and raise new ones. Each case can carry mitigation work — tasks with an owner and a due date that you move along as they get done. Security findings are in `data_security_posture`; risks raised while filling in an assessment are in `privacy_assessment_management`.

#### `privacy_assessment_management`

`[WRITE]` — Privacy assessments and records of processing, and the largest area of the server. Build and manage the questionnaires behind them, then run the assessments themselves: fill them in, collaborate and comment with colleagues, assign owners, get suggested answers drawn from similar past assessments, submit for review, complete them, and export or import in bulk — with reporting on progress, timeliness and risk along the way. Records of processing additionally cover data flow diagrams. It also reads the things assessments refer to — applications, data sources, legal entities and vendors — and covers the profiles that define where to look for a person's data.

#### `dsar_case_management`

`[WRITE]` — Requests from individuals about their own data. Raise a request, follow the search across your systems, and get back what was found, either as a full report, a summary, or the personal details on their own — and download any of it to share. It also covers the reusable request setups and report templates, the kinds of personal data that can be searched for, and the checks that confirm a deletion actually happened. Removing the data itself runs through `data_deletion`.

#### `assets_management`

`[WRITE]` — The register of business applications: the systems and tools your organisation uses, as opposed to the data sources BigID connects to. List them, look one up, see which assessments and business processes reference it, and add or update an entry. Data source connections are in `data_source_connectivity`, and the assessments themselves are in `privacy_assessment_management`.

#### `audit_compliance_logs`

`[READ]` — A record of what people have done inside BigID: who changed, deleted or exported something, and when. Filter it by time, person and kind of action. Intended for audit evidence and change history. For what people are doing with the data itself rather than with BigID, use `data_activity_monitoring`; for scan history, use `data_discovery_management`.

#### `system_administration`

`[WRITE]` — Running BigID itself: the people with access, their roles and what those roles can see, saved searches, and the platform's own configuration. It also includes BigChat, an assistant that answers from BigID's official documentation — worth reaching for first whenever the question is how something works or how to do it, since the answer usually shapes which of the other tools you need.

### Picking the right tool

A few pairs are easy to confuse:

- **Rule vs. finding** — `policy_management` defines policies; `data_security_posture` holds the cases they raise; `remediation` is the workflow to fix them; `data_deletion` actually deletes.
- **Object vs. aggregate** — `catalog` returns objects, `data_overview` returns counts.
- **Classifier vs. its output** — `classification_management` edits the rule, `results_review_refine` judges the findings.
- **Two kinds of case** — security cases are in `data_security_posture`, privacy risk cases in `risk_controls_management`.
- **Two kinds of log** — what people did inside BigID is in `audit_compliance_logs`, what they did with the data in `data_activity_monitoring`.

## Available Skills

| Skill | Triggers | Description |
|---|---|---|
| `/bigid:bigid-security-posture` | security posture, DSPM, security cases, exposed credentials, top cases, what should I fix first | DSPM triage — ranks credential-exposure and policy cases by risk, drives remediation |
| `/bigid:bigid-regulations-and-frameworks` | compliance report, GDPR, HIPAA, EO 14117, OSFI B-13, prove compliance, audit evidence, check us against [regulation] | Generates a regulation-specific compliance evidence PDF from live BigID data — supports named regulations, laws, executive orders, and custom uploaded policies |
| `/bigid:bigid-shadowai-and-ai-risk` | AI risk, Shadow AI, AI posture, ungoverned AI, LLM data exposure, vector store, ChatGPT, OpenAI, Hugging Face | Triages DSPM cases scoped to AI risk and Shadow AI — surfaces credentials and regulated data inside AI platforms and vector stores |
| `/bigid:bigid-access-graph` | who can access X, what can user Y reach, show me the access graph, map permissions, over-permissioned users, external sharing risk, access investigation, identities, entitlements, RBAC | Builds an interactive access graph from BigID ACI data — visualizes relationships between users, groups, permissions, and data resources |
| `/bigid:bigid-create-assessment-template` | PIA template, custom template, privacy impact assessment, convert questionnaire, import template from Word/Excel/PDF, build PIA template | Turns a source document (Word/Excel/PDF) or interview into a new BigID PIA custom template — parses fields, resolves types, previews with user, and creates via BigID |
| `/bigid:bigid-create-jira-tickets-for-policy-violations` | ticket BigID findings, file risk cases in Jira, open tickets for policy, track BigID cases, Jira ticket per data source, Action Center to Jira | Pulls open risk cases for a BigID policy and files one Jira ticket per data source — follows a confirmation loop to prevent misfiled batches |

## Installation

### Claude Code

```bash
claude plugin install git@gitlab.com:bigid/agentic-ai/skills.git
```

### Claude Desktop

1. Open Claude Desktop → Settings → Plugins
2. Click **Add Plugin** and upload the plugin folder, or paste the repository URL
3. Restart Claude Desktop — skills activate automatically

### OpenAI Codex

1. In your Codex environment, open the plugins or extensions settings
2. Add a new plugin and point it to this repository (or the `.codex-plugin/plugin.json` manifest directly)
3. Configure your BigID MCP server URL and credentials when prompted
