#!/usr/bin/env python3
"""Consumer-path paired skills-on/skills-off run, driven through `spawn.py`
itself (issue #3127) rather than a bare `claude -p` call (issue #3053's
floor condition).

Both arms invoke `python3 spawn.py --skills <skill-argument> "<task>" --issue
<n> -C <sandbox-repo>` -- the exact command `/on-the-record:run`'s
orchestrator issues in production (see `on-the-record/commands/run.md` step
4), with one deliberate exception documented below. The two arms differ in
whether the named skill resolves to a populated skill corpus when spawn.py
mounts it:

- skills-on: `--skills <skill>` (bare name, byte-identical to production
  usage) with `MUSTER_SKILL_REPO` pointed at the real skill-repository
  checkout.
- skills-off: `--skills skill-repo:<skill>` (the `<source>:<name>` source
  qualifier, issue #2579) with `MUSTER_SKILL_REPO` pointed at a stub
  directory this harness creates itself (`build_stub_skill_repo()`)
  containing only the named skill's frontmatter, no procedure body.

Repair-round note (issue #3127 second verification, PR #3145, finding 1):
the ORIGINAL version of this harness pointed `MUSTER_SKILL_REPO` at a
literal placeholder string (`"<empty-sibling-dir>"`) that no code ever
created, and passed the bare skill name for BOTH arms. `skills.py`'s
`resolved_skill_sources()` reads FOUR sources unconditionally
(skill-repo/plugin/local-user/local-repo) and only `MUSTER_SKILL_REPO`
touches the first; reproduced live against a real environment, that
combination either (a) fail-closed with `sys.exit()` on a genuine
multi-source conflict once `~/.claude/skills` also carried the skill, or
(b) -- because the placeholder string is not a real directory --
`_skill_repo_root()` silently fell through its sibling/managed-clone
fallback chain to the REAL, fully populated skill-repository checkout,
making the "skills-off" arm identical to skills-on (a repeat of #3053's
retracted first run). Both failure modes are closed here by (1) actually
creating the stub directory instead of naming one that never exists, and
(2) adding the `skill-repo:` qualifier to the skills-off arm's `--skills`
argument so resolution is forced through ONLY the `MUSTER_SKILL_REPO`
source -- `resolved_skill_sources()` filters to the qualified source
before it ever compares against the other three tiers, so a real
`~/.claude/skills` (or a plugin, or the target repo's own `.claude/
skills`) carrying the same skill under different content can no longer
produce either failure mode. `test/test_spawn_skills_mount.py`'s
`SymlinkCollapseAndSourceQualifierTest` already establishes this same
qualifier behavior against `spawn.resolved_skill_sources()` directly; this
file's own tests (`tests/test_issue_3127_run_consumer_pair.py`) reproduce
the specific before/after this issue found, including a case that shows
the OLD (unqualified) mechanism failing, so the fix is demonstrated
against a real failure, not just asserted.

Held constant across arms, same as `scripts/issue-3041/run_pair.sh`'s
pattern: sandbox repo + pinned commit, model, task text, issue number
sequence, orchestrator dispatch shape (spawn.py's own lint-before-spawn +
`--skills` + `--issue` invocation). The pair identifiers below intentionally
reuse `docs/issue-3053/_assets/01-study-groups` and `02-onboarding-
experiment`'s task text so pair identity is held constant across the floor-
condition (#3053) and consumer-path (#3127) measurements.

--dry-run prints the plan (both arms' exact spawn.py command lines and the
held-constant factor table) without spawning any session, so the design can
be inspected before it burns sessions. No other mode is invoked by this
issue's acceptance check; --execute (real, non-dry-run) is deliberately a
separate, explicit opt-in -- see the module docstring in
`docs/issue-3127/reports/*.md` "Rationale for deviations" for why the
original build session did not pass it.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(ROOT))
import spawn as _spawn_mod  # noqa: E402 -- see arm_workspace_dir()
import skills as _skills_mod  # noqa: E402 -- see build_stub_skill_repo()

sys.path.insert(0, str(ROOT / "scripts"))
import measure_skill_invocation as _msi  # noqa: E402 -- see collect_skill_invocation()

# Reused from issue-3053's floor-condition harness so pair identity (task
# text, discipline) is held constant across the floor and consumer-path
# measurements. Only the first two pairs are registered for this run (see
# docs/issue-3127/decisions/pre-registration.md, field (e)); the harness
# will read the other two if a future session extends the registration.
DEFAULT_PAIRS = ["01-study-groups", "02-onboarding-experiment"]
DEFAULT_TASKS_DIR = ROOT / "scripts" / "issue-3041" / "tasks"
DEFAULT_RUBRICS_DIR = ROOT / "scripts" / "issue-3041" / "rubrics"


@dataclass
class ArmConfig:
    name: str  # "skills-on" | "skills-off"
    skill_corpus_populated: bool
    # MUSTER_SKILL_REPO override: real skill-repository checkout for the
    # skills-on arm; a stub dir this harness creates (build_stub_skill_repo())
    # containing only the named skill's frontmatter for skills-off.
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


def build_stub_skill_repo(skill_name: str, dest: Path) -> Path:
    """Create a REAL, on-disk skill-repo directory containing only
    `skill_name`'s frontmatter (name + description), no procedure body --
    the "corpus present but empty" stub the skills-off arm's
    `MUSTER_SKILL_REPO` points at.

    This replaces the original harness's literal placeholder string
    (`"<empty-sibling-dir>"`, a value no code ever turned into a directory)
    with an actual write, so `skills._skill_repo_root()` finds a real,
    valid directory (`Path(...).is_dir()` true) and never falls through to
    its sibling/managed-clone fallback chain -- see this file's module
    docstring, finding 1.

    Also stubs every name in `skills._STATIC_POLICY_SKILLS` (e.g.
    `work-in-english`) the same frontmatter-only way (issue #3127 live
    execution, found dispatching against real sandbox issues 2026-09-02):
    `resolve_static_policy_source()` resolves those POLICY skills
    unconditionally from the SAME skill-repo root every session mounts
    from, regardless of arm or task language -- the `skill-repo:` source
    qualifier (see `_skills_argument_for_arm()`) forces that resolution
    through this stub dir for the skills-off arm too. Stubbing only the
    named target skill left the policy skill unresolvable there
    (`sys.exit("...모르는 스킬 work-in-english...")`), failing dispatch
    for every skills-off arm outright rather than producing the intended
    "corpus present but empty" condition.
    """
    for name in {skill_name, *_skills_mod._STATIC_POLICY_SKILLS}:
        skill_dir = dest / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: issue #3127 skills-off arm stub -- frontmatter "
            "only, no procedure body, so the named skill resolves "
            "(fail-closed unknown-skill rejection never fires) but "
            "carries no actual guidance content.\n"
            "---\n",
            encoding="utf-8")
    return dest


def _skills_argument_for_arm(plan: Plan, arm: ArmConfig) -> str:
    """The `--skills` value passed to spawn.py for one arm. skills-on uses
    the bare skill name -- byte-identical to what `/on-the-record:run`'s
    orchestrator actually types in production (held constant, per
    `held_constant['skill_name_argument']`). skills-off adds the
    `skill-repo:` source qualifier (issue #2579) -- a harness-only control,
    never something a production orchestrator types -- so
    `resolved_skill_sources()` filters to ONLY the `MUSTER_SKILL_REPO`-
    pointed source before it ever reads (or could conflict against)
    `~/.claude/skills`, installed plugins, or the target repo's own
    `.claude/skills`. See this file's module docstring for why the
    unqualified name did not achieve "corpus present but empty" in a real
    environment."""
    if arm.skill_corpus_populated:
        return plan.skill_name
    return f"skill-repo:{plan.skill_name}"


def build_plan(args: argparse.Namespace) -> Plan:
    pair_ids = args.pairs.split(",") if args.pairs else DEFAULT_PAIRS
    pairs = [
        PairPlan(pair_id=pid, task_file=DEFAULT_TASKS_DIR / f"{pid}.txt")
        for pid in pair_ids
    ]
    skill_repo_off = args.skill_repo_off
    if skill_repo_off is None:
        skill_repo_off = str(Path(tempfile.mkdtemp(prefix="issue-3127-skills-off-")))
    build_stub_skill_repo(args.skill, Path(skill_repo_off))
    arms = (
        ArmConfig(name="skills-on", skill_corpus_populated=True,
                  skill_repo_env_override=args.skill_repo_on),
        ArmConfig(name="skills-off", skill_corpus_populated=False,
                  skill_repo_env_override=skill_repo_off),
    )
    held_constant = {
        "sandbox_repo": args.repo,
        "model": args.model,
        "orchestrator_dispatch_shape":
            "spawn.py lint --issue <n> -C <repo>  (then, only if clean)  "
            "spawn.py --skills <skill-argument> \"<task>\" --issue <n> -C <repo>",
        "skill_name_argument": args.skill,
        "skill_argument_qualifier_note":
            "skills-on passes the bare name (identical to production); "
            "skills-off adds the skill-repo: source qualifier -- a "
            "harness-only manipulation-isolation control, not a claim "
            "about production orchestrator behavior (see module docstring)",
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
        "--skills", _skills_argument_for_arm(plan, arm),
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
                f"--follow --self-heal -C {plan.sandbox_repo}  "
                f"(timeout {plan.watch_timeout_s}s)")
    lines.append("")
    lines.append("Post-run instrumentation per arm (see collect_metrics()):")
    lines.append("  - H1 manipulation check (compute_h1_manipulation() / "
                  "gate_pair_on_h1(), re-operationalized 2026-09-02 -- see "
                  "docs/issue-3127/decisions/pre-registration.md's dated "
                  "amendment): did the on arm's session log record a real "
                  "Skill tool_use call naming the target skill, and did "
                  "the off arm's NOT (collect_skill_invocation(), parsing "
                  "the same <workspace>.session.*.log spawn.py already "
                  "produces). A pair that fails this is excluded from the "
                  "H2 quality comparison and the exclusion is recorded "
                  "with a reason, never silently reported alongside an "
                  "H2 figure")
    lines.append("  - directive-composition bytes: sum of "
                  "<workspace>/.on-the-record/directive/*.md file sizes -- "
                  "secondary environment-parity diagnostic ONLY, does not "
                  "gate H1 (construct-validity gap found by PR #3172: a "
                  "skill delivered via the runtime Skill tool never "
                  "touches this file set)")
    lines.append("  - token cost: matching entries in runs/ledger.jsonl "
                  "for this issue+skill")
    lines.append("  - verification rounds + defects found: count of "
                  "'repair round' / independent-verification PRs against "
                  "the arm's own issue, and defects each one's record cites")
    lines.append("  - wall-clock: this harness observes only the spawned "
                  "session's own session-end event (spawn.py watch "
                  "--follow's stop condition) -- under the unmodified "
                  "two-phase protocol that is AT MOST a phase-1 proposal "
                  "PR opening, never a merge. Reported as "
                  "wall_clock_to_pr_open_s under its true name; "
                  "wall_clock_to_landed_s is always null with an explicit "
                  "reason (see execute_arm())")
    lines.append("  - blind quality score: scrub_skill_slugs() then "
                  "evaluate_pair_blind() (wired into run_pair(), the same "
                  "blind-evaluator shape as scripts/issue-3041/"
                  "evaluate_pair.py), scored against the pair's own rubric, "
                  "gated on the pair passing the H1 check above")
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


def _extract_json_object(text: str):
    """Balanced {...} scan, same shape as scripts/issue-3041/
    evaluate_pair.py's own helper (duplicated rather than imported --
    issue-3041's directory is a different issue's own harness, and this
    repo has no shared scripts/ lib for cross-experiment helpers)."""
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


def _blind_prompt(task_text: str, rubric_text: str, doc1: str, doc2: str) -> str:
    return (
        "You are a blind evaluator. You did not write either document "
        "below, and you are not told which system, process, or person "
        "produced them.\n\n"
        f"TASK GIVEN TO BOTH WRITERS:\n{task_text}\n\n"
        f"SCORING RUBRIC (what a strong answer should contain):\n{rubric_text}\n\n"
        f"--- DOCUMENT 1 ---\n{doc1}\n--- END DOCUMENT 1 ---\n\n"
        f"--- DOCUMENT 2 ---\n{doc2}\n--- END DOCUMENT 2 ---\n\n"
        "Score DOCUMENT 1 and DOCUMENT 2 independently on a 1-10 scale for "
        "how well each satisfies the rubric above (structure and content "
        "only -- ignore length, tone, or formatting flourishes). Then "
        "state which document is better, or \"indistinguishable\" if the "
        "gap is not meaningful.\n\n"
        "Respond with ONLY a JSON object, no other text, no markdown "
        "fences:\n"
        '{"document_1_score": <int 1-10>, "document_2_score": <int 1-10>, '
        '"verdict": "document_1" | "document_2" | "indistinguishable", '
        '"reasoning": "<2-3 sentences>"}')


def _default_blind_evaluator(prompt: str) -> str:
    """Real evaluator call: a fresh `claude -p` with no tool access, same
    shape as scripts/issue-3041/evaluate_pair.py's own blind evaluator --
    it cannot inspect either workspace, so the prompt text itself is the
    only thing that can leak arm identity (see evaluate_pair_blind())."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", "sonnet", "--tools", "",
         "--setting-sources", "project,local", "--output-format", "json",
         "--max-budget-usd", "0.5"],
        capture_output=True, text=True, timeout=180)
    try:
        outer = json.loads(result.stdout)
        return outer.get("result", result.stdout)
    except json.JSONDecodeError:
        return result.stdout


