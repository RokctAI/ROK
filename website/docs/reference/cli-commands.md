---
sidebar_position: 1
title: "CLI Commands Reference"
description: "Authoritative reference for Rok terminal commands and command families"
---

# CLI Commands Reference

This page covers the **terminal commands** you run from your shell.

For in-chat slash commands, see [Slash Commands Reference](./slash-commands.md).

## Global entrypoint

```bash
rok [global-options] <command> [subcommand/options]
```

### Global options

| Option | Description |
|--------|-------------|
| `--version`, `-V` | Show version and exit. |
| `--profile <name>`, `-p <name>` | Select which Rok profile to use for this invocation. Overrides the sticky default set by `rok profile use`. |
| `--resume <session>`, `-r <session>` | Resume a previous session by ID or title. |
| `--continue [name]`, `-c [name]` | Resume the most recent session, or the most recent session matching a title. |
| `--worktree`, `-w` | Start in an isolated git worktree for parallel-agent workflows. |
| `--yolo` | Bypass dangerous-command approval prompts. |
| `--pass-session-id` | Include the session ID in the agent's system prompt. |

## Top-level commands

| Command | Purpose |
|---------|---------|
| `rok chat` | Interactive or one-shot chat with the agent. |
| `rok model` | Interactively choose the default provider and model. |
| `rok gateway` | Run or manage the messaging gateway service. |
| `rok setup` | Interactive setup wizard for all or part of the configuration. |
| `rok whatsapp` | Configure and pair the WhatsApp bridge. |
| `rok login` / `logout` | Authenticate with OAuth-backed providers. |
| `rok auth` | Manage credential pools — add, list, remove, reset, set strategy. |
| `rok status` | Show agent, auth, and platform status. |
| `rok cron` | Inspect and tick the cron scheduler. |
| `rok webhook` | Manage dynamic webhook subscriptions for event-driven activation. |
| `rok doctor` | Diagnose config and dependency issues. |
| `rok config` | Show, edit, migrate, and query configuration files. |
| `rok pairing` | Approve or revoke messaging pairing codes. |
| `rok skills` | Browse, install, publish, audit, and configure skills. |
| `rok honcho` | Manage Honcho cross-session memory integration. |
| `rok acp` | Run Rok as an ACP server for editor integration. |
| `rok mcp` | Manage MCP server configurations and run Rok as an MCP server. |
| `rok plugins` | Manage Rok Agent plugins (install, enable, disable, remove). |
| `rok tools` | Configure enabled tools per platform. |
| `rok sessions` | Browse, export, prune, rename, and delete sessions. |
| `rok insights` | Show token/cost/activity analytics. |
| `rok claw` | OpenClaw migration helpers. |
| `rok profile` | Manage profiles — multiple isolated Rok instances. |
| `rok completion` | Print shell completion scripts (bash/zsh). |
| `rok version` | Show version information. |
| `rok update` | Pull latest code and reinstall dependencies. |
| `rok uninstall` | Remove Rok from the system. |

## `rok chat`

```bash
rok chat [options]
```

Common options:

| Option | Description |
|--------|-------------|
| `-q`, `--query "..."` | One-shot, non-interactive prompt. |
| `-m`, `--model <model>` | Override the model for this run. |
| `-t`, `--toolsets <csv>` | Enable a comma-separated set of toolsets. |
| `--provider <provider>` | Force a provider: `auto`, `openrouter`, `nous`, `openai-codex`, `copilot-acp`, `copilot`, `anthropic`, `huggingface`, `zai`, `kimi-coding`, `minimax`, `minimax-cn`, `kilocode`. |
| `-s`, `--skills <name>` | Preload one or more skills for the session (can be repeated or comma-separated). |
| `-v`, `--verbose` | Verbose output. |
| `-Q`, `--quiet` | Programmatic mode: suppress banner/spinner/tool previews. |
| `--resume <session>` / `--continue [name]` | Resume a session directly from `chat`. |
| `--worktree` | Create an isolated git worktree for this run. |
| `--checkpoints` | Enable filesystem checkpoints before destructive file changes. |
| `--yolo` | Skip approval prompts. |
| `--pass-session-id` | Pass the session ID into the system prompt. |
| `--source <tag>` | Session source tag for filtering (default: `cli`). Use `tool` for third-party integrations that should not appear in user session lists. |

