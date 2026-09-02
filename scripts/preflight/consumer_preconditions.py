#!/usr/bin/env python3
"""Read-only preflight for the on-the-record consumer loop (issue #3182).

The operator's claim under test: installing only the on-the-record plugin
structurally suffices for a consumer session to work on a target repo. This
script enumerates the external preconditions the loop's real code paths
depend on -- spawn dispatch (spawn.py/pipeline.py), skill resolution
(skills.py), `gh`/git auth, and the target repo's board opt-in file -- and
reports each as satisfied or missing with the exact remedy. It never asserts
a precondition it did not actually check: if a check cannot run (binary
missing, subprocess failure, permission error, or a precondition whose
outcome would require a mutating action to observe), the precondition is
reported `satisfied: false`, never guessed `true`.

Every entry's `source` field cites the file:line in this repository whose
code path requires that precondition -- not documentation, not intuition.

Contract:
  - `--json` prints {"preconditions": [{"name","satisfied","remedy",
    "source"}, ...]} to stdout as parseable JSON.
  - No flag prints a human-readable report to stdout.
  - Exit code is 0 when every precondition is satisfied, 1 when any is
    missing. No other exit code is used.
  - Zero side effects: no file writes outside stdout, no process/state
    mutation, no `git`/`gh` invocation that creates or changes anything
    (only read-only forms: `git config --get`, `gh auth status`,
    `shutil.which`, filesystem existence checks).

Portability (macOS + Linux, stdlib only):
  - No GNU-only flags: no `stat -c` (BSD `stat` uses `-f`), no `date -d`,
    no `readlink -f`, no `sed -i`. This script uses `shutil.which` and
    `pathlib.Path`/`os.stat` instead of shelling out to `stat`/`readlink`
    at all, so the BSD/GNU flag divergence never comes up.
  - No `/proc` reads (absent on macOS).
  - `subprocess.run(..., timeout=...)` everywhere a subprocess is
    launched, so a hung `gh`/`git` cannot hang the preflight itself on
    either platform.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SUBPROCESS_TIMEOUT_SECONDS = 10

# Mirrors spawn.py's own _spawn_capacity_check() defaults (spawn.py:725-726)
# so this check degrades the same way spawn.py's real gate would, without
# importing spawn.py itself.
MIN_FREE_BYTES_DEFAULT = 3 * 119 * 1024 * 1024   # ~357MB
MIN_FREE_INODES_DEFAULT = 1000


def _run_readonly(argv: list[str], timeout: int = SUBPROCESS_TIMEOUT_SECONDS):
    """Run a read-only subprocess; never raises.

    Returns (returncode, stdout, stderr). returncode is -1 for every
    failure mode that isn't a normal process exit (binary missing, PATH
    resolution error, timeout, permission error, ...) so callers can
    treat -1 as "could not observe" rather than "observed failure".
    """
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any
        # failure here degrades this check to satisfied=false, it must
        # never propagate out of a check function.
        return -1, "", f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Individual checks. Each returns (satisfied: bool, detail: str) and is
# written so it cannot raise on its own -- filesystem/subprocess calls are
# wrapped locally, and run_checks() below adds one more catch-all layer so a
# defect in a single check degrades to "missing", never a crash or a
# silently-assumed "satisfied".
# ---------------------------------------------------------------------------

def check_posix_fork() -> tuple[bool, str]:
    has_fork = hasattr(os, "fork")
    has_setsid = hasattr(os, "setsid")
    on_supported_platform = sys.platform in ("linux", "darwin")
    ok = has_fork and has_setsid and on_supported_platform
    return ok, f"platform={sys.platform} fork={has_fork} setsid={has_setsid}"


def check_claude_cli_present() -> tuple[bool, str]:
    path = shutil.which("claude")
    return path is not None, (path or "not found on PATH")


def check_git_cli_present() -> tuple[bool, str]:
    path = shutil.which("git")
    return path is not None, (path or "not found on PATH")


def check_gh_cli_authenticated() -> tuple[bool, str]:
    if shutil.which("gh") is None:
        return False, "gh not found on PATH"
    rc, out, err = _run_readonly(["gh", "auth", "status"])
    combined = (out + err).strip().replace("\n", " ")[:400]
    return rc == 0, combined or f"gh auth status exited {rc}"


def check_git_identity_configured() -> tuple[bool, str]:
    if shutil.which("git") is None:
        return False, "git not found on PATH"
    rc_name, name_out, _ = _run_readonly(["git", "config", "--get", "user.name"])
    rc_email, email_out, _ = _run_readonly(["git", "config", "--get", "user.email"])
    name = name_out.strip()
    email = email_out.strip()
    ok = rc_name == 0 and rc_email == 0 and bool(name) and bool(email)
    return ok, f"user.name={name or '<unset>'} user.email={email or '<unset>'}"


def check_skill_repository_resolvable() -> tuple[bool, str]:
    """Mirrors skills.py's `_skill_repo_root()` resolution order (env var >
    sibling clone) plus the already-cloned managed-clone location, all as
    pure existence checks -- this script never triggers the network clone
    that `_skill_repo_managed_root()` performs on a real spawn."""
    candidates: list[Path] = []
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        candidates.append(Path(os.path.expanduser(os.path.expandvars(env_value))))
    rulebooks = os.environ.get("TOKENMAXXXER_RULEBOOKS")
    if rulebooks:
        candidates.append(Path(os.path.expanduser(rulebooks)) / "skill-repository")
    # Managed-clone location, relative to this script's own repo root
    # (scripts/preflight/../.. == the checkout spawn.py itself sits in).
    # Observed only -- never created by this script.
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidates.append(repo_root / "runs" / "rulebooks" / "skill-repository" / "skills")
    for p in candidates:
        try:
            if p.is_dir() and any(
                c.is_dir() and not c.name.startswith(".") for c in p.iterdir()
            ):
                return True, f"resolved at {p}"
        except OSError:
            continue
    return False, (
        "no MUSTER_SKILL_REPO, no $TOKENMAXXXER_RULEBOOKS/skill-repository "
        "sibling clone, and no already-populated managed clone found"
    )


def check_home_claude_skills_dir_present() -> tuple[bool, str]:
    p = Path(os.path.expanduser("~/.claude/skills"))
    return p.is_dir(), str(p)


def check_target_repo_board_file_present() -> tuple[bool, str]:
    p = Path.cwd() / "docs" / "specs" / "approvers.md"
    return p.is_file(), str(p)


def check_remote_push_access() -> tuple[bool, str]:
    """Whether `origin` will actually accept a push of a new role branch
    cannot be determined without attempting a write (a real `git push`),
    which this script must never perform. Per the unobservable-means-
    missing rule, this is always reported unsatisfied -- it is a manual
    check, not a preflight-covered one."""
    return False, (
        "not observable without a mutating `git push` -- verify manually "
        "with e.g. `git push --dry-run origin HEAD` from the target repo"
    )


def check_workspace_disk_headroom() -> tuple[bool, str]:
    """Mirrors spawn.py's `_spawn_capacity_check(path)` gate (spawn.py:729-764,
    called at spawn.py:3229 before every workspace clone): observes the same
    `shutil.disk_usage()`/`os.statvfs()` headroom under the same default
    thresholds and the same env-var overrides, without creating, deleting, or
    cloning anything itself. `os.statvfs` is POSIX (present on both macOS and
    Linux, absent on native Windows -- same platform floor as the rest of
    this script)."""
    if os.environ.get("MUSTER_SKIP_SPACE_CHECK", "") not in ("", "0", "false", "no", "off"):
        return True, "MUSTER_SKIP_SPACE_CHECK set -- spawn.py's own gate is disabled"
    probe = Path.cwd()
    while not probe.exists():
        probe = probe.parent
    try:
        usage = shutil.disk_usage(probe)
    except OSError as exc:
        return False, f"cannot read disk usage at {probe}: {type(exc).__name__}: {exc}"
    min_bytes = int(os.environ.get("MUSTER_MIN_FREE_BYTES", MIN_FREE_BYTES_DEFAULT))
    if usage.free < min_bytes:
        return False, (
            f"{usage.free // (1024 * 1024)}MB free at {probe}, below the "
            f"{min_bytes // (1024 * 1024)}MB threshold"
        )
    try:
        st = os.statvfs(probe)
        free_inodes = st.f_favail
    except (OSError, AttributeError):
        return True, f"{usage.free // (1024 * 1024)}MB free at {probe} (inode count unavailable)"
    min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
    if free_inodes and free_inodes < min_inodes:
        return False, (
            f"{free_inodes} free inodes at {probe}, below the {min_inodes} threshold"
        )
    return True, f"{usage.free // (1024 * 1024)}MB free, {free_inodes or 'n/a'} free inodes at {probe}"


CHECKS = [
    {
        "name": "posix_fork_support",
        "fn": check_posix_fork,
        "remedy": (
            "Run on macOS or Linux (native Windows is unsupported -- use "
            "WSL); this interpreter lacks os.fork()/os.setsid() or is not "
            "reporting a supported sys.platform."
        ),
        "source": (
            "spawn.py:4639 (os.fork()/os.setsid() drives _spawn_one(), the "
            "real role-session spawn path); the same fork+setsid+dup2 "
            "pattern also appears at spawn.py:2668 (background "
            "validity-consult, a different feature that mirrors it)"
        ),
        "line_anchors": [
            ("spawn.py", 4639, "os.fork()"),
            ("spawn.py", 2668, "os.fork()"),
        ],
    },
    {
        "name": "claude_cli_on_path",
        "fn": check_claude_cli_present,
        "remedy": "Install the Claude Code CLI so `claude` resolves on PATH.",
        "source": (
            'pipeline.py:661 (spawn_cmd builds cmd = ["claude", "-p", ...]); '
            "spawn.py:4761 (_spawn_one() is what actually execs it, via "
            "subprocess.Popen(cmd, ...))"
        ),
        "line_anchors": [
            ("pipeline.py", 661, 'cmd = ["claude"'),
            ("spawn.py", 4761, "subprocess.Popen("),
        ],
    },
    {
        "name": "git_cli_on_path",
        "fn": check_git_cli_present,
        "remedy": "Install git so `git` resolves on PATH.",
        "source": 'pipeline.py:798 (subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"], ...))',
        "line_anchors": [
            ("pipeline.py", 798, 'subprocess.run(["git", "-C", cwd, "remote", "get-url"'),
        ],
    },
    {
        "name": "gh_cli_authenticated",
        "fn": check_gh_cli_authenticated,
        "remedy": "Run `gh auth login` with the account that should own spawns/PRs.",
        "source": 'plumbing.py:355 (subprocess.run(["gh", "auth", "token"], ...) inside _resolve_gh_token(), used by spawn_cmd to inject GH_TOKEN)',
        "line_anchors": [
            ("plumbing.py", 355, 'subprocess.run(["gh", "auth", "token"]'),
        ],
    },
    {
        "name": "git_identity_configured",
        "fn": check_git_identity_configured,
        "remedy": (
            'Run `git config --global user.name "<name>"` and '
            '`git config --global user.email "<email>"`.'
        ),
        "source": 'board.py:83-86 (subprocess.run(["git", "-C", str(root), "commit", ...]) in init --push, fails with empty ident if unset)',
        "line_anchors": [
            ("board.py", 83, 'subprocess.run(["git", "-C", str(root), "commit"'),
        ],
    },
    {
        "name": "skill_repository_resolvable",
        "fn": check_skill_repository_resolvable,
        "remedy": (
            "Clone the skill-repository sibling to $TOKENMAXXXER_RULEBOOKS "
            "(git clone https://github.com/tokenmaxxxer/skill-repository.git "
            "$TOKENMAXXXER_RULEBOOKS/skill-repository) or set "
            "MUSTER_SKILL_REPO=<checkout>/skills."
        ),
        "source": "skills.py:96-112 (_skill_repo_root: MUSTER_SKILL_REPO env > sibling clone > managed clone)",
        "line_anchors": [
            ("skills.py", 96, "def _skill_repo_root"),
        ],
    },
    {
        "name": "home_claude_skills_dir_present",
        "fn": check_home_claude_skills_dir_present,
        "remedy": (
            "Create ~/.claude/skills and populate it with the skills a "
            "spawned session should resolve locally -- no plugin install "
            "populates this directory."
        ),
        "source": "skills.py:338 (tier3 = _sp._local_skill_dirs(home / \".claude\" / \"skills\"))",
        "line_anchors": [
            ("skills.py", 338, '_local_skill_dirs(home / ".claude" / "skills")'),
        ],
    },
    {
        "name": "target_repo_board_file_present",
        "fn": check_target_repo_board_file_present,
        "remedy": (
            "From the target repo, run `python3 spawn.py init -C <repo>` "
            "to create docs/specs/approvers.md, then push it -- every spawn "
            "is refused admission until the remote default branch carries it."
        ),
        "source": "board.py:246-256 (require_board: exits if docs/specs/approvers.md is absent)",
        "line_anchors": [
            ("board.py", 246, "def require_board"),
        ],
    },
    {
        "name": "remote_push_access",
        "fn": check_remote_push_access,
        "remedy": (
            "Confirm manually that `origin` accepts a push of an "
            "issue-<n>/<skill> branch for the account gh is authenticated "
            "as -- this cannot be checked without a mutating write."
        ),
        "source": (
            "on-the-record/hooks/git-push-guard.sh:328 (_ROLE_BRANCH_RE.match(d), "
            "the primary enforcing logic that requires an issue-<n>/<skill> "
            "branch); line 341 carries the remedy text for the fail-closed "
            "edge case where the remote's default branch cannot be resolved"
        ),
        "line_anchors": [
            ("on-the-record/hooks/git-push-guard.sh", 328, "_ROLE_BRANCH_RE.match(d)"),
            ("on-the-record/hooks/git-push-guard.sh", 341,
             "push your own role branch instead"),
        ],
    },
    {
        "name": "workspace_disk_headroom",
        "fn": check_workspace_disk_headroom,
        "remedy": (
            "Free disk space and inodes before spawning -- spawn.py refuses "
            "to clone a workspace below its own default thresholds "
            "(~357MB free / 1000 free inodes), or override with "
            "MUSTER_MIN_FREE_BYTES / MUSTER_MIN_FREE_INODES / "
            "MUSTER_SKIP_SPACE_CHECK=1."
        ),
        "source": (
            "spawn.py:729-764 (_spawn_capacity_check: shutil.disk_usage() at "
            "spawn.py:740, sys.exit() at spawn.py:745 when free bytes fall "
            "below MIN_FREE_BYTES_DEFAULT, os.statvfs() inode check follows "
            "and sys.exit()s again if free inodes fall below "
            "MIN_FREE_INODES_DEFAULT) -- called at spawn.py:3229, before "
            "every workspace clone attempt"
        ),
        "line_anchors": [
            ("spawn.py", 729, "def _spawn_capacity_check"),
            ("spawn.py", 740, "shutil.disk_usage"),
            ("spawn.py", 745, "sys.exit("),
            ("spawn.py", 3229, "_spawn_capacity_check(work)"),
        ],
    },
]


def run_checks() -> list[dict]:
    results = []
    for c in CHECKS:
        try:
            ok, detail = c["fn"]()
        except Exception as exc:  # noqa: BLE001 -- a check must never
            # crash the whole preflight; an unexpected defect in one check
            # degrades that check to "missing", not to a silent skip.
            ok, detail = False, f"check raised {type(exc).__name__}: {exc}"
        ok = bool(ok)
        if ok:
            remedy = f"n/a -- already satisfied ({detail})" if detail else "n/a -- already satisfied"
        else:
            remedy = f"{c['remedy']} (observed: {detail})" if detail else c["remedy"]
        results.append({
            "name": c["name"],
            "satisfied": ok,
            "remedy": remedy,
            "source": c["source"],
        })
    return results


def emit_json(results: list[dict]) -> None:
    print(json.dumps({"preconditions": results}, indent=2))


def emit_human(results: list[dict]) -> None:
    print("on-the-record consumer-loop preflight")
    print("=" * 40)
    for r in results:
        mark = "OK  " if r["satisfied"] else "MISS"
        print(f"[{mark}] {r['name']}")
        print(f"       source: {r['source']}")
        if not r["satisfied"]:
            print(f"       remedy: {r['remedy']}")
        print()
    missing = [r for r in results if not r["satisfied"]]
    total = len(results)
    print(f"{total - len(missing)}/{total} preconditions satisfied.")
    if missing:
        print(f"{len(missing)} missing: {', '.join(r['name'] for r in missing)}")


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    results = run_checks()
    if as_json:
        emit_json(results)
    else:
        emit_human(results)
    return 0 if all(r["satisfied"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
