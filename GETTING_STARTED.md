# Getting Started

## How Skills Work Across Surfaces

The same `SKILL.md` format works everywhere. Skills activate **automatically and associatively** — Claude reads the `description` field and activates the skill when the conversation matches, no manual invocation needed.

| Surface | Delivery | Auto-triggers? | Auto-updates? |
|---|---|---|---|
| Claude Code | Install plugin from this repo | Yes | On `claude plugin update` |
| Claude Desktop (org members) | Org owner uploads to Organization Settings | Yes | Yes — instant on new version |
| Claude Desktop (external customers) | Marketplace plugin install | Yes | Yes — on repo change |

---

## Claude Code

### Prerequisites

- [Claude Code](https://claude.ai/code) installed
- [BigID MCP Server](https://gitlab.com/bigid/agentic-ai/mcp-server) configured with your BigID URL and credentials

### Install the Plugin

```bash
claude plugin install git@gitlab.com:bigid/agentic-ai/skills.git
```

Skills are namespaced under `bigid`. Use `/bigid:bigid-know-your-data` or just ask anything BigID-related — Claude activates the skill automatically.

---

## Claude Desktop — Organization Members

Organization owners provision skills once. All org members see them instantly under **Customize → Skills → Organization skills**, with the same associative activation as Claude Code.

### Option A — Upload via UI

**Organization Settings → Skills → + Add** → upload a `.zip` of the skill directory.

### Option B — Upload via API

```bash
curl https://api.anthropic.com/v1/skills \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -F "display_title=BigID KNOW YOUR DATA" \
  -F "files=@bigid-know-your-data.zip"
```

To update: `POST /v1/skills/{skill_id}/versions` — users receive the update instantly, no action needed.

### Prerequisites (org owner must enable once)

Organization Settings → Capabilities → enable **Code execution**
Organization Settings → Skills → enable **File creation**

### Individual users

Users can toggle org skills on/off from **Customize → Skills**, but cannot delete them. The BigID MCP server must be connected for skills to make API calls — add it once via **Settings → Connectors → + → Add custom connector**.

---

## Claude Desktop — External Customers (future)

Once the plugin is listed in the Claude marketplace, customers install once:

```bash
claude plugin install bigid@claude-community
```

The plugin auto-configures the MCP server connection. Skills activate associatively and update automatically when the repo changes.

---

## Write a New Skill

1. Create a folder under `skills/`:
   ```
   skills/your-skill-name/SKILL.md
   ```

2. Add frontmatter and instruction body:
   ```markdown
   ---
   name: your-skill-name
   description: >
     What this skill does. Include trigger keywords so Claude activates
     it automatically (e.g. "data sources", "scan", "PII").
   ---

   # Your Skill Title

   [Instructions for Claude — what to do, how to behave, which MCP tools to call]
   ```

3. For Claude Code: `/reload-plugins`
4. For Claude Desktop: re-upload zip or post a new version via API

### Contribute

Open a PR. Skills are reviewed before merging.

---

## Making It Public

**Phase 1 — Internal org (now)**
Upload skills to Organization Settings. All BigID employees on Claude Desktop get them immediately.

**Phase 2 — Make the repo public**
GitLab → Settings → General → Visibility → Public. Before flipping:
- Ensure no credentials or internal URLs exist in skill files
- Update the MCP server URL in `.claude-plugin/plugin.json` from the internal CI endpoint (`bigid-mcp.ci.bigid-integrations.net`) to the production public URL

**Phase 3 — (Optional) Move to top-level BigID org**
Transfer to `bigid/skills`. GitLab redirects the old path automatically.

**Phase 4 — List in the Claude community marketplace**
Submit a PR to `anthropics/claude-plugins-community` on GitHub. After safety review, external users can discover and install the plugin. Marketplace plugins auto-update when the repo changes.

**Phase 5 — (Optional) Apply to the Claude Partner Network**
For an official Anthropic verified badge and enterprise co-marketing, apply through the [Claude Partner Network](https://anthropic.skilljar.com/page/claude-partner-network-learning-path).