Examples:

```bash
rok
rok chat -q "Summarize the latest PRs"
rok chat --provider openrouter --model anthropic/claude-sonnet-4.6
rok chat --toolsets web,terminal,skills
rok chat --quiet -q "Return only JSON"
rok chat --worktree -q "Review this repo and open a PR"
```

## `rok model`

Interactive provider + model selector.

```bash
rok model
```

Use this when you want to:
- switch default providers
- log into OAuth-backed providers during model selection
- pick from provider-specific model lists
- configure a custom/self-hosted endpoint
- save the new default into config

### `/model` slash command (mid-session)

Switch models without leaving a session:

```
/model                              # Show current model and available options
/model claude-sonnet-4              # Switch model (auto-detects provider)
/model zai:glm-5                    # Switch provider and model
/model custom:qwen-2.5              # Use model on your custom endpoint
/model custom                       # Auto-detect model from custom endpoint
/model custom:local:qwen-2.5        # Use a named custom provider
/model openrouter:anthropic/claude-sonnet-4  # Switch back to cloud
```

Provider and base URL changes are persisted to `config.yaml` automatically. When switching away from a custom endpoint, the stale base URL is cleared to prevent it leaking into other providers.

## `rok gateway`

```bash
rok gateway <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `run` | Run the gateway in the foreground. |
| `start` | Start the installed gateway service. |
| `stop` | Stop the service. |
| `restart` | Restart the service. |
| `status` | Show service status. |
| `install` | Install as a user service (`systemd` on Linux, `launchd` on macOS). |
| `uninstall` | Remove the installed service. |
| `setup` | Interactive messaging-platform setup. |

## `rok setup`

```bash
rok setup [model|terminal|gateway|tools|agent] [--non-interactive] [--reset]
```

Use the full wizard or jump into one section:

| Section | Description |
|---------|-------------|
| `model` | Provider and model setup. |
| `terminal` | Terminal backend and sandbox setup. |
| `gateway` | Messaging platform setup. |
| `tools` | Enable/disable tools per platform. |
| `agent` | Agent behavior settings. |

Options:

| Option | Description |
|--------|-------------|
| `--non-interactive` | Use defaults / environment values without prompts. |
| `--reset` | Reset configuration to defaults before setup. |

## `rok whatsapp`

```bash
rok whatsapp
```

Runs the WhatsApp pairing/setup flow, including mode selection and QR-code pairing.

## `rok login` / `rok logout`

```bash
rok login [--provider nous|openai-codex] [--portal-url ...] [--inference-url ...]
rok logout [--provider nous|openai-codex]
```

`login` supports:
- Nous Portal OAuth/device flow
- OpenAI Codex OAuth/device flow

Useful options for `login`:
- `--no-browser`
- `--timeout <seconds>`
- `--ca-bundle <pem>`
- `--insecure`

## `rok auth`

Manage credential pools for same-provider key rotation. See [Credential Pools](/docs/user-guide/features/credential-pools) for full documentation.

```bash
rok auth                                              # Interactive wizard
rok auth list                                         # Show all pools
rok auth list openrouter                              # Show specific provider
rok auth add openrouter --api-key sk-or-v1-xxx        # Add API key
rok auth add anthropic --type oauth                   # Add OAuth credential
rok auth remove openrouter 2                          # Remove by index
rok auth reset openrouter                             # Clear cooldowns
```

Subcommands: `add`, `list`, `remove`, `reset`. When called with no subcommand, launches the interactive management wizard.

## `rok status`

```bash
rok status [--all] [--deep]
```

| Option | Description |
|--------|-------------|
| `--all` | Show all details in a shareable redacted format. |
| `--deep` | Run deeper checks that may take longer. |

## `rok cron`

```bash
rok cron <list|create|edit|pause|resume|run|remove|status|tick>
```

| Subcommand | Description |
|------------|-------------|
| `list` | Show scheduled jobs. |
| `create` / `add` | Create a scheduled job from a prompt, optionally attaching one or more skills via repeated `--skill`. |
| `edit` | Update a job's schedule, prompt, name, delivery, repeat count, or attached skills. Supports `--clear-skills`, `--add-skill`, and `--remove-skill`. |
| `pause` | Pause a job without deleting it. |
| `resume` | Resume a paused job and compute its next future run. |
| `run` | Trigger a job on the next scheduler tick. |
| `remove` | Delete a scheduled job. |
| `status` | Check whether the cron scheduler is running. |
| `tick` | Run due jobs once and exit. |

## `rok webhook`

```bash
rok webhook <subscribe|list|remove|test>
```

Manage dynamic webhook subscriptions for event-driven agent activation. Requires the webhook platform to be enabled in config — if not configured, prints setup instructions.

| Subcommand | Description |
|------------|-------------|
| `subscribe` / `add` | Create a webhook route. Returns the URL and HMAC secret to configure on your service. |
| `list` / `ls` | Show all agent-created subscriptions. |
| `remove` / `rm` | Delete a dynamic subscription. Static routes from config.yaml are not affected. |
| `test` | Send a test POST to verify a subscription is working. |

### `rok webhook subscribe`

```bash
rok webhook subscribe <name> [options]
```

| Option | Description |
|--------|-------------|
| `--prompt` | Prompt template with `{dot.notation}` payload references. |
| `--events` | Comma-separated event types to accept (e.g. `issues,pull_request`). Empty = all. |
| `--description` | Human-readable description. |
| `--skills` | Comma-separated skill names to load for the agent run. |
| `--deliver` | Delivery target: `log` (default), `telegram`, `discord`, `slack`, `github_comment`. |
| `--deliver-chat-id` | Target chat/channel ID for cross-platform delivery. |
| `--secret` | Custom HMAC secret. Auto-generated if omitted. |

Subscriptions persist to `~/.rok/webhook_subscriptions.json` and are hot-reloaded by the webhook adapter without a gateway restart.

## `rok doctor`

```bash
rok doctor [--fix]
```

| Option | Description |
|--------|-------------|
| `--fix` | Attempt automatic repairs where possible. |

## `rok config`

```bash
rok config <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `show` | Show current config values. |
| `edit` | Open `config.yaml` in your editor. |
| `set <key> <value>` | Set a config value. |
| `path` | Print the config file path. |
| `env-path` | Print the `.env` file path. |
| `check` | Check for missing or stale config. |
| `migrate` | Add newly introduced options interactively. |

