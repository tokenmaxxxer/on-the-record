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

Issue #3280 (round 7): an absent-path off arm no longer runs. Commit
`da92fb8e` (issue #3277) closed the fallback that used to let a
nonexistent `MUSTER_SKILL_REPO` silently resolve to the always-populated
managed clone -- the leak this trust root exists to close. Fixing that
leak also removed the off arm's ability to dispatch at all: with no
repo, `--skills <name>` cannot resolve the name, and `spawn.py` refuses
to dispatch before either arm ever runs. Verified live on #3280: an
empty-but-present skills root does not help either -- the refusal is
about the name failing to resolve, not about the directory existing.

So the off arm's skills root is now a same-named DECOY: a fresh
directory containing `<skill_name>/SKILL.md` with only the real skill's
`name:` field carried over (so the name resolves and spawn.py
dispatches) and a placeholder `description:` in place of the real one
-- no body guidance, and (round 8 correction) no verbatim
`description:`/`metadata:` either, since those fields are themselves
most of what a rubric-scored task measures. `make_off_arm()` fails
closed if the decoy would be byte-identical to the real file (a
front-matter-only real skill has no body to strip).

Round 8, mid-flight correction: the on arm used to mount the entire
skill registry (352 files against the off arm's 1), so a scored
difference could not be attributed to the one skill under test. The on
arm's skills root is now built the same way as the off arm's -- a
fresh temp root holding only the real `<skill_name>/` directory,
copied verbatim, plus the same POLICY skills the decoy root carries.
The two roots then differ in exactly one file's content (`SKILL.md`)
and report the same file count.

Round 7, second live finding: a decoy root holding only the one
manipulated skill still refused to dispatch -- `skills.py`'s
`resolve_static_policy_source()` unconditionally resolves
`_STATIC_POLICY_SKILLS` (currently `{'work-in-english'}`) against the
SAME repo_root every issue-scoped `--skills` spawn uses, regardless of
what was asked for, and a repo_root missing that name is a fail-closed
`sys.exit`, not a warning. So the decoy root also gets a verbatim, real
copy of every POLICY skill directory from the "on" arm's real corpus --
that baseline is not the manipulated variable and must be identical
across arms, unlike the one named skill.

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
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
import skills as _skills_mod  # noqa: E402 -- only for _STATIC_POLICY_SKILLS,
# a plain module-level constant; none of _skills_mod's functions that need
# the spawn.py-injected `_sp` alias are called from this file.

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


_FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_NAME_FIELD_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)

_DECOY_DESCRIPTION = (
    "Placeholder front matter for a controlled comparison arm. Carries "
    "no guidance about any task."
)


def front_matter_block(skill_md_text: str) -> str:
    """The leading YAML front-matter block (`---\\n...\\n---\\n`) of a
    real SKILL.md, verbatim -- or a minimal name-only fallback if the
    text does not open with one, since a decoy must still resolve as a
    skill even when the real file it copies from is malformed."""
    m = _FRONT_MATTER_RE.match(skill_md_text)
    return m.group(0) if m else "---\nname: (unknown)\n---\n"


def build_decoy_front_matter(real_front_matter: str) -> str:
    """Issue #3245 mid-flight correction (round 8): the earlier decoy
    copied the real skill's front matter verbatim (`front_matter_block`,
    written unchanged). That front matter is where a rubric-scored
    skill's guidance actually lives -- `description:` states the
    primary-metric/threshold/decision-rule/guardrail-bounds/sample-size
    coverage a scorer looks for, and `metadata:` can carry fields like
    `rule_count_floor` that reveal how many rules exist. Copying it
    verbatim into the "off" arm handed that arm most of the answer
    under a different heading. Only `name:` survives -- dispatch needs
    it to resolve the skill -- and `description:` is replaced with
    placeholder text carrying no task content; `metadata:` is dropped
    entirely."""
    m = _NAME_FIELD_RE.search(real_front_matter)
    name = m.group(1) if m else "(unknown)"
    return f"---\nname: {name}\ndescription: {_DECOY_DESCRIPTION}\n---\n"


def _copy_real_policy_skills(skills_root_on: Path, decoy_root: Path) -> list[str]:
    """Copies every POLICY skill (`skills._STATIC_POLICY_SKILLS`) from the
    "on" arm's real corpus into the decoy root verbatim, unmanipulated.
    Required for the off arm to dispatch at all: `resolve_static_policy_
    source()` resolves this fixed name set against the same repo_root
    every issue-scoped `--skills` spawn uses, fail-closed (`sys.exit`) if
    any is missing -- live-reproduced this round, the off arm's first
    real dispatch attempt refused with "unknown skill work-in-english"
    once the decoy root held only the one manipulated skill. These names
    are not the manipulated variable (every spawn gets them regardless of
    `--skills`), so they are copied whole, never decoyed. Silently skips
    a name absent from `skills_root_on` itself -- nothing this function
    can fabricate a real copy of, and `resolve_static_policy_source()`
    will raise its own clear error downstream if that absence matters."""
    copied = []
    for name in sorted(_skills_mod._STATIC_POLICY_SKILLS):
        src = skills_root_on / name
        if src.is_dir():
            shutil.copytree(src, decoy_root / name)
            copied.append(name)
    return copied


def build_decoy_skill_root(skill_name: str, real_skill_md: Path,
                            skills_root_on: Path | None = None) -> Path:
    """Issue #3280: a fresh directory containing `<skill_name>/SKILL.md`
    with `real_skill_md`'s front matter copied verbatim and its body
    dropped, plus a verbatim copy of every POLICY skill (see
    `_copy_real_policy_skills()`) when `skills_root_on` is given. Raises
    `ArmPreparationError` if `real_skill_md` does not exist, or if it
    carries no body beyond its front matter (a decoy of it would be
    byte-identical to the real thing, which would prove nothing about the
    manipulated variable)."""
    if not real_skill_md.is_file():
        raise ArmPreparationError(
            f"cannot build the 'off' arm's decoy -- {real_skill_md} does "
            "not exist, so there is no real skill to build a same-named "
            "decoy of")
    real_text = real_skill_md.read_text(encoding="utf-8")
    front_matter = front_matter_block(real_text)
    if front_matter == real_text:
        raise ArmPreparationError(
            f"cannot build a decoy that differs from the real skill -- "
            f"{real_skill_md} carries no body beyond its front matter, "
            "so a front-matter-only decoy would be byte-identical to it")
    decoy_text = build_decoy_front_matter(front_matter)
    if decoy_text == real_text:
        raise ArmPreparationError(
            f"cannot build a decoy that differs from the real skill -- "
            f"the placeholder front matter for {real_skill_md} came out "
            "byte-identical to the real file")
    decoy_root = Path(tempfile.mkdtemp(prefix="consumer-path-off-skills-decoy-"))
    decoy_skill_dir = decoy_root / skill_name
    decoy_skill_dir.mkdir(parents=True)
    (decoy_skill_dir / "SKILL.md").write_text(decoy_text, encoding="utf-8")
    if skills_root_on is not None:
        _copy_real_policy_skills(skills_root_on, decoy_root)
    return decoy_root


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


def build_on_skill_root(skills_root_on: Path, skill_name: str) -> Path:
    """Issue #3245 round-8 correction: mirrors `build_decoy_skill_root()`
    -- a fresh temp root holding only the real `<skill_name>/` directory,
    copied verbatim from the registry, plus a verbatim copy of every
    POLICY skill (see `_copy_real_policy_skills()`). The earlier `on`
    arm mounted the entire registry (352 files against the off arm's
    1), so any scored difference could not be attributed to
    `skill_name` alone -- 351 other skills were also on the table. This
    way the on/off roots differ in exactly one file's content and
    nothing else."""
    src = skills_root_on / skill_name
    if not src.is_dir():
        raise ArmPreparationError(
            f"cannot build the 'on' arm's skill root -- {src} does not "
            "exist under the real corpus at "
            f"{skills_root_on}; pass --skills-root-on at a populated "
            "skill-repository checkout")
    on_root = Path(tempfile.mkdtemp(prefix="consumer-path-on-skills-"))
    shutil.copytree(src, on_root / skill_name)
    _copy_real_policy_skills(skills_root_on, on_root)
    return on_root


def make_on_arm(home: Path, skills_root_on: Path, skill_name: str) -> dict:
    """Issue #3245 round-8 correction: `skills_root` used to be the
    caller's full registry root, mounted whole. It is now `skill_name`'s
    own real directory plus policy skills, built by
    `build_on_skill_root()` -- see that function's docstring. The
    caller (`build_manifest()`) is responsible for cleaning up the
    returned `skills_root`, exactly like the off arm's decoy root."""
    on_root = build_on_skill_root(skills_root_on, skill_name)
    skill_files = resolve_skill_files(on_root)
    if not skill_files:
        raise ArmPreparationError(
            f"'on' arm's skills root {on_root} resolved to zero "
            "files -- refusing to prepare an 'on' arm that is "
            "indistinguishable from 'off'; pass --skills-root-on at a "
            "populated skill-repository checkout")
    return {
        "arm": ARM_ON,
        "home": str(home),
        "skills_root": str(on_root),
        "skill_files": skill_files,
        "decoy": None,
    }


def make_off_arm(home: Path, skills_root_on: Path, skill_name: str) -> dict:
    """Issue #3280: the off arm's skills root is a fresh, real directory
    (unlike the retired absent-path design) holding a same-named decoy of
    `skill_name` built from `skills_root_on`'s real copy -- see
    `build_decoy_skill_root()`. This directory did not exist before this
    call and is this function's own to have created; the caller
    (`build_manifest()`) is responsible for adding it to the dirs it
    cleans up, exactly like the arm's HOME."""
    decoy_root = build_decoy_skill_root(
        skill_name, skills_root_on / skill_name / "SKILL.md", skills_root_on)
    skill_files = resolve_skill_files(decoy_root)
    if not skill_files:
        raise ArmPreparationError(
            f"'off' arm's decoy root {decoy_root} resolved to zero files "
            "-- refusing to report a decoy that was not actually written")
    return {
        "arm": ARM_OFF,
        "home": str(home),
        "skills_root": str(decoy_root),
        "skill_files": skill_files,
        "decoy": {
            "skill_name": skill_name,
            "source_skill_md": str(skills_root_on / skill_name / "SKILL.md"),
            "has_body_guidance": False,
        },
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
        on_arm = make_on_arm(on_home, skills_root_on, skill_name)
        # Round 8 correction: the on arm's skills_root is now a fresh
        # temp root this call created (only skill_name + policy skills,
        # not the whole registry) -- it needs the same cleanup as the
        # off arm's decoy root.
        created_dirs.append(Path(on_arm["skills_root"]))
        off_arm = make_off_arm(off_home, skills_root_on, skill_name)
        # Issue #3280: unlike the retired absent-path design, the off
        # arm's skills_root is now a real directory this call created
        # (the decoy) -- it needs the same cleanup as either arm's HOME.
        created_dirs.append(Path(off_arm["skills_root"]))
        if on_arm["home"] == off_arm["home"]:
            raise ArmPreparationError(
                "on/off arms received the same HOME -- isolation "
                "invariant violated")
        if len(on_arm["skill_files"]) != len(off_arm["skill_files"]):
            raise ArmPreparationError(
                "on/off arms report different file counts "
                f"({len(on_arm['skill_files'])} vs "
                f"{len(off_arm['skill_files'])}) -- the arms must mount "
                "the same file set, differing only in the manipulated "
                "skill's content, or a scored difference cannot be "
                "attributed to it")
    except ArmPreparationError:
        _cleanup(created_dirs)
        raise

    argv = dispatch_command(skill_name, model, "<issue-created-per-arm>",
                             "<sandbox-repo>")
    manifest = {
        "issue": 3183,
        "skill_name": skill_name,
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
