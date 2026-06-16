# BigID Plugin

The BigID Plugin connects your AI agent directly to your BigID environment. Discover and inventory data sources, run and customize scan workflows, and explore your unified data catalog — all in natural language. Get full visibility into your data security posture across DSPM, access governance, privacy, and labeling. Manage regulatory risk, automate compliance assessments, and detect policy violations in real time. Take immediate remediation action: reduce access, delete or clean sensitive data, and enforce controls — end-to-end data and AI protection in one connector.

## Skills

Skills are context-aware instruction sets that activate automatically when relevant. When you ask about PII exposure, policy violations, security cases, or privacy compliance, the right skill kicks in — no slash commands needed. Each skill knows which BigID APIs to call, how to interpret the results, and what remediation actions are available.

## MCP Server

The plugin connects to the BigID MCP Server, which provides live API access to your BigID environment. Configure your BigID URL and credentials in the MCP server before installing the plugin.

## Available Skills

| Skill | Triggers | Description |
|---|---|---|
| `/bigid:bigid-know-your-data` | BigID, data governance, PII, violations, KYD | Know Your Data expert — inventory, catalog, remediation |
| `/bigid:bigid-security-posture` | security posture, DSPM, security cases, exposed credentials, top cases | DSPM triage — ranks security cases by risk, drives remediation |
| `/bigid:bigid-privacy-posture` | privacy posture, NIST-P, compliance report, privacy risk, posture deck | Generates a NIST Privacy Framework compliance report from live BigID data |
| `/bigid:bigid-compliance-report` | compliance report, GDPR, HIPAA, EO 14117, OSFI, prove compliance, audit evidence | Generates a regulation-specific compliance evidence PDF from live BigID data |

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
