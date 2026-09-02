#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3049.

Issue #3049 named four bash shapes that walk a session's cwd past
`gate-registration-guard.sh`'s PreToolUse `--cached` read without that
guard noticing: bare `pushd` (no argument), `pushd +N`/`-N` (stack
rotation), an env-var-prefixed `cd` (`FOO=bar cd ..`), and `$CDPATH`.
Nobody had run them against `gate-registration-post-guard.sh` -- the
issue #2705 post-commit report that is supposed to catch the bundled
`git add ... && git commit ...` shape regardless of how the cwd got
there, because it reads git's own `[<branch> <sha>] <subject>` commit
line and inspects that exact commit's tree via `git show`, never the
pre-command `--cached` state or the command text's own cwd modelling.

This script exercises each shape for real: a fresh scratch git repo,
the real bash builtin (`pushd`, `cd`, `CDPATH`) actually moving the
cwd, a real `git add && git commit` bundled in one shell invocation,
independent ground truth that the file was genuinely staged (`git log
-1 --name-status`), and then the *actual* `gate-registration-post-guard.sh`
script (unmodified, `post` then `pre` mode) fed the real captured
commit output as its `tool_response`. It asserts the DOCUMENTED status
below for each shape, so it fails in either direction: a caught shape
silently becoming uncaught, or an uncaught one being quietly closed
without docs/issue-3049's record being updated.

Run as `python3 gates/probe_cwd_shapes.py` from the repo root, no
arguments. Prints one line per shape and `ok` on success; prints `FAIL`
lines and exits non-zero on any mismatch or setup failure.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POST_GUARD = REPO_ROOT / "on-the-record" / "hooks" / "gate-registration-post-guard.sh"

_SHA_RE = re.compile(
    r"^\[\S+(?:\s+\(root-commit\))?\s+([0-9a-fA-F]{4,40})\]", re.MULTILINE
)

# Documented in docs/issue-3049/reports/... : all four shapes are CAUGHT
# by the post-commit companion. The companion never re-derives the cwd at
# all -- it greps the commit sha out of `tool_response` and inspects that
# commit's own tree, so a cwd-modelling escape at PreToolUse time has no
# effect on it. Kept here as data (not inferred at run time) so a future
# change to either hook that flips a shape's outcome fails this probe
# instead of passing silently.
DOCUMENTED_STATUS = {
    "bare-pushd": "caught",
    "pushd-plusN": "caught",
    "env-prefixed-cd": "caught",
    "cdpath": "caught",
}


def _run(cmd, cwd, env=None, input_text=None):
    return subprocess.run(
        cmd, cwd=str(cwd), env=env, input=input_text,
        capture_output=True, text=True, timeout=30,
    )


