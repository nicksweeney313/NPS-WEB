#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run(cmd: list[str]) -> None:
    print("→", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main() -> None:
    # Ensure we're in a git repo
    if not (Path.cwd() / ".git").exists():
        raise SystemExit("Error: run this from your repo root (folder containing .git).")

    msg = "Update"
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:]).strip()

    # Show status (useful)
    run(["git", "status"])

    # Stage everything
    run(["git", "add", "-A"])

    # Commit (if there's nothing to commit, don't crash)
    try:
        run(["git", "commit", "-m", msg])
    except subprocess.CalledProcessError:
        # Usually means "nothing to commit"
        print("ℹ️  Nothing new to commit.")

    # Push current branch to origin
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()

    run(["git", "push", "origin", branch])

    print(f"✅ Pushed branch '{branch}' to origin.")

if __name__ == "__main__":
    main()
