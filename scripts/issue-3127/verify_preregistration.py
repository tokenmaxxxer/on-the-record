#!/usr/bin/env python3
"""Assert that docs/issue-3127/decisions/pre-registration.md was committed
before docs/issue-3127/_assets/consumer-path-results.json (issue #3127
acceptance check) -- by commit order (git ancestry) or, when that ordering
has been collapsed by a squash-merge, by the originating PR's own
pre-squash commit history (see `_resolve_via_pr_history`) -- never by
comparing timestamp fields inside either file, which either file's own
content could misstate. Same control #3053 used (`git log` on the branch,
absence of `_assets` at the pre-registration commit) and the reason its
null was credible: a threshold set after seeing the result is not a
threshold.

Why the fallback exists: this repo lands every PR with `--squash`. PR
#3131 introduced both files in one squash-merge commit (fb0bb0d3), so on
main and on any branch cut from main, `git log --diff-filter=A` finds the
same "first commit" for both paths and the plain ancestry check can never
tell them apart again -- it would fail on every future branch by
construction, not just this one. `gh pr view <n> --json commits` still
returns PR #3131's original, un-squashed commit list (GitHub keeps it on
the PR object itself, independent of what the merge collapsed it to on
main), so that list is used to recover the true order for exactly the
collision case. Any future branch's own genuinely-new results commit
(distinct from the one that added the file) is unaffected by this and is
still verified by plain ancestry, no PR lookup involved.

Usage: python3 scripts/issue-3127/verify_preregistration.py [--repo-root PATH]
Exit 0 and prints "OK: ..." if the pre-registration precedes the results,
whether resolved by ancestry or by the PR-history fallback. Exit 1 with a
reason otherwise -- including when evidence needed for the fallback
(the `verification_pr` field, `gh`, or the PR's own commit/file history)
is unavailable. Unavailable evidence is a failure, never a pass.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

import yaml

PREREG_PATH = "docs/issue-3127/decisions/pre-registration.md"
RESULTS_PATH = "docs/issue-3127/_assets/consumer-path-results.json"

GhRunner = Callable[[list], "subprocess.CompletedProcess"]


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root), *args],
                           capture_output=True, text=True)


def _default_gh_runner(args: list) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def _first_commit_for_path(repo_root: Path, path: str) -> Optional[str]:
    """Oldest commit (across all local history reachable from HEAD, since
    build-now sessions commit directly on their own branch rather than
    landing to main first) that introduces `path`. Empty result means the
    path has no commit yet -- e.g. it exists only as an uncommitted working
    -tree file, which this check treats as "not yet registered."
    """
    r = _run_git(repo_root, "log", "--diff-filter=A", "--follow",
                 "--format=%H", "--reverse", "--", path)
    if r.returncode != 0:
        return None
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def _read_frontmatter(text: str) -> dict:
    """Parse the leading `---`-delimited YAML frontmatter block. Returns {}
    if there is no such block or it does not parse as a mapping -- callers
    treat a missing field the same as a missing block (fail closed)."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _repo_owner_repo(gh_runner: GhRunner) -> Optional[str]:
    r = gh_runner(["repo", "view", "--json", "nameWithOwner",
                   "-q", ".nameWithOwner"])
    if r.returncode != 0:
        return None
    name = r.stdout.strip()
    return name or None


def _pr_merge_commit(pr_number: int, gh_runner: GhRunner) -> Optional[str]:
    """The commit sha GitHub recorded as `pr_number`'s own merge commit --
    for a squash-merged PR this IS the single commit that lands on main,
    so it is the value an attacker cannot forge by naming an arbitrary PR
    number in `verification_pr:`: doing so would require GitHub to report
    a real, already-merged PR as having produced the attacker's own
    fabricated local commit. None if the PR has no recorded merge commit
    (not merged yet, or `gh` failed) -- fail closed at the caller."""
    r = gh_runner(["pr", "view", str(pr_number), "--json", "mergeCommit"])
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    merge_commit = data.get("mergeCommit") if isinstance(data, dict) else None
    oid = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
    return oid if isinstance(oid, str) and oid else None


