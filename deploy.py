#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path

CV_SRC = Path("cv/main.pdf")
CV_SITE_DST = Path("site/assets/cv.pdf")

# LaTeX artefacts to ensure are ignored (PDF is NOT ignored)
CV_GITIGNORE_CONTENT = """\
# LaTeX build artefacts (keep main.pdf tracked)
*.aux
*.bbl
*.bcf
*.blg
*.fdb_latexmk
*.fls
*.log
*.out
*.run.xml
*.synctex.gz
"""

def run(cmd: list[str]) -> None:
    print("→", " ".join(cmd))
    subprocess.run(cmd, check=True)

def try_run(cmd: list[str]) -> bool:
    print("→", " ".join(cmd))
    return subprocess.run(cmd).returncode == 0

def capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def ensure_repo_root() -> None:
    if not (Path.cwd() / ".git").exists():
        raise SystemExit("Error: run this from your repo root (folder containing .git).")

def ensure_cv_gitignore() -> None:
    gi = Path("cv/.gitignore")
    existing = gi.read_text() if gi.exists() else ""
    if existing.strip() != CV_GITIGNORE_CONTENT.strip():
        gi.write_text(CV_GITIGNORE_CONTENT)
        print("✅ Ensured cv/.gitignore (ignoring LaTeX artefacts)")

def untrack_if_tracked(paths: list[str]) -> None:
    # If these were ever committed before, .gitignore won't stop them until untracked.
    tracked: list[str] = []
    for p in paths:
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", p],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if r.returncode == 0:
            tracked.append(p)

    if tracked:
        run(["git", "rm", "--cached", "--quiet", "--"] + tracked)
        print("✅ Removed previously-tracked artefacts from index (kept local files)")

def sync_cv_pdf() -> None:
    if not CV_SRC.exists():
        raise SystemExit(f"Error: missing {CV_SRC}. Compile CV first (cv/main.tex → cv/main.pdf).")
    CV_SITE_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CV_SRC, CV_SITE_DST)
    print(f"✅ Synced CV PDF: {CV_SRC} → {CV_SITE_DST}")

def main() -> None:
    ensure_repo_root()

    msg = "Update"
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:]).strip()

    # 1) Keep the website copy of the PDF up to date
    sync_cv_pdf()

    # 2) Ensure LaTeX junk is ignored (but PDF is not)
    ensure_cv_gitignore()

    # 3) If any junk files were previously committed, untrack them once
    latex_junk = [
        "cv/main.aux","cv/main.bbl","cv/main.bcf","cv/main.blg","cv/main.fdb_latexmk",
        "cv/main.fls","cv/main.log","cv/main.out","cv/main.run.xml","cv/main.synctex.gz"
    ]
    untrack_if_tracked(latex_junk)

    # 4) Stage EVERYTHING else (respects .gitignore)
    run(["git", "add", "-A"])

    run(["git", "status"])

    # 5) Commit if there are staged changes
    # If nothing staged, git commit returns non-zero; we handle that.
    if try_run(["git", "commit", "-m", msg]):
        pass
    else:
        print("ℹ️  Nothing new to commit.")

    # 6) Push current branch
    branch = capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    run(["git", "push", "origin", branch])
    print(f"✅ Pushed '{branch}' to origin.")

if __name__ == "__main__":
    main()
