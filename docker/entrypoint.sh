#!/bin/bash
# Docker entrypoint: bootstrap config files into the mounted volume, then run rok.
set -e

ROK_HOME="/opt/data"
INSTALL_DIR="/opt/rok"

# --- Privilege dropping via gosu ---
# When started as root (the default), optionally remap the rok user/group
# to match host-side ownership, fix volume permissions, then re-exec as rok.
if [ "$(id -u)" = "0" ]; then
    if [ -n "$ROK_UID" ] && [ "$ROK_UID" != "$(id -u rok)" ]; then
        echo "Changing rok UID to $ROK_UID"
        usermod -u "$ROK_UID" rok
    fi

    if [ -n "$ROK_GID" ] && [ "$ROK_GID" != "$(id -g rok)" ]; then
        echo "Changing rok GID to $ROK_GID"
        groupmod -g "$ROK_GID" rok
    fi

    actual_rok_uid=$(id -u rok)
    if [ "$(stat -c %u "$ROK_HOME" 2>/dev/null)" != "$actual_rok_uid" ]; then
        echo "$ROK_HOME is not owned by $actual_rok_uid, fixing"
        chown -R rok:rok "$ROK_HOME"
    fi

    echo "Dropping root privileges"
    exec gosu rok "$0" "$@"
fi

# --- Running as rok from here ---
source "${INSTALL_DIR}/.venv/bin/activate"

# Create essential directory structure.  Cache and platform directories
# (cache/images, cache/audio, platforms/whatsapp, etc.) are created on
# demand by the application — don't pre-create them here so new installs
# get the consolidated layout from get_rok_dir().
# The "home/" subdirectory is a per-profile HOME for subprocesses (git,
# ssh, gh, npm …).  Without it those tools write to /root which is
# ephemeral and shared across profiles.  See issue #4426.
mkdir -p "$ROK_HOME"/{cron,sessions,logs,hooks,memories,skills,skins,plans,workspace,home}

# .env
if [ ! -f "$ROK_HOME/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$ROK_HOME/.env"
fi

# config.yaml
if [ ! -f "$ROK_HOME/config.yaml" ]; then
    cp "$INSTALL_DIR/cli-config.yaml.example" "$ROK_HOME/config.yaml"
fi

# SOUL.md
if [ ! -f "$ROK_HOME/SOUL.md" ]; then
    cp "$INSTALL_DIR/docker/SOUL.md" "$ROK_HOME/SOUL.md"
fi

# Sync bundled skills (manifest-based so user edits are preserved)
if [ -d "$INSTALL_DIR/skills" ]; then
    python3 "$INSTALL_DIR/tools/skills_sync.py"
fi

exec rok "$@"
