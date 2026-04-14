import os
import re
from pathlib import Path

# -----------------------------
# Paths
# -----------------------------
ROOT_DIR     = Path(__file__).resolve().parents[2]
WASHLIST_DIR = Path(__file__).resolve().parent

IGNORE_FILE   = WASHLIST_DIR / "ignore_files.txt"
EXCLUDED_FILE = WASHLIST_DIR / "excluded_phrases.txt"
PHRASES_FILE  = WASHLIST_DIR / "phrases.txt"
MISSED_FILE   = WASHLIST_DIR / "missed_phrases.txt"

# -----------------------------
# Load helpers
# -----------------------------
def load_list(file_path):
    if not file_path.exists():
        return []
    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.startswith("#")
    ]

def load_replacements(file_path):
    replacements = {}
    if not file_path.exists():
        return replacements

    for line in file_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=>" in line:
            old, new = line.split("=>", 1)
        elif ":" in line:
            old, new = line.split(":", 1)
        else:
            continue

        replacements[old.strip()] = new.strip()

    return replacements

IGNORE_PATTERNS  = load_list(IGNORE_FILE)
EXCLUDED_PHRASES = load_list(EXCLUDED_FILE)
REPLACEMENTS     = load_replacements(PHRASES_FILE)

TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml",
    ".ts", ".tsx", ".js", ".jsx",
    ".env", ".toml", ".ini", ".cfg", ".sh", ".nix", ".lock",
    ".css", ".html", ".svg"
}

# -----------------------------
# Ignore logic
# -----------------------------
def should_ignore(path: Path):
    parts = path.parts
    if ".git" in parts or ".rokct" in parts:
        return True

    path_str = str(path).replace("\\", "/")
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str:
            return True

    return False

def is_text_file(path: Path):
    return path.suffix.lower() in TEXT_EXTENSIONS

# -----------------------------
# Case-preserving replacement
# -----------------------------
def match_case(original, replacement):
    if original.isupper():
        return replacement.upper()
    elif original.islower():
        return replacement.lower()
    elif original[0].isupper():
        return replacement.capitalize()
    else:
        return replacement

def smart_replace(text, old, new):
    def repl(match):
        return match_case(match.group(0), new)
    return re.sub(re.escape(old), repl, text, flags=re.IGNORECASE)

def replace_hermes_smart(text):
    def repl(match):
        return match_case(match.group(0), "rok")
    return re.sub(r"hermes", repl, text, flags=re.IGNORECASE)

# -----------------------------
# Exclusion protection
# -----------------------------
def protect_exclusions(text):
    placeholders = {}
    for i, phrase in enumerate(EXCLUDED_PHRASES):
        key = f"__EXCL_{i}__"
        if phrase in text:
            placeholders[key] = phrase
            text = text.replace(phrase, key)
    return text, placeholders

def restore_exclusions(text, placeholders):
    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text

# -----------------------------
# Content replacement
# -----------------------------
def replace_content(text):
    text, placeholders = protect_exclusions(text)

    # 1. Apply explicit replacements first
    sorted_items = sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)
    for old, new in sorted_items:
        text = smart_replace(text, old, new)

    # 2. Final sweep (case-aware)
    text = replace_hermes_smart(text)

    text = restore_exclusions(text, placeholders)
    return text

# -----------------------------
# Filename replacement
# -----------------------------
def replace_name_smart(name):
    def repl(match):
        return match_case(match.group(0), "rok")
    return re.sub(r"hermes", repl, name, flags=re.IGNORECASE)

def compute_new_name(name):
    for old, new in REPLACEMENTS.items():
        name = smart_replace(name, old, new)

    name = replace_name_smart(name)
    return name

# -----------------------------
# Safe rename
# -----------------------------
def safe_rename(old_path, new_path):
    if old_path == new_path:
        return False

    if not old_path.exists():
        return False

    if new_path.exists():
        print(f"⚠ exists: {old_path} -> {new_path}")
        return False

    try:
        old_path.rename(new_path)
        print(f"✔ renamed: {old_path.relative_to(ROOT_DIR)} -> {new_path.name}")
        return True
    except Exception as e:
        print(f"✗ rename failed: {old_path}: {e}")
        return False

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    total_scanned  = 0
    total_modified = 0
    total_renamed  = 0

    print(f"ROOT: {ROOT_DIR}\n")

    # PASS 1 — content
    for root, dirs, files in os.walk(ROOT_DIR):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d)]

        for name in files:
            file_path = root_path / name
            total_scanned += 1

            if should_ignore(file_path) or not is_text_file(file_path):
                continue

            try:
                original = file_path.read_text(encoding="utf-8", errors="ignore")
                updated  = replace_content(original)

                if updated != original:
                    file_path.write_text(updated, encoding="utf-8")
                    total_modified += 1
            except:
                pass

    # PASS 2 — rename (bottom-up)
    rename_pairs = []

    for root, dirs, files in os.walk(ROOT_DIR, topdown=False):
        root_path = Path(root)

        for name in files + dirs:
            old_path = root_path / name

            if should_ignore(old_path):
                continue

            new_name = compute_new_name(name)

            if new_name != name:
                new_path = old_path.with_name(new_name)
                rename_pairs.append((old_path, new_path))

    for old_path, new_path in rename_pairs:
        if safe_rename(old_path, new_path):
            total_renamed += 1

    # -----------------------------
    # FINAL VERIFICATION
    # -----------------------------
    missed = []

    for root, dirs, files in os.walk(ROOT_DIR):
        root_path = Path(root)

        for name in files:
            file_path = root_path / name

            if should_ignore(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"hermes", content, re.IGNORECASE):
                    missed.append(str(file_path))
            except:
                pass

    print("\nRESULT:")
    print(f"Scanned:  {total_scanned}")
    print(f"Modified: {total_modified}")
    print(f"Renamed:  {total_renamed}")

    if missed:
        print(f"\n❌ STILL FOUND {len(missed)} FILES WITH 'hermes'")
        MISSED_FILE.write_text("\n".join(missed), encoding="utf-8")
        exit(1)
    else:
        print("\n✅ ZERO REMAINING — CLEAN REBRAND")