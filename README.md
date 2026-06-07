# BigID Skills

AI skills for BigID — reusable instruction sets for Claude Code and compatible AI agents.

## Installation

```bash
claude plugin install git@gitlab.com:bigid/agentic-ai/skills.git
```

## Available Skills

| Skill                         | Trigger | Description |
|-------------------------------|---|---|
| `/bigid:bigid-know-your-data` | BigID, data governance, PII, violations, KYD | Know Your Data expert — inventory, catalog, remediation |
## Using Skills with the BigID MCP Server

These skills work with the [BigID MCP Server](https://github.com/bigid/mcp-server), which provides live API access to your BigID environment.

**Setup:**
1. Install the BigID MCP server and configure your BigID URL + credentials
2. Install this plugin: `claude plugin install git@github.com:bigid/skills.git`
3. Skills will automatically use MCP tools when available

## Contributing

Skills are authored and managed via the [AI Backoffice](https://gitlab.com/bigid/agentic-ai/ai-backoffice).

To add a new skill:
1. Create `skills/{skill-name}/SKILL.md` following the format below
2. Open a PR — skills are reviewed before merging

### Skill Format

```markdown
---
name: skill-name
description: >
  What this skill does. Be specific about trigger conditions —
  Claude uses this description to decide when to activate the skill automatically.
---

# Skill Title

[Instruction body — what Claude should do, how to behave, which APIs to call]
```

**Name:** lowercase, hyphens only, max 64 chars
**Description:** max 1024 chars — include trigger keywords so Claude activates the skill automatically