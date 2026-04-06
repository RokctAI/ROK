import subprocess
import re
import os
import sys
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
ROOT_DIR        = Path(__file__).resolve().parents[2]
SCRIPT          = Path(__file__).resolve().parent / "rename_replace.py"
WASHLIST_DIR    = Path(__file__).resolve().parent
IGNORE_FILE     = WASHLIST_DIR / "ignore_files.txt"
EXCLUDED_FILE   = WASHLIST_DIR / "excluded_phrases.txt"
PHRASES_FILE    = WASHLIST_DIR / "phrases.txt"
MISSED_FILE     = WASHLIST_DIR / "missed_phrases.txt"
MAX_PASSES      = 3

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
        return {}
    replacements = {}
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

ignore_patterns  = load_list(IGNORE_FILE)
excluded_phrases = load_list(EXCLUDED_FILE)
REPLACEMENTS     = load_replacements(PHRASES_FILE)

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

def build_exclusion_pattern(phrases):
    if not phrases:
        return None
    sorted_phrases = sorted(phrases, key=len, reverse=True)
    combined = "|".join(re.escape(p) + r"[\w-]*" for p in sorted_phrases)
    return re.compile(combined, flags=re.IGNORECASE)

exclusion_pattern = build_exclusion_pattern(excluded_phrases)

def grep_missed():
    missed_occurrences = []
    # Search for anything containing "hermes" or "nousresearch"
    search_pattern = re.compile(r"hermes|nousresearch", re.IGNORECASE)

    for root, dirs, files in os.walk(ROOT_DIR):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_ignore(root_path / d)]

        for name in files:
            file_path = root_path / name
            if should_ignore(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if search_pattern.search(line):
                        if exclusion_pattern and exclusion_pattern.search(line):
                            continue
                        missed_occurrences.append(f"{file_path}:{i+1}: {line.strip()}")
            except Exception:
                pass
    return missed_occurrences

def run_replacer(pass_num):
    print(f"--- PASS {pass_num} ---")
    result = subprocess.run(["python", str(SCRIPT)])
    return result.returncode

# -----------------------------
# Main loop
# -----------------------------
if __name__ == "__main__":
    for p in range(1, MAX_PASSES + 1):
        run_replacer(p)
    
    print("\nChecking for missed phrases...")
    missed = grep_missed()
    if missed:
        print(f"Found {len(missed)} missed occurrences. Writing to {MISSED_FILE}")
        MISSED_FILE.write_text("\n".join(missed), encoding="utf-8")
    else:
        print("No missed phrases found!")
        if MISSED_FILE.exists():
            MISSED_FILE.unlink()

    print("\nRebranding run complete.")
