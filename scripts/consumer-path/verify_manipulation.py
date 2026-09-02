#!/usr/bin/env python3
"""Fail-closed manipulation check for the R007 consumer-path trust root
(issue #3183). Decides whether a pair's on/off manipulation actually held.

Reads exactly two artifacts, both launcher-owned and written before the
paired arms were ever dispatched:

  1. the manifest `prepare_arms.py` wrote (plus its sha256 sidecar,
     `<manifest>.sha256`, checked here before anything else in the file
     is trusted), and
  2. a transport record: the argv and environment a dispatching process
     actually handed to each arm's subprocess, captured by that
     dispatching process itself before it called `Popen()` -- see
     `prepare_arms.py`'s `dispatch_command()` docstring for the contract
     this file must satisfy.

Every other artifact this issue considered and rejected as evidence is
enumerated in the accompanying record
(docs/issue-3183/reports/experiment-trust+implementation-blueprint+
silent-failure-audit-ab4333e5.md) with the reason each one is forgeable
by the spawned process itself -- issue #3127's PR #3180 already
demonstrated this live for the previous design's own signal (a `Skill`
tool_use line appended by Bash to the spawned process's own runtime
output, spawn.py's Popen carrying no uid drop to stop it). Nothing this
module opens can be written by anything other than the process that ran
this pair's launcher.

Fails closed on every path: a missing manifest, a missing transport
record, a sidecar hash mismatch, a malformed or incomplete transport
record, or a mismatch between what the manifest declared and what the
transport record shows was actually sent excludes the pair and exits
nonzero. There is no fallback path -- a check that cannot be completed
is reported as failed, never silently skipped or passed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


class VerificationFailure(Exception):
    """Raised for every fail-closed condition this module checks. The
    message is the exclusion reason reported back to the caller -- never
    caught and retried with a fallback value."""


def load_manifest(manifest_path: Path) -> tuple[dict, bytes]:
    if not manifest_path.is_file():
        raise VerificationFailure(
            f"manifest not found at {manifest_path} -- pair excluded")
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise VerificationFailure(
            f"manifest at {manifest_path} could not be read ({exc}) -- "
            "pair excluded") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationFailure(
            f"manifest at {manifest_path} is not valid JSON ({exc}) -- "
            "pair excluded") from exc
    return manifest, raw


def verify_manifest_integrity(manifest_path: Path, raw: bytes) -> None:
    sidecar_path = Path(str(manifest_path) + ".sha256")
    if not sidecar_path.is_file():
        raise VerificationFailure(
            f"manifest hash sidecar not found at {sidecar_path} -- "
            "pair excluded (a manifest with no recorded hash cannot be "
            "trusted against tampering or partial writes)")
    try:
        recorded = sidecar_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as exc:
        raise VerificationFailure(
            f"manifest hash sidecar at {sidecar_path} could not be read "
            f"({exc}) -- pair excluded") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if recorded != actual:
        raise VerificationFailure(
            f"manifest hash mismatch at {manifest_path}: sidecar records "
            f"{recorded!r}, recomputed {actual!r} -- pair excluded "
            "(the manifest file was modified after prepare_arms.py wrote "
            "it, or the sidecar itself does not match)")


def load_transport_record(transport_path: Path) -> dict:
    if not transport_path.is_file():
        raise VerificationFailure(
            f"transport record not found at {transport_path} -- pair "
            "excluded (with no record of what was actually dispatched, "
            "a manifest alone proves only what was prepared, never what "
            "was sent)")
    try:
        raw = transport_path.read_text(encoding="utf-8")
        record = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationFailure(
            f"transport record at {transport_path} could not be read "
            f"as JSON ({exc}) -- pair excluded") from exc
    return record


def _arm_by_name(manifest: dict, name: str) -> dict:
    matches = [a for a in manifest.get("arms", []) if a.get("arm") == name]
    if len(matches) != 1:
        raise VerificationFailure(
            f"manifest does not contain exactly one '{name}' arm "
            f"(found {len(matches)}) -- pair excluded")
    return matches[0]


def cross_check(manifest: dict, transport: dict) -> None:
    """Compares the manifest's own arms against the transport record's
    argv/env for each arm. Nothing here reads any path off disk -- both
    inputs are already fully in memory as plain dicts by this point."""
    on_arm = _arm_by_name(manifest, "on")
    off_arm = _arm_by_name(manifest, "off")

    if on_arm["home"] == off_arm["home"]:
        raise VerificationFailure(
            "manifest's on/off arms share a HOME -- isolation invariant "
            "violated, pair excluded")
    if on_arm["skill_files"] == [] or off_arm["skill_files"] != []:
        raise VerificationFailure(
            "manifest does not show the manipulated variable in the "
            "expected direction (on arm must have resolved skill files, "
            "off arm must have none) -- pair excluded")

    root_env_var = manifest.get("skills_root_env_var")
    if not root_env_var:
        raise VerificationFailure(
            "manifest does not name skills_root_env_var -- cannot check "
            "the transport record's environment against it, pair "
            "excluded")

    transport_arms = transport.get("arms")
    if not isinstance(transport_arms, dict):
        raise VerificationFailure(
            "transport record has no 'arms' object -- pair excluded")

    for arm in (on_arm, off_arm):
        name = arm["arm"]
        sent = transport_arms.get(name)
        if not isinstance(sent, dict):
            raise VerificationFailure(
                f"transport record has no entry for arm '{name}' -- "
                "pair excluded")
        argv = sent.get("argv")
        env = sent.get("env")
        if not isinstance(argv, list) or not argv:
            raise VerificationFailure(
                f"transport record's argv for arm '{name}' is missing "
                "or empty -- pair excluded")
        if not any(str(a).endswith("spawn.py") for a in argv):
            raise VerificationFailure(
                f"transport record's argv for arm '{name}' does not "
                "invoke spawn.py -- the #3041/#3053 bare-CLI shortcut "
                "this issue's requirement names as invalidating that "
                "measurement, pair excluded")
        if not isinstance(env, dict):
            raise VerificationFailure(
                f"transport record's env for arm '{name}' is missing -- "
                "pair excluded")
        if env.get("HOME") != arm["home"]:
            raise VerificationFailure(
                f"transport record's HOME for arm '{name}' "
                f"({env.get('HOME')!r}) does not match the manifest's "
                f"prepared HOME ({arm['home']!r}) -- the manipulation "
                "the manifest describes is not what was actually sent, "
                "pair excluded")
        if env.get(root_env_var) != arm["skills_root"]:
            raise VerificationFailure(
                f"transport record's {root_env_var} for arm '{name}' "
                f"({env.get(root_env_var)!r}) does not match the "
                f"manifest's prepared skills_root ({arm['skills_root']!r}"
                ") -- the manipulation the manifest describes is not "
                "what was actually sent, pair excluded")


def verify(manifest_path: Path, transport_path: Path) -> dict:
    manifest, raw = load_manifest(manifest_path)
    verify_manifest_integrity(manifest_path, raw)
    transport = load_transport_record(transport_path)
    cross_check(manifest, transport)
    return {
        "manipulation_held": True,
        "pair_excluded": False,
        "manifest": str(manifest_path),
        "transport": str(transport_path),
        "arms_checked": ["on", "off"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--transport", required=True, type=Path)
    args = ap.parse_args()

    try:
        verdict = verify(args.manifest, args.transport)
    except VerificationFailure as exc:
        verdict = {
            "manipulation_held": False,
            "pair_excluded": True,
            "reason": str(exc),
            "manifest": str(args.manifest),
            "transport": str(args.transport),
        }
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 1
    except Exception as exc:  # last-resort fail-closed: an unexpected
        # error must still exclude the pair and report why, never exit
        # 0 or print a manipulation_held verdict by falling through.
        verdict = {
            "manipulation_held": False,
            "pair_excluded": True,
            "reason": f"unexpected error during verification: {exc!r}",
            "manifest": str(args.manifest),
            "transport": str(args.transport),
        }
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 1

    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