def evaluate_pair_blind(task_text: str, rubric_text: str,
                         deliverable_on: str, deliverable_off: str,
                         known_slugs: list[str], evaluator_fn=None) -> dict:
    """Blind quality scorer (issue #3127 repair round, defect 3): wires
    `scrub_skill_slugs()` into an actual scoring call instead of leaving it
    defined and never invoked. `evaluator_fn(prompt) -> raw_response_text`
    is injectable (defaults to `_default_blind_evaluator`'s real `claude -p`
    call) so tests can verify blindness and scrubbing without a real
    subprocess or network call.

    Genuinely blind in two ways: (1) which document is "Document 1" vs
    "Document 2" is randomized per call, and the arm labels ("skills-on"/
    "skills-off") never appear anywhere in the prompt text handed to
    `evaluator_fn` -- only after the raw verdict comes back is it mapped
    back to an arm, in this function's own return value; (2) skill slugs
    are redacted from both deliverables before either is placed in the
    prompt (issue #3053's leak: skills-on deliverables cited their own
    skill slugs by name).

    Also scores the UNSCRUBBED text whenever the scrub actually changed
    something (replacement_count > 0 for either document) and records
    whether the resulting score moved -- "did scrubbing matter" is a
    reported, evidence-backed field, not assumed either way. When neither
    document mentions a known slug, scrubbing is a no-op and the second
    (unscrubbed) call is skipped, since there is nothing for it to test.
    """
    evaluator_fn = evaluator_fn or _default_blind_evaluator
    scrubbed_on, n_on = scrub_skill_slugs(deliverable_on, known_slugs)
    scrubbed_off, n_off = scrub_skill_slugs(deliverable_off, known_slugs)

    def _score_pair(text_on: str, text_off: str) -> dict:
        docs = [("skills-on", text_on), ("skills-off", text_off)]
        random.shuffle(docs)
        (label_1, doc1), (label_2, doc2) = docs
        prompt = _blind_prompt(task_text, rubric_text, doc1, doc2)
        raw = evaluator_fn(prompt)
        verdict = _extract_json_object(raw)
        if verdict is None:
            verdict = {"error": "unparsed", "raw": raw}
        return {"document_1_actual_arm": label_1,
                "document_2_actual_arm": label_2, "verdict": verdict}

    scrubbed_result = _score_pair(scrubbed_on, scrubbed_off)
    result = {
        "scrub_replacement_counts": {"skills-on": n_on, "skills-off": n_off},
        "scored_on_scrubbed_text": scrubbed_result,
    }
    if n_on == 0 and n_off == 0:
        result["scrub_changed_score"] = False
        result["scrub_changed_score_reason"] = (
            "no known skill slug appeared in either deliverable -- "
            "scrubbing was a no-op, nothing to compare")
        return result

    unscrubbed_result = _score_pair(deliverable_on, deliverable_off)
    result["scored_on_unscrubbed_text"] = unscrubbed_result

    def _scores_by_arm(scored: dict) -> dict:
        v = scored["verdict"]
        out = {}
        if "document_1_score" in v:
            out[scored["document_1_actual_arm"]] = v.get("document_1_score")
        if "document_2_score" in v:
            out[scored["document_2_actual_arm"]] = v.get("document_2_score")
        return out

    scrubbed_scores = _scores_by_arm(scrubbed_result)
    unscrubbed_scores = _scores_by_arm(unscrubbed_result)
    result["scrubbed_scores_by_arm"] = scrubbed_scores
    result["unscrubbed_scores_by_arm"] = unscrubbed_scores
    result["scrub_changed_score"] = scrubbed_scores != unscrubbed_scores
    return result


