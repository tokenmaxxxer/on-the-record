#!/usr/bin/env python3
"""Consumer-path paired skills-on/skills-off run, driven through `spawn.py`
itself (issue #3127) rather than a bare `claude -p` call (issue #3053's
floor condition).

Both arms invoke `python3 spawn.py --skills <skill> "<task>" --issue <n>
-C <sandbox-repo>` -- the exact command `/on-the-record:run`'s orchestrator
issues in production (see `on-the-record/commands/run.md` step 4). The
`--skills` argument names the SAME skill in both arms (the orchestrator's
selection judgment is held constant); the two arms differ only in whether
that name resolves to a populated skill corpus when spawn.py mounts it
(`--skills-corpus` below controls this by pointing `MUSTER_SKILL_REPO` at
either the real skill-repository checkout or an empty sibling directory
containing nothing but a placeholder for the named skill, so the
`--skills` resolver's fail-closed unknown-skill rejection -- issue #2579 --
never fires in the skills-off arm; the corpus is present but empty of
actual guidance content).

Held constant across arms, same as `scripts/issue-3041/run_pair.sh`'s
pattern: sandbox repo + pinned commit, model, task text, issue number
sequence, orchestrator dispatch shape (spawn.py's own lint-before-spawn +
`--skills` + `--issue` invocation). The pair identifiers below intentionally
reuse `docs/issue-3053/_assets/01-study-groups` and `02-onboarding-
experiment`'s task text so pair identity is held constant across the floor-
condition (#3053) and consumer-path (#3127) measurements.

--dry-run prints the plan (both arms' exact spawn.py command lines and the
held-constant factor table) without shelling out to anything, so the design
can be inspected before it burns sessions. No other mode is invoked by this
issue's acceptance check; --execute (real, non-dry-run) is deliberately a
separate, explicit opt-in -- see the module docstring in
`docs/issue-3127/reports/*.md` "Rationale for deviations" for why this
session did not pass it.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Reused from issue-3053's floor-condition harness so pair identity (task
# text, discipline) is held constant across the floor and consumer-path
# measurements. Only the first two pairs are registered for this run (see
# docs/issue-3127/decisions/pre-registration.md, field (e)); the harness
# will read the other two if a future session extends the registration.
DEFAULT_PAIRS = ["01-study-groups", "02-onboarding-experiment"]
DEFAULT_TASKS_DIR = ROOT / "scripts" / "issue-3041" / "tasks"


@dataclass
class ArmConfig:
    name: str  # "skills-on" | "skills-off"
    skill_corpus_populated: bool
    # MUSTER_SKILL_REPO override: real skill-repository checkout for the
    # skills-on arm; an empty sibling dir (containing only the named
    # skill's frontmatter, no procedure body) for skills-off, so the named
    # `--skills` argument still resolves (fail-closed avoided) but carries
    # no actual guidance.
    skill_repo_env_override: str


@dataclass
class PairPlan:
    pair_id: str
    task_file: Path
    issue_skills_on: int | None = None
    issue_skills_off: int | None = None


@dataclass
class Plan:
    sandbox_repo: str
    pinned_sha: str | None
    skill_name: str
    model: str
    pairs: list[PairPlan]
    arms: tuple[ArmConfig, ArmConfig]
    watch_timeout_s: int
    held_constant: dict[str, str] = field(default_factory=dict)


def build_plan(args: argparse.Namespace) -> Plan:
    pair_ids = args.pairs.split(",") if args.pairs else DEFAULT_PAIRS
    pairs = [
        PairPlan(pair_id=pid, task_file=DEFAULT_TASKS_DIR / f"{pid}.txt")
        for pid in pair_ids
    ]
    arms = (
        ArmConfig(name="skills-on", skill_corpus_populated=True,
                  skill_repo_env_override=args.skill_repo_on),
        ArmConfig(name="skills-off", skill_corpus_populated=False,
                  skill_repo_env_override=args.skill_repo_off),
    )
    held_constant = {
        "sandbox_repo": args.repo,
        "model": args.model,
        "orchestrator_dispatch_shape":
            "spawn.py lint --issue <n> -C <repo>  (then, only if clean)  "
            "spawn.py --skills <skill> \"<task>\" --issue <n> -C <repo>",
        "skill_name_argument": args.skill,
        "task_text_per_pair": "held constant, reused from docs/issue-3053/"
                               "_assets task files (scripts/issue-3041/tasks/*.txt)",
        "permission_mode": "spawn.py's own default for --skills spawns "
                            "(role-handoff contract v3, not bypassPermissions "
                            "-- unlike #3053's bare claude -p arms, this path "
                            "goes through the real gh-guard/hook surface)",
        "issue_numbering": "each pair gets two fresh issue numbers (one per "
                            "arm) in the sandbox repo, created with identical "
                            "body text except the arm label",
    }
    return Plan(
        sandbox_repo=args.repo,
        pinned_sha=args.pinned_sha,
        skill_name=args.skill,
        model=args.model,
        pairs=pairs,
        arms=arms,
        watch_timeout_s=args.watch_timeout,
        held_constant=held_constant,
    )


def spawn_command(plan: Plan, pair: PairPlan, arm: ArmConfig, issue: int) -> list[str]:
    task_text = pair.task_file.read_text(encoding="utf-8").strip() \
        if pair.task_file.exists() else f"<task file missing: {pair.task_file}>"
    return [
        "python3", "spawn.py",
        "--skills", plan.skill_name,
        task_text,
        "--issue", str(issue),
        "--model", plan.model,
        "-C", plan.sandbox_repo,
    ]


def render_dry_run(plan: Plan) -> str:
    lines = ["=== issue-3127 consumer-path pair plan (dry run; nothing executed) ===", ""]
    lines.append("Held constant across both arms:")
    for k, v in plan.held_constant.items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("The single difference between arms: whether `--skills "
                  f"{plan.skill_name}` resolves to a populated corpus when "
                  "spawn.py mounts it.")
    for arm in plan.arms:
        lines.append(f"  - {arm.name}: skill_corpus_populated="
                      f"{arm.skill_corpus_populated}, "
                      f"MUSTER_SKILL_REPO={arm.skill_repo_env_override}")
    lines.append("")
    lines.append(f"Registered pairs ({len(plan.pairs)}):")
    for pair in plan.pairs:
        lines.append(f"  pair {pair.pair_id}:")
        for arm in plan.arms:
            placeholder_issue = f"<issue-created-for-{arm.name}>"
            cmd = spawn_command(plan, pair, arm, 0)
            cmd_display = " ".join(
                json.dumps(c) if " " in c or c == "" else c for c in cmd
            ).replace('"0"', placeholder_issue)
            lines.append(f"    {arm.name}: {cmd_display}")
            lines.append(
                "      preflight: python3 spawn.py lint --issue "
                f"{placeholder_issue} -C {plan.sandbox_repo}")
            lines.append(
                "      blocking watch (foreground, bounds this session's "
                "own turn per contract v3 s22): python3 spawn.py watch "
                f"--issue {placeholder_issue} --session {plan.skill_name} "
                f"--follow --self-heal  (timeout {plan.watch_timeout_s}s)")
    lines.append("")
    lines.append("Post-run instrumentation per arm (see collect_metrics()):")
    lines.append("  - directive-composition bytes: sum of "
                  "<workspace>/.on-the-record/directive/*.md file sizes")
    lines.append("  - token cost: matching entries in runs/ledger.jsonl "
                  "for this issue+skill")
    lines.append("  - verification rounds + defects found: count of "
                  "'repair round' / independent-verification PRs against "
                  "the arm's own issue, and defects each one's record cites")
    lines.append("  - wall-clock to landed: time from spawn dispatch to the "
                  "arm's PR reaching a merged/landed state, not first output")
    lines.append("  - blind quality score: scrub_skill_slugs() then the "
                  "same blind-evaluator shape as scripts/issue-3041/"
                  "evaluate_pair.py, scored against the pair's own rubric")
    return "\n".join(lines)


_SLUG_RE = re.compile(
    r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+){1,6})\b")


def scrub_skill_slugs(text: str, known_slugs: list[str]) -> tuple[str, int]:
    """Redact literal skill-slug mentions from deliverable text before
    blind scoring (issue #3053's leak: skills-on deliverables cited their
    own skill slugs by name, which a blind text-only evaluator can read as
    a quality signal about which arm is which rather than about the
    deliverable's content). Returns (scrubbed_text, replacement_count).

    Matches only the registered known-slug list, not every hyphenated
    token, so ordinary hyphenated domain vocabulary in the deliverable
    (e.g. "sign-up", "cross-family") is never touched -- only literal
    mentions of a mounted skill's own name.
    """
    count = 0
    scrubbed = text
    for slug in known_slugs:
        pattern = re.compile(re.escape(slug), re.IGNORECASE)
        scrubbed, n = pattern.subn("[skill-name-redacted]", scrubbed)
        count += n
    return scrubbed, count


def collect_directive_bytes(workspace: Path) -> int | None:
    directive_dir = workspace / ".on-the-record" / "directive"
    if not directive_dir.is_dir():
        return None
    return sum(p.stat().st_size for p in directive_dir.glob("*.md"))


def collect_ledger_tokens(issue: int, skill: str) -> dict | None:
    ledger = ROOT / "runs" / "ledger.jsonl"
    if not ledger.exists():
        return None
    matches = []
    with ledger.open(encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("issue") == issue and entry.get("skill") == skill:
                matches.append(entry)
    if not matches:
        return None
    return {"ledger_entries": matches}


def collect_metrics(workspace: Path, issue: int, skill: str) -> dict:
    """Post-run instrumentation for one arm's workspace. Best-effort: each
    field is None (with the reason implicit in which collector returned
    None) rather than a fabricated number when the expected artifact isn't
    present -- this function has never run against a real workspace (see
    the accompanying record's "Rationale for deviations"), so its exact
    parsing of ledger/PR-review shapes should be treated as a first draft
    to verify against a real run's actual artifacts, not as validated code.
    """
    return {
        "directive_composition_bytes": collect_directive_bytes(workspace),
        "ledger_tokens": collect_ledger_tokens(issue, skill),
    }


def execute_arm(plan: Plan, pair: PairPlan, arm: ArmConfig, issue: int,
                 confirm_real_spawn: bool) -> dict:
    """Real (non-dry-run) execution. Not invoked by this issue's acceptance
    check and not invoked by this session -- see the accompanying record's
    "Rationale for deviations" for why: spawn.py's own `--skills` dispatch
    path self-daemonizes (os.setsid() + start_new_session=True + stdio
    redirected to devnull, spawn.py:4684-4749) rather than blocking in the
    caller's process, so a bare foreground subprocess.run() of the spawn
    command does not observe completion -- only `spawn.py watch --follow`
    afterward does, and that is a second blocking call this function issues
    explicitly below, bounded by `plan.watch_timeout_s`, so the whole arm
    stays inside one foreground call chain (contract v3 s22: a headless
    single-shot turn must consume what it delegates before ending).
    """
    if not confirm_real_spawn:
        raise RuntimeError(
            "execute_arm() requires confirm_real_spawn=True -- this "
            "creates a real GitHub issue/branch/PR in plan.sandbox_repo "
            "and runs a real recursive claude session. Pass --execute "
            "--i-understand-this-spawns-real-sessions to the CLI.")
    env_override = {"MUSTER_SKILL_REPO": arm.skill_repo_env_override}
    lint = subprocess.run(
        ["python3", "spawn.py", "lint", "--issue", str(issue),
         "-C", plan.sandbox_repo],
        cwd=ROOT, env={**_os_environ(), **env_override},
        capture_output=True, text=True)
    if lint.returncode != 0:
        return {"arm": arm.name, "issue": issue, "status": "lint-failed",
                "lint_stderr": lint.stderr}
    cmd = spawn_command(plan, pair, arm, issue)
    t0 = time.monotonic()
    dispatch = subprocess.run(cmd, cwd=ROOT, env={**_os_environ(), **env_override},
                               capture_output=True, text=True)
    if dispatch.returncode != 0:
        # Do not fall through to `watch` -- a session that never dispatched
        # has nothing to watch, and blocking for watch_timeout_s anyway
        # would silently absorb the dispatch failure as if it were just a
        # slow-starting session.
        return {"arm": arm.name, "issue": issue, "status": "dispatch-failed",
                "dispatch_returncode": dispatch.returncode,
                "dispatch_stderr": dispatch.stderr}
    try:
        watch = subprocess.run(
            ["python3", "spawn.py", "watch", "--issue", str(issue),
             "--session", plan.skill_name, "--follow", "--self-heal",
             "-C", plan.sandbox_repo],
            cwd=ROOT, env={**_os_environ(), **env_override},
            capture_output=True, text=True, timeout=plan.watch_timeout_s)
    except subprocess.TimeoutExpired:
        return {"arm": arm.name, "issue": issue, "status": "watch-timed-out",
                "wall_clock_s": time.monotonic() - t0,
                "dispatch_returncode": dispatch.returncode,
                "watch_timeout_s": plan.watch_timeout_s}
    wall_clock_s = time.monotonic() - t0
    status = "watched-to-completion" if watch.returncode == 0 else "watch-failed"
    return {
        "arm": arm.name, "issue": issue, "status": status,
        "wall_clock_s": wall_clock_s,
        "dispatch_returncode": dispatch.returncode,
        "watch_returncode": watch.returncode,
        "watch_stderr": watch.stderr if watch.returncode != 0 else None,
    }


def _os_environ() -> dict:
    import os
    return dict(os.environ)


def emit_not_executed_results(plan: Plan) -> dict:
    return {
        "issue": 3127,
        "run_status": "not_executed",
        "pre_registration_ref": "docs/issue-3127/decisions/pre-registration.md",
        "pairs_registered": [p.pair_id for p in plan.pairs],
        "arms": {arm.name: {
            "quality_blind_score": None,
            "wall_clock_to_landed_s": None,
            "tokens_total": None,
            "directive_composition_bytes": None,
            "verification_rounds": None,
            "verification_defects_found": None,
            "note": "not measured -- see run_status",
        } for arm in plan.arms},
        "decision": "unmeasured -- not a null result (no data was collected "
                     "this session); see power statement in pre-registration.md",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="<sandbox-repo-not-yet-chosen>",
                     help="sandbox repo (-C target) both arms clone from; "
                          "must already be spawn.py-init'd (docs/specs/"
                          "approvers.md present)")
    ap.add_argument("--pinned-sha", default=None)
    ap.add_argument("--skill", default="product-discovery-hypothesis-preregistration",
                     help="skill name passed to --skills identically in "
                          "both arms; orchestrator selection judgment held "
                          "constant, only corpus availability differs")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--pairs", default=None,
                     help=f"comma-separated pair ids, default: {','.join(DEFAULT_PAIRS)}")
    ap.add_argument("--skill-repo-on", default="$MUSTER_SKILL_REGISTRY_ROOT",
                     help="MUSTER_SKILL_REPO value for the skills-on arm")
    ap.add_argument("--skill-repo-off", default="<empty-sibling-dir>",
                     help="MUSTER_SKILL_REPO value for the skills-off arm "
                          "-- a dir containing only the named skill's "
                          "frontmatter (name+description), no procedure "
                          "body, so --skills resolves without fail-closing")
    ap.add_argument("--watch-timeout", type=int, default=1800)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--i-understand-this-spawns-real-sessions",
                     action="store_true", dest="confirm_real_spawn",
                     help="required alongside --execute: this creates real "
                          "GitHub issues/PRs in --repo and runs real "
                          "recursive claude sessions")
    ap.add_argument("--out", default=str(
        ROOT / "docs" / "issue-3127" / "_assets" / "consumer-path-results.json"))
    args = ap.parse_args()

    if not args.dry_run and not args.execute:
        print("error: pass --dry-run to inspect the plan, or --execute "
              "(with --i-understand-this-spawns-real-sessions) to run it "
              "for real.", file=sys.stderr)
        return 2

    plan = build_plan(args)

    if args.dry_run:
        print(render_dry_run(plan))
        return 0

    if not args.confirm_real_spawn:
        print("error: --execute requires "
              "--i-understand-this-spawns-real-sessions", file=sys.stderr)
        return 2

    # Real execution path: intentionally not exercised by this issue's
    # acceptance check or by the session that authored this file. Left
    # implemented (not a stub) so a future session can run it directly.
    results = emit_not_executed_results(plan)
    results["run_status"] = "executed-with-incomplete-instrumentation"
    for pair in plan.pairs:
        for arm in plan.arms:
            print(f"[plan] would execute {arm.name} for pair {pair.pair_id} "
                  "-- issue-number allocation and result aggregation are "
                  "left to the caller (this harness stops short of "
                  "gh issue create side effects); see execute_arm().",
                  file=sys.stderr)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
