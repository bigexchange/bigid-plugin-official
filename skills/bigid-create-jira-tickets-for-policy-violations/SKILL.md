---
name: bigid-create-jira-tickets-for-policy-violations
description: Turn BigID Security Posture risk cases for a given policy into Jira tickets, one ticket per data source. Use this whenever the user wants to "ticket," "file," or "track" BigID findings, mentions a BigID policy or risk case (e.g. "Personal Financial Information with High Sensitivity", "Open Access ... detected on ...") together with Jira, asks for a ticket per data source, or wants BigID's Action Center output turned into real Jira issues. Trigger even if they only say something like "open tickets for the [policy name] cases" or "file these risk cases in Jira" without spelling out the full workflow.
---

# BigID Security Posture → Jira tickets

This skill pulls the open risk cases for one BigID policy, shows them grouped by data source (each case already *is* one data source), and then files one Jira ticket per case. It follows a proven interview loop — don't skip the confirmation steps, since a wrong policy match or wrong project turns into a batch of wrong tickets.

## Step 1 — Get the policy

If the user hasn't already named an exact policy, ask which one they mean. If they give something fuzzy or partial, do a "contains" search first (see Step 2's filter, but with `operator: contains`) to find candidate policy names, show them to the user, and get them to confirm the exact one before moving on. BigID often has several sibling policies whose names overlap (e.g. a plain policy plus "Open Access <policy>" and "External Access <policy>" variants) — these are different policies with different cases, not the same one.

## Step 2 — Pull the open cases for that policy

Find the BigID connector's generic read tool — its name embeds a connector-specific id that varies by environment, so search for it rather than assuming the exact string:

```
ToolSearch query: "get_objects BigID API"
```

Call it with:
- `server_name`: `"Security Posture"`
- `tool_name`: `"get_actionable_insights_all_cases"`
- `arguments.filter`: `[{"field":"policyName","value":"<exact policy name>","operator":"equals"},{"field":"caseStatus","value":"open","operator":"equals"}]`
- `arguments.limit`: `100` (bump it if the response indicates more)

Two lessons baked into that filter:

- **Use `equals`, not `contains`, on `policyName`.** A `contains` match silently pulls in sibling policies too and over-counts the cases — this happened the first time this workflow was run.
- **Filter to `caseStatus: open`.** Each case corresponds to exactly one data source. Cases that are already remediated report 0 remaining affected objects and don't need a ticket — mention them exist, but leave them out of the ticket batch.

Each returned case already has everything needed for the "per data source" view: `caseId`, `dataSourceName`, `dataSourceDisplayName` (the source type, e.g. "Amazon S3"), `severityLevel`, `numberOfAffectedObjects`. That *is* the grouping — there's no need to separately query the Data Catalog for individual object names/files unless the user explicitly asks for object-level detail. Going a level deeper than the case list is a much bigger, noisier pull and is usually not what's wanted here.

## Step 3 — Show the list and confirm before doing anything else

Present a table: Case ID | Data Source | Source Type | Severity | Affected Objects (sorted by affected objects descending, unless the user wants a different order). Confirm this is the right set before creating tickets — the number of rows becomes the number of tickets.

## Step 4 — Pick the Jira destination

Find the Jira/Atlassian connector's tools the same way (search, don't assume the exact registered name):

```
ToolSearch query: "createJiraIssue getVisibleJiraProjects lookupJiraAccountId Jira"
```

Get a `cloudId` via `getAccessibleAtlassianResources` (or try the site hostname directly, per that tool's own hint). Ask the user which Jira project the tickets should go into. If they don't already know the project key, call `getVisibleJiraProjects` with a `searchString` to narrow it down — its unfiltered output is large enough to blow past context limits, so don't call it with no filter.

Once you have the project, call `getJiraProjectIssueTypesMetadata` to see what issue types it actually supports, and default to `Task` if available. Not every project has a `Task` type — fall back to whatever else looks like a generic work item (`Story`, `Bug`, etc.) if it doesn't.

## Step 5 — Get an assignee per data source

For each distinct data source in the case list, ask who it should be assigned to. `AskUserQuestion` allows up to 4 questions per call, so batch them in groups of 4 and run multiple rounds if there are more than 4 data sources. Accept an email or name, then resolve it to a Jira account id with `lookupJiraAccountId` — `createJiraIssue` needs `assignee_account_id`, not a raw email or name. If a lookup comes back empty, tell the user and ask for another identifier rather than quietly leaving that ticket unassigned.

## Step 6 — Create one ticket per case

For each case, call `createJiraIssue` with:
- `cloudId`, `projectKey`, `issueTypeName` (from Step 4)
- `summary`: `[Security Posture] <policy name> - <source type> (<data source name>)`
- `description`: case id, policy name, severity, data source, affected object count, status, and a one-line reminder of what the policy actually flags (pull this from the case's `policyDescription` field if present)
- `assignee_account_id`: resolved in Step 5 for that case's data source

These calls don't depend on each other, so fire them as one batch of tool calls rather than one at a time.

## Step 7 — Report back

Give the user a table: Case ID | Data Source | Ticket (key + link). Call out any cases you left out because they were already remediated, and any assignee lookups that failed and need a different identifier.

## Notes and gotchas

- **Don't over-fetch.** Pulling individual Data Catalog objects for a policy can return hundreds of rows and exceed output size limits. Stay at the case level unless the user explicitly wants object/file-level detail.
- **If a read call errors with something like "result exceeds maximum tokens,"** don't retry with the same shape. Cut the requested fields down to the minimum needed, lower the `limit`, or hand the saved raw-output file to a subagent to parse instead of reading it directly.
- **BigID's own Action Center also offers a per-case "create Jira ticket" action** (tool name pattern like `post_actionable_insights_cases_\::actionType_by_caseid`, called with `type: "jira", subType: "createTicket"`). In this environment it has consistently returned `502` errors regardless of case or payload shape, so this skill goes straight to the Jira/Atlassian connector instead. If that Action Center integration ever starts working, tickets created through it link back to the BigID case automatically, which the direct-connector path doesn't do — worth revisiting if BigID's Jira integration gets fixed on the backend.