def collect_directive_bytes(workspace: Path | None) -> int | None:
    if workspace is None:
        return None
    directive_dir = workspace / ".on-the-record" / "directive"
    if not directive_dir.is_dir():
        return None
    return sum(p.stat().st_size for p in directive_dir.glob("*.md"))


def _find_latest_session_log(workspace: Path | None) -> Path | None:
    """Locate the most recent spawn.py-authored
    `<workspace>.session.<ts>.<pid>.log` stream-json tee for a workspace
    (issue #3127 H1 re-operationalization, 2026-09-02 consult -- see
    compute_h1_manipulation()'s docstring for why this replaced
    directive-composition bytes as the gating signal). A respawned
    session leaves multiple `.session.*.log` files next to the same
    workspace directory; the latest by mtime is the one whose events
    matter for a completed arm.
    """
    if workspace is None:
        return None
    parent = workspace.parent
    candidates = sorted(parent.glob(workspace.name + ".session.*.log"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def collect_skill_invocation(workspace: Path | None, skill_name: str,
                              dispatch_confirmed: bool = False) -> dict:
    """H1's manipulation-check evidence (re-operationalized 2026-09-02,
    issue #3127 consult, `runs/consult-logs/20260902T125610799701-
    948846.log`): whether the target skill was actually INVOKED via the
    Skill tool, read from an artifact the spawned session's own model
    generation does not author.

    Parses `<workspace>.session.<ts>.<pid>.log` -- spawn.py's own capture
    of the spawned CLI's raw stdout stream -- the exact same artifact
    `scripts/measure_skill_invocation.py` already parses for production
    skill-usage measurement (this function reuses that module's
    `analyze()` rather than re-deriving its regex/schema a second time).
    A `{"type":"tool_use","name":"Skill","input":{"skill":"<name>"}}`
    line in that stream is serialized by the `claude` CLI binary itself
    the instant the model's tool call happens -- the model's own
    generation has no code path that writes to this file directly; it
    can only ever cause a genuine entry to appear by actually invoking
    the Skill tool. (See docs/issue-3127/decisions/pre-registration.md's
    2026-09-02 amendment for the fuller forgeability comparison against
    the other three candidate artifacts the consult named, and the
    residual risk this does not close.)

    Also returns `mounted` -- the session's own init-event plugin list,
    i.e. availability, not invocation -- so callers can cross-check
    mounted-but-never-invoked or invoked-without-being-mounted as an
    internal-consistency signal (this re-operationalization's own
    instruction to cross-check against spawn.py's mounted-skill list for
    the arm; the init event's plugin list is populated from the same
    resolved-skill-sources spawn.py itself computes pre-session for the
    roster, see `_skill_roster_fields()` in skills.py).

    `dispatch_confirmed` (issue #3245 round 3 -- live-reproduced watch
    race: `execute_arm()` recorded `dispatch_returncode: 0` and
    `status: "watched-to-completion"` for both arms of a real pair, yet
    this function's old unconditional "never reached a dispatched,
    log-producing state" message still fired when the session log could
    not be found -- because the log had since been rotated/reclaimed
    from disk, not because the arm never ran. A caller that already knows
    dispatch+watch succeeded (`run_pair()` only reaches this gate after
    confirming both arms are `watched-to-completion`) must pass
    `dispatch_confirmed=True` so a missing log is reported as `unknown`
    -- unobservable now, never asserted as `never-dispatched` when
    positive proof of dispatch already exists elsewhere in the same
    result. Defaults to `False` so a caller with no such proof keeps the
    original, more conservative message.
    """
    log_path = _find_latest_session_log(workspace)
    if log_path is None:
        if dispatch_confirmed:
            return {"session_log": None, "mounted": None, "invoked": False,
                    "measured": False, "status": "unknown",
                    "reason": f"no {workspace}.session.*.log found, but "
                              "this arm's own dispatch+watch already "
                              "confirmed completion (dispatch_returncode=0, "
                              "watched-to-completion) -- the log is missing "
                              "now, not evidence the arm never ran; "
                              "invocation status is unknown, never "
                              "never-dispatched"}
        return {"session_log": None, "mounted": None, "invoked": False,
                "measured": False, "status": "never-dispatched",
                "reason": f"no {workspace}.session.*.log found -- the arm "
                          "never reached a dispatched, log-producing state"}
    result = _msi.analyze(workspace.name, str(log_path))
    if result.get("status") != "measured":
        return {"session_log": str(log_path), "mounted": None,
                "invoked": False, "measured": False,
                "reason": "measure_skill_invocation.analyze() returned "
                          f"status={result.get('status')!r} "
                          f"({result.get('reason')})"}
    mounted = result.get("mounted") or []
    invoked = skill_name in result.get("invoked_skills", [])
    return {"session_log": str(log_path), "mounted": mounted,
            "invoked": invoked, "measured": True,
            "mounted_but_not_invoked": skill_name in mounted and not invoked,
            "invoked_but_not_mounted": invoked and skill_name not in mounted,
            "reason": None}


def compute_h1_manipulation(workspace_on: Path | None,
                             workspace_off: Path | None,
                             skill_name: str | None,
                             dispatch_confirmed: bool = False) -> dict:
    """H1 enforcement, re-operationalized 2026-09-02 (issue #3127
    consult, `runs/consult-logs/20260902T125610799701-948846.log`,
    following PR #3172's construct-validity finding).

    Before this: H1 gated on `directive_composition_bytes` (sum of
    `<workspace>/.on-the-record/directive/*.md`). PR #3172 ran two real
    skills-on sessions (study-companion issues #19, #21) and found, with
    live evidence, that this proxy cannot see a skills-on/skills-off
    difference for a skill delivered via the runtime Skill-tool
    mechanism: both real workspaces held only the 8 session-universal
    baseline policy files in that directory -- byte-identical regardless
    of which skill was mounted. The metric could never fail this check
    even when the manipulation genuinely had not happened, and could
    never pass it when it genuinely had -- a construct-validity gap, not
    a measurement of the thing H1 claims to gate.

    The gating signal is now `collect_skill_invocation()`: did the on
    arm's session log record a real Skill tool_use call naming the
    target skill, and did the off arm's NOT. `directive_composition_bytes`
    is still collected, returned under `directive_bytes_parity`, but only
    as a secondary environment-parity diagnostic -- it no longer gates
    `differs` (pre-registration's decision rule, threshold, and sample
    size are unchanged; only this H1 observation changed -- see the
    pre-registration's dated amendment).

    Missing/unmeasurable session-log data for the ON arm is a
    manipulation-check FAILURE, same discipline the original proxy used
    for a missing workspace: there is nothing to prove the manipulation
    worked, so it is not credited as having worked. Missing/unmeasurable
    data for the OFF arm is compatible with "the off arm did not invoke
    the target skill" (absence of invocation evidence is itself evidence
    of non-invocation for an arm whose corpus was deliberately made
    empty) and does not by itself fail the gate -- but is recorded, never
    silently conflated with a genuinely-measured non-invocation.
    """
    directive_bytes_parity = {
        "on_bytes": collect_directive_bytes(workspace_on),
        "off_bytes": collect_directive_bytes(workspace_off),
        "note": "secondary environment-parity diagnostic only -- does "
                "NOT gate H1 (construct-validity gap found by PR #3172: "
                "a skill delivered via the runtime Skill tool never "
                "touches this file set, so identical bytes here is "
                "expected and uninformative, not a manipulation-check "
                "failure)",
    }
    if not skill_name:
        return {"directive_bytes_parity": directive_bytes_parity,
                "on_invocation": None, "off_invocation": None,
                "differs": False,
                "reason": "no skill_name supplied -- cannot compute the "
                          "invocation-based H1 check"}

    on_invocation = collect_skill_invocation(workspace_on, skill_name,
                                              dispatch_confirmed=dispatch_confirmed)
    off_invocation = collect_skill_invocation(workspace_off, skill_name,
                                               dispatch_confirmed=dispatch_confirmed)
    base = {"directive_bytes_parity": directive_bytes_parity,
            "on_invocation": on_invocation, "off_invocation": off_invocation}

    if not on_invocation["measured"]:
        unknown = on_invocation.get("status") == "unknown"
        return {**base, "differs": False,
                "h1_status": "unknown" if unknown else "never-dispatched",
                "reason": ("the skills-on arm's session log is unknown, not "
                            "never-dispatched -- dispatch+watch already "
                            f"confirmed this arm ran ({on_invocation['reason']})"
                            " -- excluded from H2 (missing evidence is not "
                            "credited as manipulation-held), but this is not "
                            "the same claim as the arm never having run"
                           ) if unknown else (
                            "the skills-on arm's session log could not be "
                            "found/parsed for a real Skill tool_use call "
                            f"({on_invocation['reason']}) -- treated as a "
                            "manipulation-check failure, not silently passed")}
    if not on_invocation["invoked"]:
        return {**base, "differs": False,
                "reason": "the skills-on arm's session log never recorded "
                          f"a Skill tool_use call naming {skill_name!r} -- "
                          "the manipulation did not happen even though "
                          "the arm was configured to receive it"}
    if off_invocation["invoked"]:
        return {**base, "differs": False,
                "reason": "the skills-off arm's session log ALSO recorded "
                          f"a Skill tool_use call naming {skill_name!r} -- "
                          "the corpus leaked through despite the "
                          "skill-repo: source-qualifier isolation (the "
                          "mirror image of issue #3053's retracted first, "
                          "zero-mount run)"}
    return {**base, "differs": True, "reason": None}


def gate_pair_on_h1(pair_id: str, workspace_on: Path | None,
                     workspace_off: Path | None, skill_name: str | None = None,
                     compute_h2=None, dispatch_confirmed: bool = False) -> dict:
    """Applies the H1 gate to one pair (issue #3127 repair round, defect 2):
    computes H1 via `compute_h1_manipulation()`; if it fails, the pair is
    excluded from H2 and the exclusion + reason are recorded in the
    returned dict -- `compute_h2` is NOT EVEN CALLED for an excluded pair,
    so a failed H1 can never produce an H2 figure. If H1 passes and
    `compute_h2` (a zero-arg callable) is supplied, its result is stored
    under "h2"; if not supplied, "h2" stays None with an explicit
    "h2_unavailable_reason", kept distinct from an H1-driven exclusion so
    the two "no H2" causes are never conflated in the results JSON.

    `skill_name` (re-operationalized 2026-09-02) is the target skill
    whose invocation compute_h1_manipulation() checks for; omitting it
    forces an automatic H1 failure (see compute_h1_manipulation()).
    """
    h1 = compute_h1_manipulation(workspace_on, workspace_off, skill_name,
                                  dispatch_confirmed=dispatch_confirmed)
    result = {"pair_id": pair_id, "h1": h1, "h1_manipulation_ok": h1["differs"]}
    if not h1["differs"]:
        result["excluded_from_h2"] = True
        result["exclusion_reason"] = (
            "H1 manipulation check failed: " + (h1.get("reason") or ""))
        result["h2"] = None
        return result
    result["excluded_from_h2"] = False
    result["exclusion_reason"] = None
    if compute_h2 is None:
        result["h2"] = None
        result["h2_unavailable_reason"] = "no H2 scorer supplied to gate_pair_on_h1()"
        return result
    result["h2"] = compute_h2()
    return result


def build_execute_results(plan: Plan, pair_results: list[dict]) -> dict:
    """Assembles the final results JSON from a real `--execute` run's
    per-pair results (issue #3127 repair round, defect 2): a pair excluded
    by the H1 gate (or with no H2 for any other reason) is listed under
    `pairs_excluded_from_h2` with its reason and NEVER contributes an H2
    figure to `pairs_included_in_h2` -- a results file that reported an H2
    number for a pair whose own H1 failed is exactly the defect this
    structure prevents.
    """
    included = [p for p in pair_results
                if not p.get("excluded_from_h2", True) and p.get("h2") is not None]
    excluded = [p for p in pair_results
                if p.get("excluded_from_h2", True) or p.get("h2") is None]
    return {
        "issue": 3127,
        "run_status": "executed",
        "pre_registration_ref": "docs/issue-3127/decisions/pre-registration.md",
        "pairs": pair_results,
        "pairs_included_in_h2": [p["pair_id"] for p in included],
        "pairs_excluded_from_h2": [
            {"pair_id": p["pair_id"],
             "reason": p.get("exclusion_reason") or p.get("h2_unavailable_reason")}
            for p in excluded
        ],
        "decision": (
            "no pairs passed the H1 manipulation check with a scored H2 -- "
            "nothing to compare against the pre-registered threshold"
            if not included else
            "see per-pair h2 verdicts in 'pairs'; combined-margin decision-"
            "rule arithmetic against docs/issue-3127/decisions/"
            "pre-registration.md's threshold (b) is computed over "
            "pairs_included_in_h2 only, by the session interpreting this "
            "file"),
    }


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
    """Real (non-dry-run) execution: lint, dispatch, then block on
    `spawn.py watch --follow` (contract v3 s22: a headless single-shot
    turn must consume what it delegates before ending -- spawn.py's own
    `--skills` dispatch path self-daemonizes, os.setsid() +
    start_new_session=True + stdio to devnull, spawn.py:4684-4749, so only
    the `watch` call afterward observes completion).

    Wall-clock (issue #3127 repair round, defect 4): the only stop
    condition this function (or `spawn.py watch --follow`) can observe is
    the spawned session's own session-end event (events.py's `_watch()`),
    which under the unmodified two-phase protocol is AT MOST a phase-1
    proposal PR opening -- never a merge to main. A headless single-shot
    harness cannot block through a later human-approval step, a phase-2
    build, and a merge without itself becoming a long-running blocking
    process outside contract v3 s22's own bound. Per the issue's own
    "record time-to-PR-open under its true name" fallback: this function
    reports `wall_clock_to_pr_open_s` (what it actually measures) and
    always sets `wall_clock_to_landed_s: None` with an explicit
    `landing_measurement_status` reason -- never relabels one as the
    other.
    """
    if not confirm_real_spawn:
        raise RuntimeError(
            "execute_arm() requires confirm_real_spawn=True -- this "
            "creates a real GitHub issue/branch/PR in plan.sandbox_repo "
            "and runs a real recursive claude session. Pass --execute "
            "--i-understand-this-spawns-real-sessions to the CLI.")
    landing_status = (
        "not_measured -- this harness observes only the spawned session's "
        "own session-end event, which under the unmodified two-phase "
        "protocol is at most a phase-1 proposal PR opening, not a merge to "
        "main; a headless single-shot session cannot block through a "
        "later human-approval + phase-2 build + merge (contract v3 s22). "
        "wall_clock_to_pr_open_s is the honest name for what was actually "
        "timed.")
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
                "wall_clock_to_pr_open_s": time.monotonic() - t0,
                "wall_clock_to_landed_s": None,
                "landing_measurement_status": landing_status,
                "dispatch_returncode": dispatch.returncode,
                "watch_timeout_s": plan.watch_timeout_s}
    wall_clock_to_pr_open_s = time.monotonic() - t0
    status = "watched-to-completion" if watch.returncode == 0 else "watch-failed"
    return {
        "arm": arm.name, "issue": issue, "status": status,
        "wall_clock_to_pr_open_s": wall_clock_to_pr_open_s,
        "wall_clock_to_landed_s": None,
        "landing_measurement_status": landing_status,
        "dispatch_returncode": dispatch.returncode,
        "watch_returncode": watch.returncode,
        "watch_stderr": watch.stderr if watch.returncode != 0 else None,
    }


def _os_environ() -> dict:
    import os
    return dict(os.environ)


def arm_workspace_dir(plan: Plan, issue: int) -> Path | None:
    """The workspace directory a real `--execute` run's arm lands in --
    reuses spawn.py's OWN `_workspace_target_path()` rather than
    re-deriving the `<repo>-issue-<n>-<skill>` naming convention a second
    time, so this harness cannot drift from the real layout spawn.py
    itself computes."""
    _, work = _spawn_mod._workspace_target_path(
        plan.sandbox_repo, issue, plan.skill_name)
    return Path(work) if work else None


def _default_deliverable_fetcher(plan: Plan, issue: int) -> str | None:
    """Best-effort: read the arm's own PR body via `gh pr view`, run inside
    the sandbox repo and keyed by the issue-scoped branch name the
    role-handoff contract uses (`issue-<n>/<skill>`). Returns None (not a
    fabricated empty string) when no such PR is found, so a missing
    deliverable is visibly missing rather than silently scored as empty."""
    branch = f"issue-{issue}/{plan.skill_name}"
    r = subprocess.run(
        ["gh", "pr", "view", branch, "--json", "body", "-q", ".body"],
        cwd=plan.sandbox_repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def run_pair(plan: Plan, pair: PairPlan, on_issue: int, off_issue: int,
             confirm_real_spawn: bool, known_slugs: list[str],
             deliverable_fetcher=None, evaluator_fn=None) -> dict:
    """Real per-pair orchestration entry point (issue #3127 repair round,
    defects 2+3): dispatches+watches both arms via `execute_arm()`, gates
    the quality comparison behind the H1 manipulation check via
    `gate_pair_on_h1()`, and -- only for pairs that pass H1 -- calls
    `evaluate_pair_blind()` (skill slugs scrubbed first) as the H2 scorer.
    `deliverable_fetcher`/`evaluator_fn` are injectable so tests can
    exercise this without a real spawn.py dispatch or a real `claude -p`
    call; defaults are `_default_deliverable_fetcher` /
    `_default_blind_evaluator`.
    """
    deliverable_fetcher = deliverable_fetcher or _default_deliverable_fetcher
    arm_on, arm_off = plan.arms
    result_on = execute_arm(plan, pair, arm_on, on_issue, confirm_real_spawn)
    result_off = execute_arm(plan, pair, arm_off, off_issue, confirm_real_spawn)
    arm_results = {"skills-on": result_on, "skills-off": result_off}

    if result_on.get("status") != "watched-to-completion" or \
            result_off.get("status") != "watched-to-completion":
        return {
            "pair_id": pair.pair_id, "issue_skills_on": on_issue,
            "issue_skills_off": off_issue, "arm_results": arm_results,
            "h1": None, "h1_manipulation_ok": False,
            "excluded_from_h2": True,
            "exclusion_reason": (
                "at least one arm did not reach watched-to-completion "
                f"(skills-on status={result_on.get('status')!r}, "
                f"skills-off status={result_off.get('status')!r}) -- no "
                "workspace to compare, H1 cannot be checked"),
            "h2": None,
        }

    workspace_on = arm_workspace_dir(plan, on_issue)
    workspace_off = arm_workspace_dir(plan, off_issue)

    def compute_h2():
        deliverable_on = deliverable_fetcher(plan, on_issue)
        deliverable_off = deliverable_fetcher(plan, off_issue)
        if deliverable_on is None or deliverable_off is None:
            return {
                "h2_unavailable": True,
                "h2_unavailable_reason":
                    "deliverable fetch failed for at least one arm -- "
                    f"skills-on={'ok' if deliverable_on is not None else 'missing'}, "
                    f"skills-off={'ok' if deliverable_off is not None else 'missing'}",
            }
        task_text = pair.task_file.read_text(encoding="utf-8").strip() \
            if pair.task_file.exists() else ""
        rubric_file = DEFAULT_RUBRICS_DIR / f"{pair.pair_id}.md"
        rubric_text = rubric_file.read_text(encoding="utf-8").strip() \
            if rubric_file.exists() else ""
        return evaluate_pair_blind(task_text, rubric_text, deliverable_on,
                                    deliverable_off, known_slugs,
                                    evaluator_fn=evaluator_fn)

    gated = gate_pair_on_h1(pair.pair_id, workspace_on, workspace_off,
                             skill_name=plan.skill_name, compute_h2=compute_h2,
                             dispatch_confirmed=True)
    if gated.get("h2", {}) and gated["h2"].get("h2_unavailable"):
        gated["h2_unavailable_reason"] = gated["h2"]["h2_unavailable_reason"]
        gated["h2"] = None
    gated["issue_skills_on"] = on_issue
    gated["issue_skills_off"] = off_issue
    gated["arm_results"] = arm_results
    return gated


def emit_not_executed_results(plan: Plan) -> dict:
    """Not-executed results skeleton -- the single source of truth for
    `docs/issue-3127/_assets/consumer-path-results.json` while no
    `--execute` run has happened yet (issue #3127 repair round 2, PR
    #3158 finding: this function was never called from anywhere, so the
    committed skeleton drifted from it -- in particular it kept the
    pre-defect-4 single `wall_clock_to_landed_s` field with no
    `wall_clock_to_pr_open_s` and no `landing_measurement_status` reason.
    Wired into `main()` via `--emit-not-executed` so the file can be
    regenerated from this function instead of hand-edited out of sync
    with it.
    """
    landing_status = (
        "not measured -- see run_status; this harness can only ever "
        "measure time-to-PR-open, not time-to-landed -- see execute_arm()")
    arms = {arm.name: {
        "quality_blind_score": None,
        "wall_clock_to_pr_open_s": None,
        "wall_clock_to_landed_s": None,
        "landing_measurement_status": landing_status,
        "tokens_total": None,
        "directive_composition_bytes": None,
        "verification_rounds": None,
        "verification_defects_found": None,
        "note": "not measured -- see run_status",
    } for arm in plan.arms}
    arms["skills-on"]["bm25_selection_position"] = None
    return {
        "issue": 3127,
        "run_status": "not_executed",
        "run_status_reason": (
            "A later session (2026-09-02, this run) had explicit operator "
            "authorization to execute for real (CORE_BUILD_NOW=1, and the "
            "prior session's confirmation blocker was resolved) and "
            "located the pre-provisioned sandbox repo "
            "(JiwonJung94/study-companion -- spawn.py-init'd, docs/specs/"
            "approvers.md present, docs/issue-1 and docs/issue-5 already "
            "matching this harness's pair task text). The dry-run plan "
            "was verified to match the pre-registration (arms, "
            "held-constant factors, H1 gate, blind scorer, wall-clock "
            "naming). Execution then hit a hard, mechanically-enforced "
            "block distinct from the prior session's caution-based one: "
            "creating the 4 seed GitHub issues `--issue-map` requires "
            "(one skills-on + one skills-off issue per registered pair) "
            "was refused live by this repo's own gh-guard pretooluse "
            "hook -- 'issues are the user's requirement backlog, "
            "user-authored only (contract v3 s9) -- no skill touches "
            "them' (two-account model, contract v3 s8) -- reproduced "
            "verbatim against `gh issue create --repo "
            "JiwonJung94/study-companion ...` this session. This is a "
            "deliberate safety boundary (skill sessions cannot author "
            "requirement-backlog issues in ANY repo, not just the "
            "orchestrator's own), not a caution call this session made "
            "unilaterally, and it was not bypassed -- no alternate gh "
            "auth, no hook skip. It structurally means no skill session "
            "under this protocol can complete this harness's --execute "
            "path alone: the seed issues for --issue-map must be created "
            "by the human operator (or another user-authored channel) "
            "out-of-band, before a skill session's spawn.py dispatch + "
            "watch --follow can run. The self-daemonization concern from "
            "the prior session's reasoning is otherwise resolved -- "
            "execute_arm() calls `spawn.py watch --follow` and blocks "
            "the caller for real, so a session with the seed issues "
            "already in hand could complete a live run within one "
            "sitting."),
        "pre_registration_ref": "docs/issue-3127/decisions/pre-registration.md",
        "pairs_registered": [p.pair_id for p in plan.pairs],
        "threshold": {
            "primary_metric": "blind deliverable score margin "
                               "(sum(skills-on) - sum(skills-off)) across "
                               "registered pairs",
            "decision_rule": "better if skills-on wins >=3 of pairs AND "
                              "combined margin >=3; worse under the "
                              "symmetric condition; indistinguishable "
                              "otherwise",
            "guardrail": "skills-on wall-clock-to-landed must not exceed "
                         "skills-off's by more than 50% combined, AND "
                         "skills-on verification-round count must not "
                         "exceed skills-off's by more than 1 round "
                         "combined -- a primary-metric win alongside a "
                         "breached guardrail is reported as a breach, not "
                         "an unqualified win",
            "sample_size": f"n={len(plan.pairs)} pairs registered for "
                            f"this run ({', '.join(p.pair_id for p in plan.pairs)}), "
                            "extensible to n=4",
            "threshold_met": None,
            "threshold_met_reason": "unmeasured -- no data was collected "
                                     "this session, see run_status",
        },
        "confound_check": {
            "question": "issue #3091's diagnosis: does "
                         "test/test_spawn_cross_family_skill_selection.py"
                         "::Bm25CrossFamilySkillMatchesTest::"
                         "test_family_skill_never_returned_as_cross_family_candidate "
                         "pin a family-skill exclusion that issue #2507 "
                         "intentionally removed, narrowing the candidate "
                         "pool #3053 measured against?",
            "finding": "current pool is NOT narrowed by this rule -- "
                       "#3053's selection numbers do not need re-deriving "
                       "on this account",
            "evidence": [
                "pipeline.py's _cross_family_candidate_corpus() docstring "
                "states verbatim: '이슈 #2507: `_ROLE_SKILLS[role]` "
                "exclusion 은 없앴다 -- 고정 role->skill 표가 더 이상 "
                "family를 정의하지 않으므로... 후보 풀을 role 기준으로 "
                "미리 좁힐 이유가 사라졌다.' The function body confirms "
                "this: it deletes the `skill` parameter (`del skill`) and "
                "only excludes `_sp._STATIC_POLICY_SKILLS` (policy skills "
                "like work-in-english), never a role-family set.",
                "test/test_spawn_cross_family_skill_selection.py"
                "::Bm25CrossFamilySkillMatchesTest::"
                "test_family_skill_never_returned_as_cross_family_candidate "
                "currently FAILS live (re-run this session via the "
                "lint-test-on-edit hook on Read of that file) -- it "
                "asserts the pre-#2507 exclusion behavior against the "
                "post-#2507 implementation, confirming the exclusion is "
                "gone from the code, not just from the docstring's claim "
                "about it.",
                "commit dates: issue #2507's landing commits (0879f12a, "
                "28e9c1e9) are dated 2026-08-26; issue #3053's actual "
                "paired run landed in commit 573e7382 dated 2026-09-02 -- "
                "#3053 ran against main after #2507 had already removed "
                "the exclusion, so its candidate pool already reflected "
                "current (non-excluding) behavior.",
            ],
            "separate_defect_noted_not_fixed_here": (
                "the stale, currently-failing unit test itself (asserting "
                "behavior #2507 removed) is a test-currency defect "
                "independent of runtime pool composition -- already "
                "covered by issue #3091's diagnosis scope, not fixed in "
                "this PR (out of this issue's scope)."),
        },
        "slug_scrub": {
            "implemented": "scripts/issue-3127/run_consumer_pair.py"
                            "::scrub_skill_slugs()",
            "applied_this_session": False,
            "reason": "no real deliverables exist to scrub or score "
                      "(run_status: not_executed) -- whether the scrub "
                      "changes any score is unmeasured, not zero-effect",
        },
        "arms": arms,
        "decision": "unmeasured -- not a null result (no data was collected "
                     "this session); see power statement in pre-registration.md",
        "power_statement": (
            "At the registered n=2 pairs, a binary per-pair win/loss/tie "
            "read has no meaningful statistical power to distinguish a "
            "true small effect from noise under any reasonable "
            "significance convention. The registered decision rule is a "
            "directional threshold (met/not-met against a fixed +/-3-"
            "point margin, a 50% wall-clock guardrail, and a 1-round "
            "guardrail), never a significance test. Had this session "
            "executed the harness and returned 'indistinguishable', that "
            "would mean the sample could not resolve an effect smaller "
            "than the registered 3-point margin (roughly one grade-band "
            "shift per pair on the rubric scale) -- it would not mean no "
            "such effect exists. Because no run occurred at all, this "
            "JSON reports zero information about effect size in either "
            "direction, not a null."),
        "next_steps_for_a_future_executing_session": [
            "sandbox repo already provisioned: JiwonJung94/study-companion "
            "(spawn.py-init'd, docs/specs/approvers.md present, "
            "docs/issue-1 + docs/issue-5 already match this harness's "
            "pair task text) -- no need to provision a new one",
            "the human operator (not a skill session -- gh-guard refuses "
            "issue creation from a skill session, contract v3 s8/s9) "
            "must create the 2 registered pairs' issues (skills-on issue "
            "+ skills-off issue per pair, 4 total) in that sandbox with "
            "identical body text except the arm label, then hand the "
            "resulting issue numbers to the executing session via "
            "--issue-map",
            "run scripts/issue-3127/run_consumer_pair.py --execute "
            "--i-understand-this-spawns-real-sessions --repo <local clone "
            "of JiwonJung94/study-companion> --issue-map "
            "'01-study-groups:<on>:<off>,02-onboarding-experiment:<on>:<off>' "
            "in a session with enough turn budget to block on spawn.py "
            "watch --follow per arm (see execute_arm()); commit results "
            "after each pair completes",
            "run scrub_skill_slugs() against each arm's deliverable "
            "before scoring, and report whether the scrub changed "
            "either pair's score",
            "re-run scripts/issue-3127/verify_preregistration.py before "
            "interpreting the populated results -- the pre-registration "
            "commit that already exists on this branch remains valid and "
            "must not be re-written after seeing the new data",
        ],
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
    ap.add_argument("--skill-repo-off", default=None,
                     help="MUSTER_SKILL_REPO value for the skills-off arm -- "
                          "if unset (default), this harness creates a fresh "
                          "temp dir itself via build_stub_skill_repo(), "
                          "containing only the named skill's frontmatter. "
                          "The skills-off arm's --skills argument always "
                          "adds the skill-repo: qualifier (see "
                          "_skills_argument_for_arm()) so resolution never "
                          "reads ~/.claude/skills, installed plugins, or "
                          "the target repo's own .claude/skills -- see the "
                          "module docstring for why the old literal-string "
                          "default and unqualified name did not achieve "
                          "'corpus present but empty' in a real environment.")
    ap.add_argument("--watch-timeout", type=int, default=1800)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--emit-not-executed", action="store_true",
                     help="write emit_not_executed_results()'s output to "
                          "--out and exit -- regenerates the committed "
                          "not-yet-run results skeleton from this module "
                          "instead of hand-editing it out of sync with "
                          "the code (issue #3127 repair round 2)")
    ap.add_argument("--i-understand-this-spawns-real-sessions",
                     action="store_true", dest="confirm_real_spawn",
                     help="required alongside --execute: this creates real "
                          "GitHub issues/PRs in --repo and runs real "
                          "recursive claude sessions")
    ap.add_argument("--issue-map", default=None,
                     help="required to actually orchestrate a pair under "
                          "--execute: '<pair_id>:<on_issue>:<off_issue>,...' "
                          "-- this harness does not create GitHub issues "
                          "itself (unchanged limitation, left to the "
                          "caller); a pair with no entry here is reported "
                          "as skipped, not silently dropped")
    ap.add_argument("--out", default=str(
        ROOT / "docs" / "issue-3127" / "_assets" / "consumer-path-results.json"))
    args = ap.parse_args()

    if not args.dry_run and not args.execute and not args.emit_not_executed:
        print("error: pass --dry-run to inspect the plan, --emit-not-"
              "executed to (re)write the not-yet-run results skeleton, or "
              "--execute (with --i-understand-this-spawns-real-sessions) "
              "to run it for real.", file=sys.stderr)
        return 2

    plan = build_plan(args)

    if args.dry_run:
        print(render_dry_run(plan))
        return 0

    if args.emit_not_executed:
        results = emit_not_executed_results(plan)
        Path(args.out).write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(f"wrote {args.out}")
        return 0

    if not args.confirm_real_spawn:
        print("error: --execute requires "
              "--i-understand-this-spawns-real-sessions", file=sys.stderr)
        return 2

    # Real execution path: intentionally not exercised by this issue's
    # acceptance check. This harness does not call `gh issue create`
    # itself (unchanged limitation) -- a pair only actually dispatches if
    # the caller supplies its real issue numbers via --issue-map; a pair
    # with no entry is reported as skipped, not silently dropped.
    issue_map = _parse_issue_map(args.issue_map)
    known_slugs = [plan.skill_name]
    pair_results: list[dict] = []
    for pair in plan.pairs:
        mapping = issue_map.get(pair.pair_id)
        if mapping is None:
            print(f"[plan] no --issue-map entry for pair {pair.pair_id} -- "
                  "cannot orchestrate without real issue numbers (this "
                  "harness does not call `gh issue create`); skipping real "
                  "dispatch for this pair.", file=sys.stderr)
            pair_results.append({
                "pair_id": pair.pair_id, "status": "no-issue-map-entry",
                "excluded_from_h2": True,
                "exclusion_reason": "no --issue-map entry for this pair",
                "h2": None,
            })
            continue
        on_issue, off_issue = mapping
        pair_results.append(run_pair(plan, pair, on_issue, off_issue,
                                      args.confirm_real_spawn, known_slugs))

    results = build_execute_results(plan, pair_results)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


def _parse_issue_map(raw: str | None) -> dict[str, tuple[int, int]]:
    """`--issue-map` CLI value: '<pair_id>:<on_issue>:<off_issue>,...'. This
    harness does not call `gh issue create` itself (unchanged from the
    original build session's documented limitation) -- real issue
    allocation is left to the caller, who supplies the resulting numbers
    here so `run_pair()` has something real to dispatch against."""
    if not raw:
        return {}
    out: dict[str, tuple[int, int]] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        pair_id, on_s, off_s = entry.split(":")
        out[pair_id] = (int(on_s), int(off_s))
    return out


if __name__ == "__main__":
    sys.exit(main())
