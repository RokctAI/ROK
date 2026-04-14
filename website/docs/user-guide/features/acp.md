---
sidebar_position: 11
title: "ACP Editor Integration"
description: "Use Rok Agent inside ACP-compatible editors such as VS Code, Zed, and JetBrains"
---

# ACP Editor Integration

Rok Agent can run as an ACP server, letting ACP-compatible editors talk to Rok over stdio and render:

- chat messages
- tool activity
- file diffs
- terminal commands
- approval prompts
- streamed thinking / response chunks

ACP is a good fit when you want Rok to behave like an editor-native coding agent instead of a standalone CLI or messaging bot.

## What Rok exposes in ACP mode

Rok runs with a curated `rok-acp` toolset designed for editor workflows. It includes:

- file tools: `read_file`, `write_file`, `patch`, `search_files`
- terminal tools: `terminal`, `process`
- web/browser tools
- memory, todo, session search
- skills
- execute_code and delegate_task
- vision

It intentionally excludes things that do not fit typical editor UX, such as messaging delivery and cronjob management.

## Installation

Install Rok normally, then add the ACP extra:

```bash
pip install -e '.[acp]'
```

This installs the `agent-client-protocol` dependency and enables:

- `rok acp`
- `rok-acp`
- `python -m acp_adapter`

## Launching the ACP server

Any of the following starts Rok in ACP mode:

```bash
rok acp
```

```bash
rok-acp
```

```bash
python -m acp_adapter
```

Rok logs to stderr so stdout remains reserved for ACP JSON-RPC traffic.

## Editor setup

### VS Code

Install an ACP client extension, then point it at the repo's `acp_registry/` directory.

Example settings snippet:

```json
{
  "acpClient.agents": [
    {
      "name": "rok",
      "registryDir": "/path/to/rok/acp_registry"
    }
  ]
}
```

### Zed

Example settings snippet:

```json
{
  "agent_servers": {
    "rok": {
      "type": "custom",
      "command": "rok",
      "args": ["acp"],
    },
  },
}
```

### JetBrains

Use an ACP-compatible plugin and point it at:

```text
/path/to/rok/acp_registry
```

## Registry manifest

The ACP registry manifest lives at:

```text
acp_registry/agent.json
```

It advertises a command-based agent whose launch command is:

```text
rok acp
```

## Configuration and credentials

ACP mode uses the same Rok configuration as the CLI:

- `~/.rok/.env`
- `~/.rok/config.yaml`
- `~/.rok/skills/`
- `~/.rok/state.db`

Provider resolution uses Rok' normal runtime resolver, so ACP inherits the currently configured provider and credentials.

## Session behavior

ACP sessions are tracked by the ACP adapter's in-memory session manager while the server is running.

Each session stores:

- session ID
- working directory
- selected model
- current conversation history
- cancel event

The underlying `AIAgent` still uses Rok' normal persistence/logging paths, but ACP `list/load/resume/fork` are scoped to the currently running ACP server process.

## Working directory behavior

ACP sessions bind the editor's cwd to the Rok task ID so file and terminal tools run relative to the editor workspace, not the server process cwd.

## Approvals

Dangerous terminal commands can be routed back to the editor as approval prompts. ACP approval options are simpler than the CLI flow:

- allow once
- allow always
- deny

On timeout or error, the approval bridge denies the request.

## Troubleshooting

### ACP agent does not appear in the editor

Check:

- the editor is pointed at the correct `acp_registry/` path
- Rok is installed and on your PATH
- the ACP extra is installed (`pip install -e '.[acp]'`)

### ACP starts but immediately errors

Try these checks:

```bash
rok doctor
rok status
rok acp
```

### Missing credentials

ACP mode does not have its own login flow. It uses Rok' existing provider setup. Configure credentials with:

```bash
rok model
```

or by editing `~/.rok/.env`.

## See also

- [ACP Internals](../../developer-guide/acp-internals.md)
- [Provider Runtime Resolution](../../developer-guide/provider-runtime.md)
- [Tools Runtime](../../developer-guide/tools-runtime.md)
