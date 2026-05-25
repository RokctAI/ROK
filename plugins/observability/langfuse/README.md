# Langfuse Observability Plugin

This plugin ships bundled with Rok but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
rok tools  # → Langfuse Observability

# Manual
pip install langfuse
rok plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.rok/.env` (or via `rok tools`):

```bash
ROK_LANGFUSE_PUBLIC_KEY=pk-lf-...
ROK_LANGFUSE_SECRET_KEY=sk-lf-...
ROK_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
rok plugins list                 # observability/langfuse should show "enabled"
rok chat -q "hello"              # then check Langfuse for a "Rok turn" trace
```

## Optional tuning

```bash
ROK_LANGFUSE_ENV=production       # environment tag
ROK_LANGFUSE_RELEASE=v1.0.0       # release tag
ROK_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
ROK_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
ROK_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
rok plugins disable observability/langfuse
```
