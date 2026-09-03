#!/usr/bin/env python3
"""Launcher-owned trust root for the R007 consumer-path on/off comparison
(issue #3183). Prepares the "on" (skill corpus reachable) and "off" (not
reachable) arms and writes a manifest recording what THIS process -- the
launcher, never the spawned session -- actually prepared, before either arm
is dispatched.

Replaces issue #3127's in-session toggle. That design's trust root was a
`Skill` tool_use line in the spawned session's own log
(`collect_skill_invocation()`, PR #3176) -- issue #3127's independent
verification (PR #3180) reproduced a spawned session forging that exact
line by appending it to its own log via Bash, live, with no sandboxing on
this machine to stop it (`spawn.py`'s `Popen()` carries no `preexec_fn` /
`user=` / uid drop). That PR also found the harness's own frontmatter-only
"skills-off" stub (`build_stub_skill_repo()`) gets invoked by every
off-arm run by construction, so the same signal could not tell a genuine
corpus leak apart from the harness's own stub being read as designed.

This module never creates a stub. The off arm's skills root is a path
that is never created at all -- `demonstrate_absence()` records that the
path does not exist, not merely an empty list asserted -- so there is
nothing there for a spawned process to read, stub or otherwise.

Both arms get an isolated, freshly created temporary HOME
(`tempfile.mkdtemp`, cleaned up by this process before it exits -- never a
previous run's HOME, never reused). The manifest records, per arm: the arm
name, the HOME path, the skills-root path, and for "on" every resolved
file under the skills root with its sha256; for "off" the scan that found
none and that scan's own recorded output. The manifest is written, then
its own bytes on disk are hashed and the digest is written to a sidecar
file alongside it (`<out>.sha256`) -- `verify_manipulation.py` (this issue)
recomputes that digest independently before trusting anything else in the
file.

`--dry-run` runs the exact same preparation (fresh HOMEs are still
created, the real skills root is still scanned) but only prints the
manifest as JSON on stdout -- nothing is persisted to `--out` and no
sidecar is written, so a smoke invocation leaves no durable file behind.
Every mode cleans up the temporary HOMEs it created before exiting; the
real (non-`--skills-root-on`-default) skills root, being external to this
process, is never touched or deleted.

Dispatch shape (documented, not invoked by this module -- issue #3053/
#3041's bare `claude -p` call is exactly what invalidated that earlier
measurement for this requirement; running the pairs is separate work,
scope note in issue #3183): `dispatch_command()` below builds the argv
each arm would actually be run with -- `python3 spawn.py --skills <name>
... --issue <n> -C <repo>`, spawn.py with an orchestrator, never a bare
`claude -p` -- and the two arms' argv lists are identical except for the
manipulated env (`HOME`, the skills-root pointer). That argv+env pair,
captured by the process that calls `Popen()` before the child can write
anything, is the "transport-level record" `verify_manipulation.py` checks
against this manifest.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

ARM_ON = "on"
ARM_OFF = "off"
SKILLS_ROOT_ENV_VAR = "MUSTER_SKILL_REPO"


class ArmPreparationError(Exception):
    """Raised when an arm cannot be prepared in a way that would make the
    manifest an honest record -- e.g. the declared "on" corpus is empty,
    or the "off" path turns out to already exist with files in it. Always
    fatal: there is no fallback value that would not risk reporting a
    manipulation that did not actually hold."""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_skill_files(skills_root: Path) -> list[dict]:
    """Recursive scan for regular files under `skills_root`. Portable:
    pathlib only, no `find`/GNU flags, no shelling out. Sorted by relative
    path for a deterministic manifest. Skips any path with a
    dot-prefixed component (`.git`, `.pytest_cache`, ...) -- volatile
    tooling artifacts that can sit inside a real checkout alongside the
    skill corpus, not skill content itself."""
    if not skills_root.is_dir():
        return []
    files = sorted(
        (p for p in skills_root.rglob("*")
         if p.is_file()
         and not any(part.startswith(".")
                     for part in p.relative_to(skills_root).parts)),
        key=lambda p: str(p.relative_to(skills_root)),
    )
    return [
        {
            "path": str(p.relative_to(skills_root)),
            "sha256": _sha256_file(p),
            "size_bytes": p.stat().st_size,
        }
        for p in files
    ]


def demonstrate_absence(skills_root: Path) -> dict:
    """Runs the identical scan `resolve_skill_files()` uses against the
    "off" arm's skills root and records the method plus its literal
    result -- the check that found nothing and that check's own output,
    not a bare `[]` written with no evidence behind it."""
    root_exists = skills_root.exists()
    found = resolve_skill_files(skills_root) if root_exists else []
    return {
        "method": "recursive Path.rglob('*') filtered to regular files "
                  "(resolve_skill_files())",
        "skills_root": str(skills_root),
        "skills_root_exists": root_exists,
        "files_found": found,
        "file_count": len(found),
    }


def dispatch_command(skill_name: str, model: str, issue_placeholder: str,
                      repo_placeholder: str) -> list[str]:
    """The argv an arm would actually be dispatched with -- spawn.py with
    an orchestrator (`--skills`), never a bare `claude -p` (the #3041/
    #3053 shortcut this issue's requirement names as invalidating). Held
    byte-identical across both arms; only the env (HOME, skills-root
    pointer) the caller supplies alongside this argv differs."""
    return [
        "python3", "spawn.py",
        "--skills", skill_name,
        "<task text, held constant across both arms>",
        "--issue", issue_placeholder,
        "--model", model,
        "-C", repo_placeholder,
    ]


def make_on_arm(home: Path, skills_root: Path) -> dict:
    skill_files = resolve_skill_files(skills_root)
    if not skill_files:
        raise ArmPreparationError(
            f"'on' arm's skills root {skills_root} resolved to zero "
            "files -- refusing to prepare an 'on' arm that is "
            "indistinguishable from 'off'; pass --skills-root-on at a "
            "populated skill-repository checkout")
    return {
        "arm": ARM_ON,
        "home": str(home),
        "skills_root": str(skills_root),
        "skill_files": skill_files,
        "absence_check": None,
    }


def make_off_arm(home: Path) -> dict:
    # Never created -- a path that does not exist is a stronger
    # demonstration of "not reachable" than an empty directory a stub
    # could later be written into, and there is nothing here to clean up.
    off_skills_root = Path(tempfile.gettempdir()) / (
        f"consumer-path-off-skills-absent-{uuid.uuid4().hex}")
    absence_check = demonstrate_absence(off_skills_root)
    if absence_check["file_count"] != 0 or absence_check["skills_root_exists"]:
        raise ArmPreparationError(
            f"'off' arm's skills root {off_skills_root} already exists "
            "or is non-empty -- refusing to report an absence that was "
            "not actually demonstrated")
    return {
        "arm": ARM_OFF,
        "home": str(home),
        "skills_root": str(off_skills_root),
        "skill_files": [],
        "absence_check": absence_check,
    }


def build_manifest(skills_root_on: Path, skill_name: str, model: str,
                    operator: str) -> tuple[dict, list[Path]]:
    """Returns (manifest, created_dirs) -- `created_dirs` is exactly the
    temporary HOMEs this call created, for the caller to clean up on
    success. Fails closed (raises `ArmPreparationError`) rather than
    emitting a manifest that does not honestly reflect what was
    prepared -- and on that failure path, cleans up whichever HOMEs it
    had already created before raising, so a rejected preparation never
    leaks a temp HOME either."""
    on_home = Path(tempfile.mkdtemp(prefix="consumer-path-on-home-"))
    off_home = Path(tempfile.mkdtemp(prefix="consumer-path-off-home-"))
    created_dirs = [on_home, off_home]
    try:
        on_arm = make_on_arm(on_home, skills_root_on)
        off_arm = make_off_arm(off_home)
        if on_arm["home"] == off_arm["home"]:
            raise ArmPreparationError(
                "on/off arms received the same HOME -- isolation "
                "invariant violated")
    except ArmPreparationError:
        _cleanup(created_dirs)
        raise

    argv = dispatch_command(skill_name, model, "<issue-created-per-arm>",
                             "<sandbox-repo>")
    manifest = {
        "issue": 3183,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "operator": operator,
        "skills_root_env_var": SKILLS_ROOT_ENV_VAR,
        "dispatch": {
            "argv_template": argv,
            "argv_identical_across_arms": True,
            "env_keys_that_differ_by_arm": ["HOME", SKILLS_ROOT_ENV_VAR],
            "note": "spawn.py with an orchestrator -- not a bare `claude "
                    "-p` (the #3041/#3053 shortcut this issue's floor "
                    "condition invalidated for this requirement)",
        },
        "arms": [on_arm, off_arm],
    }
    return manifest, created_dirs


def provision_credentials(home: Path, source_home: Path | None = None) -> dict:
    """Copy ONLY `~/.claude/.credentials.json` into an arm's isolated HOME.

    Nothing else -- no `settings.json`, no plugin or marketplace
    registration, no `.claude.json` -- so a `claude -p` call under this
    arm's freshly created HOME can authenticate without widening the trust
    root's isolation beyond auth itself.

    Two independent verifications traced R007's "0 of 5 pairs scored"
    outcome to exactly this gap: every arm's `claude -p` subprocess failed
    on "Not logged in" before any hook, and before the on/off skill
    manipulation, ever ran. `spawn.py doctor()`'s coarser check then
    reported it as a hook-firing regression -- a wrong diagnosis produced
    by a failure that never named itself.

    Returns paths and a verdict, never credential content: nothing here
    reaches the manifest, the transport record, or any committed artifact.
    A missing source file is reported rather than skipped -- the caller
    decides whether that is fatal to the pair; this function never
    fabricates success.
    """
    source_home = source_home or Path.home()
    source = source_home / ".claude" / ".credentials.json"
    if not source.is_file():
        return {"provisioned": False, "source": str(source),
                "reason": f"no credentials file at {source}"}
    dest_dir = home / ".claude"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ".credentials.json"
    dest.write_bytes(source.read_bytes())
    dest.chmod(0o600)
    return {"provisioned": True, "source": str(source), "dest": str(dest)}


def _cleanup(dirs: list[Path]) -> None:
    """Best-effort removal of this run's own temporary HOMEs. A failure
    here does not change the manifest already written, but is reported
    (not silently swallowed) since it means a temp HOME may be left
    behind for someone to clean up by hand."""
    import shutil
    for d in dirs:
        try:
            shutil.rmtree(d)
        except OSError as exc:
            print(f"warning: could not remove temporary HOME {d}: {exc}",
                  file=sys.stderr)


def render_manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skills-root-on", default=None,
                     help="populated skill corpus root for the 'on' arm; "
                          "defaults to $MUSTER_SKILL_REGISTRY_ROOT if unset")
    ap.add_argument("--skill-name", default="adversarial-review",
                     help="skill name held constant in both arms' "
                          "documented dispatch argv (illustrative only -- "
                          "this module never dispatches)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--operator", default=None,
                     help="who is running this launcher -- defaults to "
                          "the OS user; recorded verbatim in the "
                          "manifest (see docs/issue-3183/decisions/"
                          "instrument-limitations.md, operator-"
                          "independence limitation)")
    ap.add_argument("--out", default=None,
                     help="manifest file path (persisted mode only -- "
                          "required unless --dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                     help="prepare both arms and print the manifest as "
                          "JSON on stdout; nothing is written to --out "
                          "and no sidecar hash file is created")
    args = ap.parse_args()

    if not args.dry_run and not args.out:
        print("error: --out is required unless --dry-run is passed",
              file=sys.stderr)
        return 2

    import os
    skills_root_on = Path(
        args.skills_root_on
        or os.environ.get("MUSTER_SKILL_REGISTRY_ROOT")
        or "")
    if not str(skills_root_on):
        print("error: --skills-root-on not given and "
              "$MUSTER_SKILL_REGISTRY_ROOT is not set -- refusing to "
              "guess a skills root for the 'on' arm", file=sys.stderr)
        return 2

    operator = args.operator or getpass.getuser()

    created_dirs: list[Path] = []
    try:
        manifest, created_dirs = build_manifest(
            skills_root_on, args.skill_name, args.model, operator)
    except ArmPreparationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        _cleanup(created_dirs)

    if args.dry_run:
        manifest_text = render_manifest_json(manifest)
        manifest_with_hash = dict(manifest)
        manifest_with_hash["manifest_sha256"] = _sha256_bytes(
            manifest_text.encode("utf-8"))
        print(json.dumps(manifest_with_hash, indent=2, sort_keys=True))
        return 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_text = render_manifest_json(manifest)
    out_path.write_text(manifest_text, encoding="utf-8")
    digest = _sha256_bytes(out_path.read_bytes())
    sidecar_path = Path(str(out_path) + ".sha256")
    sidecar_path.write_text(digest + "\n", encoding="utf-8")
    print(f"wrote {out_path} (sha256 {digest}, sidecar {sidecar_path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
