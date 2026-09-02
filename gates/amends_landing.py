#!/usr/bin/env python3
"""Issue #3134 repair round 3, finding 3: the automatic caller
`write_backlinks()`/`--apply-backlinks` never had.

The round-2 delivery built the landing-step action (`amends_index.py::
write_backlinks()`/`--apply-backlinks`) but nothing anywhere called it: no
CI workflow exists in this repo, no hook, no code path. A correcting PR
could land with its `amends:` edge permanently unlinked unless a human
remembered to run the CLI by hand -- confirmed live by grepping the whole
tree for any caller (docs/issue-3134/reports/adversarial-review+
knowledge-management-supersession-lifecycle+silent-failure-audit-
48484397.md, "What was done" item 4).

`land()` is that caller. It is deliberately NOT run against the
orchestrator's own live checkout (mutating a working directory a human or
another process may be using concurrently is its own hazard) -- it clones
`remote`@`branch` into a disposable directory, applies backlinks and
regenerates the index there, and pushes the result straight back if
anything changed. `on-the-record/hooks/amends-landing-apply.sh` calls
this on a successful `gh pr merge`, so the backlink appears in the
target with no human step between the PR landing and the correction
becoming visible to a reader who opens it directly.

  python3 gates/amends_landing.py <remote> [<branch>]   # default branch: main
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import amends_index  # noqa: E402


def land(remote: str, branch: str = "main", workdir: str | None = None) -> dict:
    """Clone `remote`@`branch` into a disposable directory, apply
    backlinks and regenerate the index, push the result back to `branch`
    if anything changed. Returns `{"pushed": bool, "written": [...],
    "error": str | None, "remaining": [...]}`. Never raises -- a clone or
    push failure is reported in `error`, not thrown, since the caller (a
    `PostToolUse` hook, which cannot deny anything) has nothing useful to
    do with an exception; `remaining` carries whatever `check()` still
    reports after the apply (a structural problem -- broken target,
    missing section, conflict, cycle -- that no automatic apply can
    resolve, surfaced rather than silently dropped)."""
    tmp = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="amends-landing-"))
    owns_tmp = workdir is None
    try:
        r = subprocess.run(
            ["git", "clone", "--quiet", "--branch", branch, "--single-branch",
             remote, str(tmp)],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            return {"pushed": False, "written": [], "error": r.stderr.strip(),
                     "remaining": []}

        written = amends_index.write_backlinks(tmp)
        amends_index.update(tmp)
        remaining = amends_index.check(tmp)

        status = subprocess.run(
            ["git", "-C", str(tmp), "status", "--porcelain"],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        if not status:
            return {"pushed": False, "written": written, "error": None,
                     "remaining": remaining}

        subprocess.run(["git", "-C", str(tmp), "add", "-A"],
                        capture_output=True, timeout=30)
        subprocess.run(
            ["git", "-C", str(tmp),
             "-c", "user.email=amends-landing@tokenmaxxxer.local",
             "-c", "user.name=amends-landing-bot",
             "commit", "-q", "-m",
             "amends: apply backlinks -- issue #3134 landing step"],
            capture_output=True, timeout=30,
        )
        r = subprocess.run(
            ["git", "-C", str(tmp), "push", "origin", "HEAD:" + branch],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode != 0:
            return {"pushed": False, "written": written,
                     "error": r.stderr.strip(), "remaining": remaining}
        return {"pushed": True, "written": written, "error": None,
                 "remaining": remaining}
    finally:
        if owns_tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print("usage: python3 gates/amends_landing.py <remote> [<branch>]",
              file=sys.stderr)
        return 1
    remote = argv[0]
    branch = argv[1] if len(argv) > 1 else "main"
    result = land(remote, branch)
    if result["error"]:
        print(f"amends-landing: {result['error']}", file=sys.stderr)
        return 1
    if result["pushed"]:
        print("backlinks applied and pushed: " + ", ".join(result["written"]))
    else:
        print("no backlinks needed -- every amended target already "
              "carries its marker")
    if result["remaining"]:
        print("remaining (not auto-resolvable, needs a human decision):")
        for r in result["remaining"]:
            print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
