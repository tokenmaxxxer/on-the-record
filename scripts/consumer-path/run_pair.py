#!/usr/bin/env python3
"""Real paired skills-on/skills-off consumer-path run for issue #3245 (R007).

Combines two pieces of already-landed machinery rather than re-deriving
either:

  - `scripts/consumer-path/prepare_arms.py` (issue #3183 / PR #3185): the
    launcher-owned trust root. Both arms get a fresh, isolated HOME; the
    "on" arm's skills root is a real, populated skill-repository checkout;
    the "off" arm's skills root is a path this process never creates at
    all -- no stub, nothing for a spawned process to read.
  - `scripts/issue-3127/run_consumer_pair.py` (issue #3127): the actual
    dispatch-through-`spawn.py`-with-the-orchestrator mechanics (lint,
    dispatch, blocking `watch --follow`), the H1 skill-invocation gate
    (`collect_skill_invocation`), and the blind H2 scorer
    (`evaluate_pair_blind` / `scrub_skill_slugs`).

This module supplies only what neither of those already does: building the
dispatch argv+env for each arm FROM the trust-root manifest (both HOME and
MUSTER_SKILL_REPO, not MUSTER_SKILL_REPO alone the way #3127's ArmConfig
did), and persisting a transport record of that argv+env to disk *before*
either arm is dispatched, so `verify_manipulation.py` has something
launcher-owned to check the manifest against afterward.

skills-off's `--skills` value carries the `skill-repo:` source qualifier
(issue #2579), exactly as #3127's run established live: without it, a real
run on this machine either fail-closed on a genuine multi-source conflict
or silently fell through to the fully-populated real corpus (the exact
defect this whole trust-root line of work exists to close) -- see
`scripts/issue-3127/run_consumer_pair.py`'s module docstring. The
qualifier changes which of `resolved_skill_sources()`'s four tiers is
read; it is not a stub file and it manipulates nothing the off arm's
skills root does not already guarantee (a path that was never created).
`prepare_arms.py`'s manifest documents an "argv identical across arms"
TEMPLATE as the ideal; this launcher's actual dispatch differs from that
template by exactly this one token, for the reason above, and says so in
the transport record's own `argv_deviation_from_template` field rather
than silently asserting identity `verify_manipulation.py` does not itself
check.

Usage:
  python3 scripts/consumer-path/run_pair.py \\
      --pair-id 01-study-groups --repo <local clone of target repo> \\
      --skill product-discovery-hypothesis-preregistration \\
      --on-issue 19 --off-issue 20 \\
      --out-dir docs/issue-3245/_assets/01-study-groups \\
      --execute --i-understand-this-spawns-real-sessions
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CONSUMER_PATH_DIR = ROOT / "scripts" / "consumer-path"
TASKS_DIR = ROOT / "scripts" / "issue-3041" / "tasks"
RUBRICS_DIR = ROOT / "scripts" / "issue-3041" / "rubrics"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare_arms = _load_module("prepare_arms", CONSUMER_PATH_DIR / "prepare_arms.py")
verify_manipulation = _load_module(
    "verify_manipulation", CONSUMER_PATH_DIR / "verify_manipulation.py")

sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import run_consumer_pair as rcp  # noqa: E402


def _skills_argument(skill_name: str, arm: str) -> str:
    """Bare name for "on" (byte-identical to production usage); the
    `skill-repo:` source qualifier for "off" so resolution reads ONLY
    `MUSTER_SKILL_REPO` (see module docstring)."""
    return skill_name if arm == "on" else f"skill-repo:{skill_name}"


def spawn_command(skill_name: str, model: str, task_text: str, issue: int,
                   repo: str, arm: str) -> list[str]:
    return [
        "python3", "spawn.py",
        "--skills", _skills_argument(skill_name, arm),
        task_text,
        "--issue", str(issue),
        "--model", model,
        "-C", repo,
    ]


def build_transport(manifest: dict, skill_name: str, model: str,
                     task_text: str, repo: str, on_issue: int,
                     off_issue: int) -> dict:
    """The argv+env this launcher is ABOUT to hand each arm's Popen(),
    captured as a plain dict this function's caller writes to disk before
    any subprocess starts -- the "transport record"
    `verify_manipulation.py` cross-checks against the manifest."""
    on_arm = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off_arm = [a for a in manifest["arms"] if a["arm"] == "off"][0]
    argv_on = spawn_command(skill_name, model, task_text, on_issue, repo, "on")
    argv_off = spawn_command(skill_name, model, task_text, off_issue, repo, "off")
    return {
        "captured_before_dispatch": True,
        "argv_deviation_from_template": (
            "off arm's --skills value carries the skill-repo: source "
            "qualifier (issue #2579); on arm's does not. See module "
            "docstring -- proven necessary on this machine, not a stub "
            "or a claim of byte-identical argv."
        ),
        "arms": {
            "on": {"argv": argv_on,
                   "env": {"HOME": on_arm["home"],
                           manifest["skills_root_env_var"]: on_arm["skills_root"]}},
            "off": {"argv": argv_off,
                    "env": {"HOME": off_arm["home"],
                            manifest["skills_root_env_var"]: off_arm["skills_root"]}},
        },
    }


_LEAK_PRONE_ENV_RE = re.compile(r"^(CLAUDE|MUSTER|TOKENMAXXXER)_[A-Z0-9_]*$")


def _clean_base_env() -> dict:
    """This orchestrating session's own env, with every CLAUDE_*/MUSTER_*/
    TOKENMAXXXER_* var stripped before an arm's own overrides are layered
    on top -- same discipline as `scripts/issue-3041/run_pair.sh` (issue
    #3053: two of four skills-off arms in that issue's first real run
    resolved "the repo root" to THIS repo's own working directory because
    inherited CLAUDE_CODE_MESSAGING_SOCKET/BRIDGE_SESSION_ID/SESSION_ID
    let the child attach to this session's own SDK bridge). Also strips
    `CORE_BUILD_NOW` specifically: leaking this orchestrating session's
    own build-now bypass into the spawned arm would make it skip its own
    proposal-only phase-1 default, contaminating `execute_arm()`'s own
    documented assumption that `watch --follow`'s stop condition is at
    most a phase-1 PR opening under the *unmodified* two-phase protocol.
    """
    env = {k: v for k, v in os.environ.items()
           if not _LEAK_PRONE_ENV_RE.match(k)}
    env.pop("CORE_BUILD_NOW", None)
    return env


def execute_arm(argv: list[str], env_override: dict, repo: str, issue: int,
                 arm_name: str, watch_session: str, watch_timeout_s: int,
                 confirm_real_spawn: bool) -> dict:
    """Lint, dispatch, then block on `spawn.py watch --follow` -- same
    shape as `run_consumer_pair.execute_arm()`, adapted to take a fully
    pre-built argv/env pair (this arm's trust-rooted HOME +
    MUSTER_SKILL_REPO) instead of an `ArmConfig`."""
    if not confirm_real_spawn:
        raise RuntimeError(
            "execute_arm() requires confirm_real_spawn=True -- this "
            "creates a real GitHub PR in the target repo and runs a real "
            "recursive claude session.")
    landing_status = (
        "not_measured -- this harness observes only the spawned session's "
        "own session-end event, which under the unmodified two-phase "
        "protocol is at most a phase-1 proposal PR opening, not a merge "
        "to main. wall_clock_to_pr_open_s is the honest name for what "
        "was actually timed.")
    env = {**_clean_base_env(), **env_override}
    lint = subprocess.run(
        ["python3", "spawn.py", "lint", "--issue", str(issue), "-C", repo],
        cwd=ROOT, env=env, capture_output=True, text=True)
    if lint.returncode != 0:
        return {"arm": arm_name, "issue": issue, "status": "lint-failed",
                "lint_stderr": lint.stderr}
    t0 = time.monotonic()
    dispatch = subprocess.run(argv, cwd=ROOT, env=env,
                               capture_output=True, text=True)
    if dispatch.returncode != 0:
        return {"arm": arm_name, "issue": issue, "status": "dispatch-failed",
                "dispatch_returncode": dispatch.returncode,
                "dispatch_stderr": dispatch.stderr}
    try:
        watch = subprocess.run(
            ["python3", "spawn.py", "watch", "--issue", str(issue),
             "--session", watch_session, "--follow", "--self-heal",
             "-C", repo],
            cwd=ROOT, env=env, capture_output=True, text=True,
            timeout=watch_timeout_s)
    except subprocess.TimeoutExpired:
        return {"arm": arm_name, "issue": issue, "status": "watch-timed-out",
                "wall_clock_to_pr_open_s": time.monotonic() - t0,
                "wall_clock_to_landed_s": None,
                "landing_measurement_status": landing_status,
                "dispatch_returncode": dispatch.returncode,
                "watch_timeout_s": watch_timeout_s}
    wall_clock_to_pr_open_s = time.monotonic() - t0
    status = "watched-to-completion" if watch.returncode == 0 else "watch-failed"
    return {
        "arm": arm_name, "issue": issue, "status": status,
        "wall_clock_to_pr_open_s": wall_clock_to_pr_open_s,
        "wall_clock_to_landed_s": None,
        "landing_measurement_status": landing_status,
        "dispatch_returncode": dispatch.returncode,
        "watch_returncode": watch.returncode,
        "watch_stderr": watch.stderr if watch.returncode != 0 else None,
    }


def collect_verification_rounds(repo: str, issue: int, skill_name: str) -> dict:
    """Best-effort: how many review rounds the arm's own PR needed before
    it would have landed. Proxy: count of `CHANGES_REQUESTED` reviews on
    the PR opened from branch `issue-<n>/<skill>`, plus commits pushed
    after the first. None (with a reason), never a fabricated 0, when the
    PR cannot be found or `gh` fails -- silent-failure-audit discipline:
    a missing signal is reported missing, not silently scored as clean."""
    branch = f"issue-{issue}/{skill_name}"
    r = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "reviews,commits"],
        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return {"verification_rounds": None, "defects_found": None,
                "measured": False,
                "reason": f"gh pr view {branch!r} failed: {r.stderr.strip()}"}
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        return {"verification_rounds": None, "defects_found": None,
                "measured": False,
                "reason": f"gh pr view output not valid JSON: {exc}"}
    reviews = data.get("reviews") or []
    changes_requested = [rv for rv in reviews
                          if rv.get("state") == "CHANGES_REQUESTED"]
    return {
        "verification_rounds": len(changes_requested),
        "defects_found": None,
        "measured": True,
        "reason": "proxy: count of CHANGES_REQUESTED reviews on the arm's "
                  "own PR branch; does not distinguish which review found "
                  "how many distinct defects",
        "commit_count": len(data.get("commits") or []),
    }


def collect_cost(repo: str, issue: int, skill_name: str) -> dict:
    ledger = ROOT / "runs" / "ledger.jsonl"
    if not ledger.exists():
        return {"cost_usd": None, "measured": False,
                "reason": "runs/ledger.jsonl does not exist"}
    matches = []
    with ledger.open(encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("issue") == issue and entry.get("skill") == skill_name:
                matches.append(entry)
    if not matches:
        return {"cost_usd": None, "measured": False,
                "reason": f"no runs/ledger.jsonl entries for issue={issue} "
                          f"skill={skill_name!r}"}
    total = sum(m.get("cost_usd") or 0 for m in matches)
    return {"cost_usd": total, "measured": True, "ledger_entries": matches}


def run_pair(pair_id: str, repo: str, skill_name: str, model: str,
             on_issue: int, off_issue: int, out_dir: Path,
             watch_timeout_s: int, confirm_real_spawn: bool,
             evaluator_fn=None) -> dict:
    task_file = TASKS_DIR / f"{pair_id}.txt"
    task_text = task_file.read_text(encoding="utf-8").strip()

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest, created_dirs = prepare_arms.build_manifest(
        Path(os.environ.get("MUSTER_SKILL_REGISTRY_ROOT", "")),
        skill_name, model, os.environ.get("USER", "unknown"))
    manifest_path = out_dir / "manifest.json"
    manifest_text = prepare_arms.render_manifest_json(manifest)
    manifest_path.write_text(manifest_text, encoding="utf-8")
    digest = prepare_arms._sha256_bytes(manifest_path.read_bytes())
    (out_dir / "manifest.json.sha256").write_text(digest + "\n", encoding="utf-8")

    # Auth, not manipulation: an isolated HOME from build_manifest() has
    # no CLI credentials, and a `claude -p` dispatch under it fails
    # closed on "Not logged in" before hooks or skill selection ever run
    # (issue #3245 independent-verification-2). Applied identically to
    # both arms.
    try:
        for arm in manifest["arms"]:
            prepare_arms.provision_credentials(Path(arm["home"]))
    except prepare_arms.ArmPreparationError as exc:
        prepare_arms._cleanup(created_dirs)
        return {"pair_id": pair_id, "status": "credential-provisioning-failed",
                "manifest": str(manifest_path), "reason": str(exc),
                "excluded_from_h2": True, "exclusion_reason": str(exc),
                "h2": None}

    transport = build_transport(manifest, skill_name, model, task_text, repo,
                                 on_issue, off_issue)
    transport_path = out_dir / "transport.json"
    transport_path.write_text(json.dumps(transport, indent=2), encoding="utf-8")

    try:
        pre_dispatch_verdict = verify_manipulation.verify(manifest_path, transport_path)
    except verify_manipulation.VerificationFailure as exc:
        prepare_arms._cleanup(created_dirs)
        return {"pair_id": pair_id, "status": "manipulation-check-failed-pre-dispatch",
                "manifest": str(manifest_path), "transport": str(transport_path),
                "reason": str(exc), "excluded_from_h2": True,
                "exclusion_reason": str(exc), "h2": None}

    arm_results = {}
    for arm_name, issue in (("on", on_issue), ("off", off_issue)):
        argv = transport["arms"][arm_name]["argv"]
        env_override = transport["arms"][arm_name]["env"]
        arm_results[arm_name] = execute_arm(
            argv, env_override, repo, issue, arm_name, skill_name,
            watch_timeout_s, confirm_real_spawn)

    prepare_arms._cleanup(created_dirs)

    both_ok = all(arm_results[a].get("status") == "watched-to-completion"
                  for a in ("on", "off"))
    if not both_ok:
        return {
            "pair_id": pair_id, "manifest": str(manifest_path),
            "transport": str(transport_path),
            "manipulation_check": pre_dispatch_verdict,
            "arm_results": arm_results, "h1": None,
            "h1_manipulation_ok": False, "excluded_from_h2": True,
            "exclusion_reason": (
                "at least one arm did not reach watched-to-completion "
                f"(on={arm_results['on'].get('status')!r}, "
                f"off={arm_results['off'].get('status')!r})"),
            "h2": None,
        }

    class _P:  # minimal shim for rcp.arm_workspace_dir()'s Plan-shaped arg
        sandbox_repo = repo
        skill_name = skill_name
    plan_shim = _P()
    workspace_on = rcp.arm_workspace_dir(plan_shim, on_issue)
    workspace_off = rcp.arm_workspace_dir(plan_shim, off_issue)

    def _fetch(_plan, issue):
        return rcp._default_deliverable_fetcher(plan_shim, issue)

    def compute_h2():
        deliverable_on = _fetch(plan_shim, on_issue)
        deliverable_off = _fetch(plan_shim, off_issue)
        if deliverable_on is None or deliverable_off is None:
            return {"h2_unavailable": True,
                    "h2_unavailable_reason":
                        "deliverable fetch failed for at least one arm -- "
                        f"on={'ok' if deliverable_on is not None else 'missing'}, "
                        f"off={'ok' if deliverable_off is not None else 'missing'}"}
        rubric_file = RUBRICS_DIR / f"{pair_id}.md"
        rubric_text = rubric_file.read_text(encoding="utf-8").strip() \
            if rubric_file.exists() else ""
        return rcp.evaluate_pair_blind(task_text, rubric_text, deliverable_on,
                                        deliverable_off, [skill_name],
                                        evaluator_fn=evaluator_fn)

    gated = rcp.gate_pair_on_h1(pair_id, workspace_on, workspace_off,
                                 skill_name=skill_name, compute_h2=compute_h2)
    if gated.get("h2") and gated["h2"].get("h2_unavailable"):
        gated["h2_unavailable_reason"] = gated["h2"]["h2_unavailable_reason"]
        gated["h2"] = None

    gated["manifest"] = str(manifest_path)
    gated["transport"] = str(transport_path)
    gated["manipulation_check"] = pre_dispatch_verdict
    gated["arm_results"] = arm_results
    gated["verification"] = {
        "on": collect_verification_rounds(repo, on_issue, skill_name),
        "off": collect_verification_rounds(repo, off_issue, skill_name),
    }
    gated["cost"] = {
        "on": collect_cost(repo, on_issue, skill_name),
        "off": collect_cost(repo, off_issue, skill_name),
    }
    return gated


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pair-id", required=True)
    ap.add_argument("--repo", required=True,
                    help="local clone of the target sandbox repo")
    ap.add_argument("--skill", required=True,
                    help="skill name held constant across both arms "
                         "(pre-registered pinning -- see docs/issue-3245/"
                         "decisions/)")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--on-issue", type=int, required=True)
    ap.add_argument("--off-issue", type=int, required=True)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--watch-timeout", type=int, default=1800)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--i-understand-this-spawns-real-sessions",
                    action="store_true", dest="confirm_real_spawn")
    ap.add_argument("--out", default=None,
                    help="where to write this pair's result JSON "
                         "(defaults to <out-dir>/result.json)")
    args = ap.parse_args()

    if not args.execute:
        print("error: pass --execute (with "
              "--i-understand-this-spawns-real-sessions) to run a real "
              "pair -- this module has no --dry-run mode of its own; use "
              "prepare_arms.py --dry-run to inspect the trust root alone.",
              file=sys.stderr)
        return 2
    if not args.confirm_real_spawn:
        print("error: --execute requires "
              "--i-understand-this-spawns-real-sessions", file=sys.stderr)
        return 2

    result = run_pair(args.pair_id, args.repo, args.skill, args.model,
                       args.on_issue, args.off_issue, args.out_dir,
                       args.watch_timeout, args.confirm_real_spawn)
    out_path = Path(args.out) if args.out else args.out_dir / "result.json"
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps(result, indent=2, default=str)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