def _pr_commit_order(pr_number: int, gh_runner: GhRunner) -> Optional[list]:
    """Ordered (oldest-first) list of commit SHAs GitHub recorded for
    `pr_number`, from the PR object's own commit list -- this survives a
    later squash-merge because GitHub retains it independent of the repo's
    post-merge ref graph. None on any failure (fail closed at the caller,
    never treated as "no violation found")."""
    r = gh_runner(["pr", "view", str(pr_number), "--json", "commits"])
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    commits = data.get("commits") if isinstance(data, dict) else None
    if not isinstance(commits, list) or not commits:
        return None
    shas = [c.get("oid") if isinstance(c, dict) else None for c in commits]
    if any(not isinstance(s, str) or not s for s in shas):
        return None
    return shas


def _first_pr_commit_touching(owner_repo: str, shas: list, path: str,
                               gh_runner: GhRunner) -> Optional[int]:
    """Index into `shas` of the first commit whose changed-file list
    includes `path`, resolved via the GitHub commits API rather than local
    git -- the PR's branch objects are not guaranteed to still be locally
    fetchable. None if no commit touches `path`, or on any lookup failure
    (fail closed at the caller)."""
    for i, sha in enumerate(shas):
        r = gh_runner(["api", f"repos/{owner_repo}/commits/{sha}",
                       "--jq", ".files[].filename"])
        if r.returncode != 0:
            return None
        if path in r.stdout.splitlines():
            return i
    return None


def _resolve_via_pr_history(repo_root: Path, colliding_commit: str,
                             gh_runner: GhRunner) -> tuple[bool, str]:
    """Fallback for the case where PREREG_PATH and RESULTS_PATH were both
    first introduced in the same local commit (`colliding_commit`) -- the
    squash-merge collapse this check exists to survive. Resolves the true
    pre-squash order from the originating PR's own commit history instead
    of failing outright. Every missing field, gh error, or unresolved
    lookup is a failure, never a pass -- there is no code path here that
    returns True without a strictly-ordered pair of indices actually
    observed.

    `verification_pr:` is attacker-controlled working-tree content (it
    lives in PREREG_PATH itself), so naming a PR number alone proves
    nothing -- any PR whose own history happens to touch both paths in
    the right order would otherwise pass regardless of whether it ever
    produced `colliding_commit`. The bind below closes that: the named
    PR's own recorded merge commit (immutable, GitHub-side history the
    working tree cannot rewrite) must equal `colliding_commit` before its
    pre-squash commit list is trusted at all. That equality -- not the
    pin itself -- is the actual trust root; the pin is now only a lookup
    key naming which PR to check, and a forged pin fails this bind
    because the attacker cannot make GitHub misreport a real PR's merge
    commit."""
    frontmatter = _read_frontmatter((repo_root / PREREG_PATH).read_text())
    pr_number = frontmatter.get("verification_pr")
    if not isinstance(pr_number, int):
        return False, (
            f"{PREREG_PATH} and {RESULTS_PATH} were introduced in the same "
            "commit (squash-merge collapse) and the pre-registration file "
            "carries no integer `verification_pr:` frontmatter field to "
            "resolve the true pre-squash order against -- cannot verify "
            "ordering")

    merge_commit = _pr_merge_commit(pr_number, gh_runner)
    if merge_commit is None:
        return False, (
            f"PR #{pr_number} has no recorded merge commit (`gh pr view "
            f"{pr_number} --json mergeCommit` failed or returned none) -- "
            "cannot confirm it actually produced the colliding commit "
            f"{colliding_commit}, so its history cannot be trusted")
    if merge_commit != colliding_commit:
        return False, (
            f"PR #{pr_number}'s merge commit ({merge_commit}) does not "
            f"match the colliding commit under review ({colliding_commit})"
            f" -- `verification_pr: {pr_number}` does not name the PR "
            "that actually produced this commit, so its history cannot "
            "be trusted to explain it")

    owner_repo = _repo_owner_repo(gh_runner)
    if owner_repo is None:
        return False, ("could not resolve the GitHub owner/repo (`gh repo "
                        "view` failed) -- cannot query PR "
                        f"#{pr_number}'s commit history")

    shas = _pr_commit_order(pr_number, gh_runner)
    if shas is None:
        return False, (f"`gh pr view {pr_number} --json commits` failed or "
                        "returned no commits -- cannot resolve the "
                        "pre-squash order (fail closed: unavailable "
                        "evidence is not a pass)")

    prereg_idx = _first_pr_commit_touching(owner_repo, shas, PREREG_PATH,
                                            gh_runner)
    results_idx = _first_pr_commit_touching(owner_repo, shas, RESULTS_PATH,
                                             gh_runner)
    if prereg_idx is None or results_idx is None:
        missing = ("both files" if prereg_idx is None and results_idx is None
                   else (PREREG_PATH if prereg_idx is None else RESULTS_PATH))
        return False, (
            f"PR #{pr_number}'s commit history has no commit touching "
            f"{missing} (or the lookup failed) -- cannot resolve ordering "
            "(fail closed)")

    if prereg_idx < results_idx:
        return True, (
            f"OK: same-commit collapse resolved via PR #{pr_number}'s own "
            f"pre-squash commit history -- {PREREG_PATH} first appears at "
            f"commit index {prereg_idx} ({shas[prereg_idx]}), "
            f"{RESULTS_PATH} at index {results_idx} ({shas[results_idx]}), "
            "strictly earlier")

    return False, (
        f"PR #{pr_number}'s own pre-squash commit history does NOT show "
        f"{PREREG_PATH} strictly before {RESULTS_PATH} (indices "
        f"{prereg_idx} vs {results_idx}) -- the pre-registration did not "
        "precede the results even before the squash collapsed the "
        "ordering on this branch")


