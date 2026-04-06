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
    if not file_path.exists():
        print(f"⚠ phrases file missing: {file_path}")
        return {}

    replacements = {}
    for line in file_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=>" not in line:
            # Fallback to colon if => not present for legacy support
            if ":" in line:
                old, new = line.split(":", 1)
            else:
                print(f"⚠ invalid line (skip): {line}")
                continue
        else:
            old, new = line.split("=>", 1)
            
        replacements[old.strip()] = new.strip()

    return replacements

ignore_patterns  = load_list(IGNORE_FILE)
excluded_phrases = load_list(EXCLUDED_FILE)
REPLACEMENTS     = load_replacements(PHRASES_FILE)

TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml",
    ".ts", ".tsx", ".js", ".jsx",
    ".env", ".toml", ".ini", ".cfg", ".sh", ".nix", ".lock"
}

# -----------------------------
# Ignore logic
# -----------------------------
def should_ignore(path: Path):
    path_str = str(path).replace("\\", "/")
    if ".git" in path_str or ".rokct" in path_str:
        return True
    for pattern in ignore_patterns:
        pattern = pattern.replace("\\", "/")
        if pattern.endswith("/"):
            if pattern.rstrip("/") in path_str:
                return True
        if pattern in path_str:
            return True
    return False

def is_text_file(path: Path):
    return path.suffix.lower() in TEXT_EXTENSIONS

# -----------------------------
# Protect excluded phrases
# -----------------------------
def build_exclusion_pattern(phrases):
    if not phrases:
        return None
    sorted_phrases = sorted(phrases, key=len, reverse=True)
    # Match the excluded phrase possibly followed by more word chars/hyphens
    combined = "|".join(re.escape(p) + r"[\w-]*" for p in sorted_phrases)
    return re.compile(combined, flags=re.IGNORECASE)

exclusion_pattern = build_exclusion_pattern(excluded_phrases)

def protect_phrases(text):
    if not exclusion_pattern:
        return text, {}
    placeholders = {}
    counter = [0]

    def replacer(m):
        key = f"__EXCL_{counter[0]}__"
        counter[0] += 1
        placeholders[key] = m.group(0)
        return key

    text = exclusion_pattern.sub(replacer, text)
    return text, placeholders

def restore_phrases(text, placeholders):
    for key, val in placeholders.items():
        text = text.replace(key, val)
    return text

# -----------------------------
# Replace logic
# -----------------------------
def replace_content(text):
    text, placeholders = protect_phrases(text)

    # Sort replacements by length descending to match longer phrases first
    sorted_items = sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)

    for old, new in sorted_items:
        # Use boundary check that doesn't treat underscores as word characters
        # so hermes matches in hermes_constants if hermes is replaced.
        pattern = re.compile(rf"(?<![a-zA-Z0-9]){re.escape(old)}(?![a-zA-Z0-9])")
        text = pattern.sub(new, text)

    text = restore_phrases(text, placeholders)
    return text

# -----------------------------
# Main Execution
# -----------------------------
if __name__ == "__main__":
    total_scanned  = 0
    total_modified = 0
    total_renamed  = 0
    
    # Pass 1: Replace file contents
    for root, dirs, files in os.walk(ROOT_DIR):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d)]

        for name in files:
            file_path = root_path / name
            total_scanned += 1

            if should_ignore(file_path) or not is_text_file(file_path):
                continue

            try:
                original = file_path.read_text(encoding="utf-8")
                updated  = replace_content(original)
                if updated != original:
                    file_path.write_text(updated, encoding="utf-8")
                    total_modified += 1
            except Exception as e:
                pass # skip binary or encoding errors silently

    # Pass 2 & 3: Rename files and folders (bottom-up)
    for root, dirs, files in os.walk(ROOT_DIR, topdown=False):
        root_path = Path(root)

        for name in files + dirs:
            old_path = root_path / name
            if should_ignore(old_path):
                continue

            new_name = name
            sorted_items = sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)
            for old, new in sorted_items:
                # Use robust boundary-like logic for renaming too if appropriate, 
                # but simple replace is usually what's wanted for filenames.
                new_name = new_name.replace(old, new)

            if new_name != name:
                new_path = old_path.with_name(new_name)
                try:
                    if not new_path.exists():
                        old_path.rename(new_path)
                        total_renamed += 1
                except Exception as e:
                    print(f"Error renaming {old_path}: {e}")

    print(f"Scanned: {total_scanned}, Modified: {total_modified}, Renamed: {total_renamed}")