## `rok pairing`

```bash
rok pairing <list|approve|revoke|clear-pending>
```

| Subcommand | Description |
|------------|-------------|
| `list` | Show pending and approved users. |
| `approve <platform> <code>` | Approve a pairing code. |
| `revoke <platform> <user-id>` | Revoke a user's access. |
| `clear-pending` | Clear pending pairing codes. |

## `rok skills`

```bash
rok skills <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `browse` | Paginated browser for skill registries. |
| `search` | Search skill registries. |
| `install` | Install a skill. |
| `inspect` | Preview a skill without installing it. |
| `list` | List installed skills. |
| `check` | Check installed hub skills for upstream updates. |
| `update` | Reinstall hub skills with upstream changes when available. |
| `audit` | Re-scan installed hub skills. |
| `uninstall` | Remove a hub-installed skill. |
| `publish` | Publish a skill to a registry. |
| `snapshot` | Export/import skill configurations. |
| `tap` | Manage custom skill sources. |
| `config` | Interactive enable/disable configuration for skills by platform. |

Common examples:

```bash
rok skills browse
rok skills browse --source official
rok skills search react --source skills-sh
rok skills search https://mintlify.com/docs --source well-known
rok skills inspect official/security/1password
rok skills inspect skills-sh/vercel-labs/json-render/json-render-react
rok skills install official/migration/openclaw-migration
rok skills install skills-sh/anthropics/skills/pdf --force
rok skills check
rok skills update
rok skills config
```

Notes:
- `--force` can override non-dangerous policy blocks for third-party/community skills.
- `--force` does not override a `dangerous` scan verdict.
- `--source skills-sh` searches the public `skills.sh` directory.
- `--source well-known` lets you point Rok at a site exposing `/.well-known/skills/index.json`.

## `rok honcho`

```bash
rok honcho <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `setup` | Interactive Honcho setup wizard. |
| `status` | Show current Honcho config and connection status. |
| `sessions` | List known Honcho session mappings. |
| `map` | Map the current directory to a Honcho session name. |
| `peer` | Show or update peer names and dialectic reasoning level. |
| `mode` | Show or set memory mode: `hybrid`, `honcho`, or `local`. |
| `tokens` | Show or set token budgets for context and dialectic. |
| `identity` | Seed or show the AI peer identity representation. |
| `migrate` | Migration guide from openclaw-honcho to Rok Honcho. |