def verify(repo_root: Path,
           gh_runner: GhRunner = _default_gh_runner) -> tuple[bool, str]:
    prereg_full = repo_root / PREREG_PATH
    results_full = repo_root / RESULTS_PATH
    if not prereg_full.exists():
        return False, f"missing: {PREREG_PATH} does not exist -- nothing to verify order against"
    if not results_full.exists():
        return False, f"missing: {RESULTS_PATH} does not exist -- nothing to verify order against"

    prereg_commit = _first_commit_for_path(repo_root, PREREG_PATH)
    results_commit = _first_commit_for_path(repo_root, RESULTS_PATH)

    if prereg_commit is None and results_commit is None:
        return False, ("neither file has a commit yet (both uncommitted in "
                        "the working tree) -- commit the pre-registration "
                        "first, then the results, so this check has "
                        "ancestry to verify")
    if prereg_commit is None:
        return False, (f"{PREREG_PATH} is uncommitted while {RESULTS_PATH} "
                        f"is committed ({results_commit}) -- the "
                        "pre-registration must land in a commit that "
                        "precedes the results commit")
    if results_commit is None:
        # Pre-registration committed, results file present only in the
        # working tree (e.g. this same uncommitted session) -- order is
        # trivially satisfied: nothing committed for results yet that
        # could have preceded the pre-registration.
        return True, (f"OK: {PREREG_PATH} committed at {prereg_commit}; "
                       f"{RESULTS_PATH} not yet committed (working tree "
                       "only), so it cannot precede the pre-registration")

    if prereg_commit == results_commit:
        # Both files were first added in the same commit on this branch's
        # own history -- either a genuine same-commit write, or (as on
        # this issue) a squash-merge that collapsed a real two-commit
        # order into one. Local ancestry cannot tell these apart anymore;
        # resolve via the originating PR's own pre-squash history instead
        # of assuming either outcome.
        return _resolve_via_pr_history(repo_root, prereg_commit, gh_runner)

    is_ancestor = _run_git(repo_root, "merge-base", "--is-ancestor",
                            prereg_commit, results_commit)
    if is_ancestor.returncode == 0:
        return True, (f"OK: pre-registration commit {prereg_commit} is an "
                       f"ancestor of results commit {results_commit}")
    if is_ancestor.returncode == 1:
        return False, (f"pre-registration commit {prereg_commit} is NOT an "
                        f"ancestor of results commit {results_commit} -- "
                        "either unrelated history or the results were "
                        "committed first")
    # `git merge-base --is-ancestor` returns >1 for a real git error (bad
    # object, not a commit, etc.), not for "not an ancestor" -- reporting
    # that uniformly as "not an ancestor" would silently misclassify a git
    # failure as a normal negative verification result.
    return False, (f"git merge-base --is-ancestor errored (exit "
                    f"{is_ancestor.returncode}), not a normal ancestry "
                    f"negative -- stderr: {is_ancestor.stderr.strip()}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    ok, message = verify(Path(args.repo_root).resolve())
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