def _make_scratch_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    (repo / "gates").mkdir()
    _run(["git", "init", "-q"], cwd=repo)
    _run(["git", "config", "user.email", "probe@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "probe"], cwd=repo)
    (repo / "README.md").write_text("scratch repo for gates/probe_cwd_shapes.py\n")
    _run(["git", "add", "README.md"], cwd=repo)
    r = _run(["git", "commit", "-q", "-m", "init"], cwd=repo)
    if r.returncode != 0:
        raise RuntimeError(f"scratch repo init commit failed: {r.stderr}")
    return repo


def _setup_bare_pushd(root: Path, repo: Path) -> None:
    (repo / "sub").mkdir()
    (repo / "gates" / "probe_bare_pushd.py").write_text("# probe\n")


def _setup_pushd_plusn(root: Path, repo: Path) -> None:
    (repo / "pn_a").mkdir()
    (repo / "gates" / "probe_pushd_plusn.py").write_text("# probe\n")


def _setup_env_prefixed_cd(root: Path, repo: Path) -> None:
    (repo / "envprefix_sub").mkdir()
    (repo / "gates" / "probe_envprefix.py").write_text("# probe\n")


def _setup_cdpath(root: Path, repo: Path) -> None:
    cdpath_target = root / "cdpath_target"
    cdpath_target.mkdir()
    (cdpath_target / "back").symlink_to(repo, target_is_directory=True)
    (repo / "gates" / "probe_cdpath.py").write_text("# probe\n")


SHAPES = [
    {
        "name": "bare-pushd",
        "setup": _setup_bare_pushd,
        # real bash: bare `pushd` (no argument) swaps the top two stack
        # entries and cds into the new top -- not a no-op.
        "command": (
            "pushd sub >/dev/null && pushd >/dev/null && "
            "git add gates/probe_bare_pushd.py && "
            "git commit -m add_probe_bare_pushd"
        ),
        "added_path": "gates/probe_bare_pushd.py",
    },
    {
        "name": "pushd-plusN",
        "setup": _setup_pushd_plusn,
        # real bash: `pushd +1` rotates stack index 1 to the top and cds
        # there.
        "command": (
            "pushd pn_a >/dev/null && pushd +1 >/dev/null && "
            "git add gates/probe_pushd_plusn.py && "
            "git commit -m add_probe_pushd_plusn"
        ),
        "added_path": "gates/probe_pushd_plusn.py",
    },
    {
        "name": "env-prefixed-cd",
        "setup": _setup_env_prefixed_cd,
        # real bash: a per-command env-var assignment prefix on `cd`
        # (`FOO=bar cd ..`) still really changes directory.
        "command": (
            "cd envprefix_sub && FOO=bar cd .. && "
            "git add gates/probe_envprefix.py && "
            "git commit -m add_probe_envprefix"
        ),
        "added_path": "gates/probe_envprefix.py",
    },
    {
        "name": "cdpath",
        "setup": _setup_cdpath,
        # real bash: `$CDPATH` is consulted for a plain `cd` target name
        # that does not exist relative to cwd, cd-ing through a
        # CDPATH-resolved symlink instead.
        "command": (
            "export CDPATH=" + "__CDPATH_TARGET__" + " && cd back && "
            "git add gates/probe_cdpath.py && "
            "git commit -m add_probe_cdpath"
        ),
        "added_path": "gates/probe_cdpath.py",
    },
]


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)


def run_shape(shape: dict, tmp_root: Path) -> dict:
    shape_root = tmp_root / shape["name"]
    repo = _make_scratch_repo(shape_root)
    shape["setup"](shape_root, repo)

    command = shape["command"]
    if shape["name"] == "cdpath":
        command = command.replace("__CDPATH_TARGET__", str(shape_root / "cdpath_target"))

    result = _run(["bash", "-c", command], cwd=repo)
    if result.returncode != 0:
        return {
            "name": shape["name"], "ok": False,
            "reason": f"bundled command exited {result.returncode}: {result.stderr.strip()}",
        }
    commit_stdout = result.stdout

    # Ground truth #1: the file is genuinely staged and committed by real
    # git, independent of anything the hook itself later reports.
    show = _run(["git", "log", "-1", "--name-status", "--format="], cwd=repo)
    staged_lines = [l for l in show.stdout.splitlines() if l.strip()]
    genuinely_staged = any(
        l.startswith("A") and shape["added_path"] in l for l in staged_lines
    )
    if not genuinely_staged:
        return {
            "name": shape["name"], "ok": False,
            "reason": (
                "not-reproducible: bundled command ran and committed, but "
                f"real git's own `git log -1 --name-status` does not show "
                f"{shape['added_path']} as added -- attempt: {command!r}, "
                f"commit stdout: {commit_stdout!r}"
            ),
        }

    m = _SHA_RE.search(commit_stdout)
    if not m:
        return {
            "name": shape["name"], "ok": False,
            "reason": (
                "not-reproducible: git commit succeeded but its stdout did "
                f"not carry the `[<branch> <sha>] <subject>` line the "
                f"companion parses -- stdout: {commit_stdout!r}"
            ),
        }
    abbrev_sha = m.group(1)

    state_dir = shape_root / "state"
    state_dir.mkdir()
    session_id = f"probe-{shape['name']}"
    env = dict(os.environ)
    env["OTR_GRG_POST_STATE_DIR"] = str(state_dir)
    # Force the hook's own kill switch off regardless of the ambient
    # environment this probe happens to run in -- an inherited
    # ORCHESTRATE_OFF=1 would make every shape look "uncaught" for a
    # reason that has nothing to do with the companion's own cwd
    # handling, and silently at that (issue #3049's own silent-failure-
    # audit skill call: a copied ambient env is exactly the kind of
    # catch-and-continue that hides the real cause).
    env["ORCHESTRATE_OFF"] = "0"

    post_payload = json.dumps({
        "session_id": session_id,
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": command},
        "tool_response": commit_stdout,
    })
    post_res = _run(["bash", str(POST_GUARD), "post"], cwd=repo, env=env, input_text=post_payload)
    if post_res.returncode != 0:
        # gate-registration-post-guard.sh's own header comment documents
        # `post` mode as pure side-effect, always exit 0 -- a non-zero
        # exit here is itself a finding, not something to paper over by
        # falling through to the pre-mode check as if nothing happened.
        return {
            "name": shape["name"], "ok": False,
            "reason": (
                f"post-guard 'post' mode exited {post_res.returncode} "
                f"(expected 0 per its own contract) -- stderr: "
                f"{post_res.stderr!r}"
            ),
        }

    pre_payload = json.dumps({
        "session_id": session_id, "tool_name": "Bash", "cwd": str(repo),
    })
    pre_res = _run(["bash", str(POST_GUARD), "pre"], cwd=repo, env=env, input_text=pre_payload)
    if pre_res.returncode != 0:
        return {
            "name": shape["name"], "ok": False,
            "reason": (
                f"post-guard 'pre' mode exited {pre_res.returncode} -- "
                f"stderr: {pre_res.stderr!r}"
            ),
        }

    report_text = ""
    parse_error = None
    if pre_res.stdout.strip():
        try:
            out = json.loads(pre_res.stdout)
            report_text = out.get("hookSpecificOutput", {}).get("additionalContext", "")
        except json.JSONDecodeError as exc:
            parse_error = f"{exc} -- raw stdout: {pre_res.stdout!r}"

    caught = bool(report_text) and abbrev_sha in report_text and shape["added_path"] in report_text

    return {
        "name": shape["name"],
        "ok": True,
        "status": "caught" if caught else "uncaught",
        "parse_error": parse_error,
        "commit_stdout": commit_stdout.strip(),
        "post_exit": post_res.returncode,
        "report_text": report_text,
    }


def main() -> None:
    tmp_root = Path(tempfile.mkdtemp(prefix="otr-probe-cwd-shapes-"))
    failures = []
    try:
        for shape in SHAPES:
            documented = DOCUMENTED_STATUS[shape["name"]]
            try:
                result = run_shape(shape, tmp_root)
            except Exception as exc:  # noqa: BLE001 - report, don't crash silently
                failures.append(f"{shape['name']}: setup/run raised {exc!r}")
                print(f"{shape['name']}: ERROR {exc!r}")
                continue

            if not result["ok"]:
                # A shape that cannot be reproduced against current bash is
                # recorded as not-reproducible with the attempt shown, never
                # silently dropped -- but that is itself a mismatch against
                # a documented "caught"/"uncaught" status and must fail loud.
                print(f"{shape['name']}: {result['reason']}")
                failures.append(f"{shape['name']}: {result['reason']}")
                continue

            actual = result["status"]
            print(
                f"{shape['name']}: documented={documented} actual={actual} "
                f"commit={result['commit_stdout'].splitlines()[0] if result['commit_stdout'] else ''!r}"
            )
            if actual != documented:
                detail = result["report_text"] or result.get("parse_error") or "(empty)"
                failures.append(
                    f"{shape['name']}: documented status {documented!r} but this run "
                    f"observed {actual!r} -- companion report: {detail!r}"
                )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    if failures:
        for f in failures:
            _fail(f)
        sys.exit(1)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
