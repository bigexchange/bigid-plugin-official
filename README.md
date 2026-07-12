# BigID Plugin

The BigID Plugin connects your AI agent directly to your BigID environment. Get full visibility into your data security posture across DSPM, privacy, and compliance — all in natural language. Manage regulatory risk, automate compliance assessments, and detect policy violations in real time.

## Skills

Skills are context-aware instruction sets that activate automatically when relevant. When you ask about security cases, compliance evidence, or AI risk, the right skill kicks in — no slash commands needed. Each skill knows which BigID APIs to call, how to interpret the results, and what remediation actions are available.

## MCP Server

> **Early Adopters Program**
> The BigID MCP Server is currently available as part of an Early Adopters Program. To join the program and get access, contact BigID support or reach out at [mcp@bigid.com](mailto:mcp@bigid.com).

The plugin connects to the BigID MCP Server, which provides live API access to your BigID environment. Configure your BigID URL and credentials in the MCP server before installing the plugin.

## Available Skills

| Skill | Triggers | Description |
|---|---|---|
| `/bigid:bigid-security-posture` | security posture, DSPM, security cases, exposed credentials, top cases, what should I fix first | DSPM triage — ranks credential-exposure and policy cases by risk, drives remediation |
| `/bigid:bigid-regulations-and-frameworks` | compliance report, GDPR, HIPAA, EO 14117, OSFI B-13, prove compliance, audit evidence, check us against [regulation] | Generates a regulation-specific compliance evidence PDF from live BigID data — supports named regulations, laws, executive orders, and custom uploaded policies |
| `/bigid:bigid-shadowai-and-ai-risk` | AI risk, Shadow AI, AI posture, ungoverned AI, LLM data exposure, vector store, ChatGPT, OpenAI, Hugging Face | Triages DSPM cases scoped to AI risk and Shadow AI — surfaces credentials and regulated data inside AI platforms and vector stores |

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
