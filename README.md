# BigID Plugin for Claude Code

Official BigID plugin for [Claude Code](https://claude.ai/code), built on the [Agent Skills](https://agentskills.io) standard.

Connects your BigID environment to Claude Code via the BigID MCP server, and ships a set of skills that give Claude deep domain knowledge for data governance, privacy, security, and compliance workflows.

---

## Installation

Add this plugin to your Claude Code session:

```
/plugins add https://github.com/bigexchange/bigid-plugin-official
```

This registers the BigID MCP server and loads all available skills automatically.

---

## Available Skills

### `bigid-demo` — Product Demo

Showcases BigID capabilities using safe, fictional sample data. No real PII or sensitive assets involved. Suitable for onboarding, public demos, and exploring BigID features without a live environment.

**Trigger examples:**
- "Show me a BigID demo"
- "What can BigID do?"
- "Walk me through a data discovery workflow"

### `bigid-hello-world` — Hello World

Minimal skill to verify the plugin is installed and skills are loading correctly.

**Trigger:**
- "Run a hello world"

---

## How It Works

This plugin follows the [Agent Skills](https://agentskills.io) format — each skill is a folder containing a `SKILL.md` file with metadata and instructions. Skills use progressive disclosure:

1. **Discovery** — Claude loads only the skill name and description at startup
2. **Activation** — Full instructions load when a user message matches the skill's purpose
3. **Execution** — Claude follows the skill instructions, calling BigID MCP tools as needed

---

## MCP Server

All BigID API calls are proxied through the BigID MCP server:

```
https://bigid-mcp.bigid.cloud
```

Authentication is handled by your BigID session token configured in Claude Code settings.

---

## License

Proprietary — © BigID Inc.
