#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

REPO = Path.home() / "dev" / "NPS-WEB"
SITE_DIR = REPO / "site"

def run(cmd, cwd=REPO, capture=False, check=True):
    print(f"\n→ ({cwd}) $ {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        check=check,
        capture_output=capture,
    )

def git_has_changes(repo_dir=REPO) -> bool:
    r = run(["git", "status", "--porcelain"], cwd=repo_dir, capture=True)
    return bool(r.stdout.strip())

def current_branch() -> str:
    r = run(["git", "branch", "--show-current"], capture=True)
    return r.stdout.strip()

def stash_if_needed() -> bool:
    """Stash unstaged/staged changes (but not untracked) if needed. Returns True if we stashed."""
    if not git_has_changes():
        return False
    # stash tracked changes only; keep untracked files in place
    run(["git", "stash", "push", "-m", "deploy.py autostash", "--keep-index"])
    return True

def pop_stash_if_present():
    # Pop only if the top stash is ours
    r = run(["git", "stash", "list"], capture=True)
    top = r.stdout.splitlines()[0] if r.stdout.strip() else ""
    if "deploy.py autostash" in top:
        run(["git", "stash", "pop"])
    else:
        print("\n(no deploy.py autostash to pop)")

def get_remote_url() -> str:
    r = run(["git", "remote", "get-url", "origin"], capture=True)
    return r.stdout.strip()

def guess_actions_url(remote_url: str) -> str:
    remote_url = remote_url.removesuffix(".git")
    if remote_url.startswith("git@github.com:"):
        path = remote_url.split("git@github.com:", 1)[1]
        return f"https://github.com/{path}/actions"
    if remote_url.startswith("https://github.com/"):
        return f"{remote_url}/actions"
    return ""

def main():
    if not REPO.exists():
        raise SystemExit(f"Repo not found at {REPO}")
    if not SITE_DIR.exists():
        raise SystemExit(f"Quarto site dir not found at {SITE_DIR}")

    msg = "Update site"
    do_render = True
    for a in sys.argv[1:]:
        if a == "--no-render":
            do_render = False
        else:
            msg = a

    run(["git", "switch", "main"])
    stashed = stash_if_needed()

    run(["git", "fetch", "origin", "--prune"])
    run(["git", "pull", "--rebase", "origin", "main"])

    if stashed:
        pop_stash_if_present()

    # Optional local render (catches errors fast)
    if do_render:
        run(["quarto", "render"], cwd=SITE_DIR)

    # Commit + push (if needed)
    if git_has_changes():
        run(["git", "add", "-A"])
        run(["git", "commit", "-m", msg])
    else:
        print("\n(no changes to commit)")

    run(["git", "push", "origin", "main"])

    remote = get_remote_url()
    actions_url = guess_actions_url(remote)

    print("\n✅ Pushed to main.")
    if actions_url:
        print(f"→ Check deploy progress in GitHub Actions: {actions_url}")
    else:
        print("→ Check deploy progress in GitHub Actions (repo Actions tab).")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print("\n❌ Command failed.")
        if getattr(e, "stdout", None):
            print("\n--- stdout ---\n", e.stdout)
        if getattr(e, "stderr", None):
            print("\n--- stderr ---\n", e.stderr)
        raise
