#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run(cmd: list[str]) -> None:
    print("→", " ".join(cmd))
    subprocess.run(cmd, check=True)

def main() -> None:
    if not (Path.cwd() / ".git").exists():
        raise SystemExit("Error: run this from your repo root (folder containing .git).")

    msg = "Update"
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:]).strip()

    run(["git", "add", "-A"])
    run(["git", "status"])

    # Commit (no-op if nothing changed)
    r = subprocess.run(["git", "commit", "-m", msg])
    if r.returncode != 0:
        print("ℹ️  Nothing new to commit.")

    branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
    run(["git", "push", "origin", branch])

if __name__ == "__main__":
    main()