## `rok acp`

```bash
rok acp
```

Starts Rok as an ACP (Agent Client Protocol) stdio server for editor integration.

Related entrypoints:

```bash
rok-acp
python -m acp_adapter
```

Install support first:

```bash
pip install -e '.[acp]'
```

See [ACP Editor Integration](../user-guide/features/acp.md) and [ACP Internals](../developer-guide/acp-internals.md).

## `rok mcp`

```bash
rok mcp <subcommand>
```

Manage MCP (Model Context Protocol) server configurations and run Rok as an MCP server.

| Subcommand | Description |
|------------|-------------|
| `serve [-v\|--verbose]` | Run Rok as an MCP server — expose conversations to other agents. |
| `add <name> [--url URL] [--command CMD] [--args ...] [--auth oauth\|header]` | Add an MCP server with automatic tool discovery. |
| `remove <name>` (alias: `rm`) | Remove an MCP server from config. |
| `list` (alias: `ls`) | List configured MCP servers. |
| `test <name>` | Test connection to an MCP server. |
| `configure <name>` (alias: `config`) | Toggle tool selection for a server. |

See [MCP Config Reference](./mcp-config-reference.md), [Use MCP with Rok](../guides/use-mcp-with-rok.md), and [MCP Server Mode](../user-guide/features/mcp.md#running-rok-as-an-mcp-server).

## `rok plugins`

```bash
rok plugins [subcommand]
```

Manage Rok Agent plugins. Running `rok plugins` with no subcommand launches an interactive curses checklist to enable/disable installed plugins.

| Subcommand | Description |
|------------|-------------|
| *(none)* | Interactive toggle UI — enable/disable plugins with arrow keys and space. |
| `install <identifier> [--force]` | Install a plugin from a Git URL or `owner/repo`. |
| `update <name>` | Pull latest changes for an installed plugin. |
| `remove <name>` (aliases: `rm`, `uninstall`) | Remove an installed plugin. |
| `enable <name>` | Enable a disabled plugin. |
| `disable <name>` | Disable a plugin without removing it. |
| `list` (alias: `ls`) | List installed plugins with enabled/disabled status. |

Disabled plugins are stored in `config.yaml` under `plugins.disabled` and skipped during loading.

See [Plugins](../user-guide/features/plugins.md) and [Build a Rok Plugin](../guides/build-a-rok-plugin.md).

## `rok tools`

```bash
rok tools [--summary]
```

| Option | Description |
|--------|-------------|
| `--summary` | Print the current enabled-tools summary and exit. |

Without `--summary`, this launches the interactive per-platform tool configuration UI.

## `rok sessions`

```bash
rok sessions <subcommand>
```

Subcommands:

| Subcommand | Description |
|------------|-------------|
| `list` | List recent sessions. |
| `browse` | Interactive session picker with search and resume. |
| `export <output> [--session-id ID]` | Export sessions to JSONL. |
| `delete <session-id>` | Delete one session. |
| `prune` | Delete old sessions. |
| `stats` | Show session-store statistics. |
| `rename <session-id> <title>` | Set or change a session title. |

## `rok insights`

```bash
rok insights [--days N] [--source platform]
```

| Option | Description |
|--------|-------------|
| `--days <n>` | Analyze the last `n` days (default: 30). |
| `--source <platform>` | Filter by source such as `cli`, `telegram`, or `discord`. |

## `rok claw`

```bash
rok claw migrate [options]
```

Migrate your OpenClaw setup to Rok. Reads from `~/.openclaw` (or a custom path) and writes to `~/.rok`. Automatically detects legacy directory names (`~/.clawdbot`, `~/.moldbot`) and config filenames (`clawdbot.json`, `moldbot.json`).

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview what would be migrated without writing anything. |
| `--preset <name>` | Migration preset: `full` (default, includes secrets) or `user-data` (excludes API keys). |
| `--overwrite` | Overwrite existing Rok files on conflicts (default: skip). |
| `--migrate-secrets` | Include API keys in migration (enabled by default with `--preset full`). |
| `--source <path>` | Custom OpenClaw directory (default: `~/.openclaw`). |
| `--workspace-target <path>` | Target directory for workspace instructions (AGENTS.md). |
| `--skill-conflict <mode>` | Handle skill name collisions: `skip` (default), `overwrite`, or `rename`. |
| `--yes` | Skip the confirmation prompt. |

### What gets migrated

The migration covers 30+ categories across persona, memory, skills, model providers, messaging platforms, agent behavior, session policies, MCP servers, TTS, and more. Items are either **directly imported** into Rok equivalents or **archived** for manual review.

**Directly imported:** SOUL.md, MEMORY.md, USER.md, AGENTS.md, skills (4 source directories), default model, custom providers, MCP servers, messaging platform tokens and allowlists (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost), agent defaults (reasoning effort, compression, human delay, timezone, sandbox), session reset policies, approval rules, TTS config, browser settings, tool settings, exec timeout, command allowlist, gateway config, and API keys from 3 sources.

**Archived for manual review:** Cron jobs, plugins, hooks/webhooks, memory backend (QMD), skills registry config, UI/identity, logging, multi-agent setup, channel bindings, IDENTITY.md, TOOLS.md, HEARTBEAT.md, BOOTSTRAP.md.

**API key resolution** checks three sources in priority order: config values → `~/.openclaw/.env` → `auth-profiles.json`. All token fields handle plain strings, env templates (`${VAR}`), and SecretRef objects.

For the complete config key mapping, SecretRef handling details, and post-migration checklist, see the **[full migration guide](../guides/migrate-from-openclaw.md)**.

### Examples

```bash
# Preview what would be migrated
rok claw migrate --dry-run

# Full migration including API keys
rok claw migrate --preset full

# Migrate user data only (no secrets), overwrite conflicts
rok claw migrate --preset user-data --overwrite

# Migrate from a custom OpenClaw path
rok claw migrate --source /home/user/old-openclaw
```

## `rok profile`

```bash
rok profile <subcommand>
```

Manage profiles — multiple isolated Rok instances, each with its own config, sessions, skills, and home directory.

| Subcommand | Description |
|------------|-------------|
| `list` | List all profiles. |
| `use <name>` | Set a sticky default profile. |
| `create <name> [--clone] [--no-alias]` | Create a new profile. `--clone` copies config, `.env`, and `SOUL.md` from the active profile. |
| `delete <name> [-y]` | Delete a profile. |
| `show <name>` | Show profile details (home directory, config, etc.). |
| `alias <name> [--remove] [--name NAME]` | Manage wrapper scripts for quick profile access. |
| `rename <old> <new>` | Rename a profile. |
| `export <name> [-o FILE]` | Export a profile to a `.tar.gz` archive. |
| `import <archive> [--name NAME]` | Import a profile from a `.tar.gz` archive. |

Examples:

```bash
rok profile list
rok profile create work --clone
rok profile use work
rok profile alias work --name h-work
rok profile export work -o work-backup.tar.gz
rok profile import work-backup.tar.gz --name restored
rok -p work chat -q "Hello from work profile"
```

## `rok completion`

```bash
rok completion [bash|zsh]
```

Print a shell completion script to stdout. Source the output in your shell profile for tab-completion of Rok commands, subcommands, and profile names.

Examples:

```bash
# Bash
rok completion bash >> ~/.bashrc

# Zsh
rok completion zsh >> ~/.zshrc
```

## Maintenance commands

| Command | Description |
|---------|-------------|
| `rok version` | Print version information. |
| `rok update` | Pull latest changes and reinstall dependencies. |
| `rok uninstall [--full] [--yes]` | Remove Rok, optionally deleting all config/data. |

## See also

- [Slash Commands Reference](./slash-commands.md)
- [CLI Interface](../user-guide/cli.md)
- [Sessions](../user-guide/sessions.md)
- [Skills System](../user-guide/features/skills.md)
- [Skins & Themes](../user-guide/features/skins.md)
