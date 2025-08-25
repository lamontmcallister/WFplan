
import sys, re
from pathlib import Path
import shutil

def clean_file(path_str: str):
    p = Path(path_str)
    if not p.exists():
        print(f"[ERROR] File not found: {p}")
        sys.exit(1)

    backup = p.with_suffix(p.suffix + ".backup")
    shutil.copyfile(p, backup)
    print(f"[INFO] Backup saved to: {backup}")

    text = p.read_text()

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 1) Convert stray bare headers like "(Something) ---" -> "# --- Something ---"
    def fix_bare_header(line: str) -> str:
        m = re.match(r'^\s*\((.+?)\)\s*---\s*$', line)
        if m:
            inner = m.group(1).strip()
            return f"# --- {inner} ---"
        return line

    lines = [fix_bare_header(ln) for ln in text.splitlines()]

    # 2) Normalize header comments to column 0 and single "# "
    def is_header_comment(s: str) -> bool:
        return re.match(r'^\s*#\s*--- .* ---\s*$', s or "") is not None

    new_lines = []
    for ln in lines:
        if is_header_comment(ln):
            ln = re.sub(r'^\s*#\s*', '# ', ln)  # ensure "# " prefix
        new_lines.append(ln)

    # 3) Ensure top-level "if page ==" blocks are at column 0
    cleaned = "\n".join(new_lines)
    cleaned = re.sub(r'^\s+(if page == )', r'\1', cleaned, flags=re.MULTILINE)

    # 4) Convert tabs to 4 spaces (safe normalization)
    cleaned = cleaned.replace("\t", "    ")

    # 5) Ensure file ends with a newline
    if not cleaned.endswith("\n"):
        cleaned += "\n"

    p.write_text(cleaned)
    print(f"[INFO] Cleaned and wrote: {p}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python wf_cleaner.py /path/to/WF.py")
        sys.exit(2)
    sys.exit(clean_file(sys.argv[1]))
