"""
Isolated ROKCT Core Plugin

Provides custom workspace mapping and active gateway session status tools.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

# Project types definitions
PROJECT_MOD = "mod"
PROJECT_NODE = "node"
PROJECT_FLUTTER = "flutter"
PROJECT_FRAPPE = "frappe"
PROJECT_PYTHON = "python"
PROJECT_UNKNOWN = "unknown"

SKIP_DIRS = {".git", "node_modules", ".next", "build", "dist", "vendor", "__pycache__", "venv"}

def detect_project_type(directory: Path) -> str:
    """Identifies the language/framework based on file presence."""
    if (directory / "main.go").exists() or (directory / "go.mod").exists():
        return PROJECT_MOD
    if (directory / "package.json").exists():
        return PROJECT_NODE
    if (directory / "pubspec.yaml").exists():
        return PROJECT_FLUTTER
    if (directory / "frappe-app.txt").exists():
        return PROJECT_FRAPPE
    if (directory / "requirements.txt").exists():
        return PROJECT_PYTHON
    return PROJECT_UNKNOWN

def is_entry_point(filename: str, project_type: str) -> bool:
    """Checks if a filename is a common entry point."""
    if project_type == PROJECT_MOD:
        return filename == "main.go"
    if project_type == PROJECT_NODE:
        return filename in ("index.js", "index.ts", "app.js")
    if project_type == PROJECT_FLUTTER:
        return filename == "main.dart"
    if project_type == PROJECT_PYTHON:
        return filename in ("app.py", "manage.py")
    return False

def is_config(filename: str) -> bool:
    """Checks if a filename is a configuration file."""
    return (filename.endswith((".env", ".yml", ".yaml", ".json")) or 
            filename in ("Makefile", "docker-compose.yml"))

def map_workspace(root_path: str = ".") -> str:
    """Scans the given path and identifies all project roots."""
    abs_root = Path(root_path).resolve()
    
    root_node = {
        "path": str(abs_root),
        "name": abs_root.name,
        "children": []
    }

    project_roots = []
    
    for root, dirs, files in os.walk(abs_root):
        current_path = Path(root)
        
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        pt = detect_project_type(current_path)
        if pt != PROJECT_UNKNOWN:
            project_roots.append(current_path)

    for rp in project_roots:
        rel_path = os.path.relpath(rp, abs_root)
        pt = detect_project_type(rp)
        
        node = {
            "path": rel_path if rel_path != "." else "",
            "name": rp.name,
            "type": pt,
            "is_root": True,
            "entry_points": [],
            "configs": []
        }
        
        try:
            for entry in os.scandir(rp):
                if entry.is_file():
                    if is_entry_point(entry.name, pt):
                        node["entry_points"].append(entry.name)
                    if is_config(entry.name):
                        node["configs"].append(entry.name)
        except OSError:
            pass
            
        root_node["children"].append(node)

    return json.dumps(root_node, indent=2)

def generate_session_digest(active_threshold_minutes: int = 60, format: str = "text") -> Any:
    """Generates a digest of current active and idle gateway sessions."""
    try:
        from gateway.config import load_gateway_config
        from gateway.session import SessionStore
        from datetime import datetime, timedelta
        
        # Load gateway config and sessions directory using the rebranded constants
        config = load_gateway_config()
        from rok_constants import get_rok_home
        sessions_dir = get_rok_home() / "sessions"
        
        store = SessionStore(sessions_dir, config)
        store._ensure_loaded()
        
        all_sessions = store.list_sessions()
        if not all_sessions:
            return "No sessions found."
            
        now = datetime.now()
        active = []
        idle = []
        
        threshold = now - timedelta(minutes=active_threshold_minutes)
        
        for entry in all_sessions:
            info = {
                "id": entry.session_id,
                "platform": entry.platform.value if entry.platform else "unknown",
                "user": entry.origin.user_name if entry.origin else "unknown",
                "last_active": entry.updated_at,
                "tokens": entry.total_tokens,
                "display_name": entry.display_name or entry.session_id[:12]
            }
            if entry.updated_at >= threshold:
                active.append(info)
            else:
                idle.append(info)
                
        if format == "card":
            rows = []
            for s in active[:3]:
                rows.append(f"🟢 {s['display_name']}")
            for s in idle[:3]:
                diff = now - s['last_active']
                hours = int(diff.total_seconds() // 3600)
                time_str = f"{hours}h" if hours > 0 else f"{int(diff.total_seconds() // 60)}m"
                rows.append(f"🔴 {s['display_name']} {time_str}")
            
            return {
                "title": "⚕ Your Sessions",
                "rows": rows,
                "footer": f"{len(active)} active / {len(idle)} idle"
            }

        lines = ["# 📊 Session Digest\n"]
        if active:
            lines.append("## 🔥 Active Sessions (Last hour)")
            for s in active:
                lines.append(f"- **{s['user']}** ({s['platform']}): `{s['id'][:8]}` - {s['tokens']} tokens")
            lines.append("")
        if idle:
            lines.append("## 😴 Idle Sessions")
            for s in idle[:5]:
                lines.append(f"- **{s['user']}** ({s['platform']}): `{s['id'][:8]}` (Last active: {s['last_active'].strftime('%H:%M')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error generating digest: {e}"

def session_digest_tool() -> str:
    """Tool entry point."""
    digest = generate_session_digest()
    return json.dumps({"success": True, "digest": digest})

def register(ctx):
    """
    Called automatically on startup by the ROK Plugin Manager.
    Registers custom tools completely outside of core repository files.
    """
    ctx.register_tool(
        name="workspace_map",
        toolset="rokct-coding",
        schema={
            "name": "workspace_map",
            "description": "Recursively scans the workspace to identify project roots, entry points, and configuration files. Use this to understand the high-level architecture of the project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "root_path": {
                        "type": "string",
                        "description": "The root directory to start scanning from (default: '.')",
                        "default": "."
                    }
                }
            }
        },
        handler=lambda args, **kw: map_workspace(args.get("root_path", ".")),
        emoji="🗺️"
    )

    ctx.register_tool(
        name="session_digest",
        toolset="gateway",
        schema={
            "name": "session_digest",
            "description": "Generates a high-level active/idle session status summary.",
            "parameters": {"type": "object", "properties": {}}
        },
        handler=lambda args, **kw: session_digest_tool(),
        emoji="📊"
    )
