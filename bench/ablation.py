#!/usr/bin/env python3
"""Quality-ablation runner (issue #2130) — arm B (bare model) + scoresheets.

Protocol (inherits bench/run.py's contract verbatim):
  * The hidden answer key (bench/ablation-tasks/<task>/key/) NEVER enters a
    run workspace. Only the fixture template is copied; the key stays home.
  * No automated grading, no pass/fail aggregation anywhere. The runner
    emits a scoresheet whose verdict cells are BLANK; a human (or a
    documented, labeled independent grader session) fills them.
  * Both arms get the same task text, same model, same --max-turns budget.

Arms:
  B (this runner): `claude -p --model <m> --max-turns <n>
    --permission-mode bypassPermissions` in a fresh clone of the fixture,
    with every plugin disabled — no hooks, no records, no rulebooks.
  A (the real pipeline): runs through the live board via spawn.py; this
    runner only PREPARES it (`prepare-a` prints the fixture-instantiation
    steps and the exact spawn.py command per task). It never invokes
    spawn.py itself.

Usage:
  python3 bench/ablation.py list
  python3 bench/ablation.py run-b --task t01-version-bugfix --reps 2
  python3 bench/ablation.py prepare-a --task t01-version-bugfix
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = Path(__file__).resolve().parent / "ablation-tasks"

# Same budget/model both arms — arm A's spawn command must repeat these.
DEFAULT_MODEL = "sonnet"       # routing default for implementation single-phase
DEFAULT_MAX_TURNS = 200

# Directories that must never be copied into a run workspace. "key" is the
# hidden answer key; "answers" mirrors bench/run.py's convention; caches are
# noise that would leak the authoring environment.
EXCLUDED_FROM_WORKSPACE = ("key", "answers", "__pycache__", ".git")


# --- task loading -------------------------------------------------------

def load_task(task_id: str) -> dict:
    d = TASKS_DIR / task_id
    if not d.is_dir():
        raise SystemExit(f"unknown task: {task_id} (see `ablation.py list`)")
    meta = json.loads((d / "meta.json").read_text())
    meta["dir"] = str(d)
    meta["requirement"] = (d / meta["requirement_file"]).read_text().strip()
    return meta


def load_key(task_id: str) -> dict:
    """The hidden key — read only by the scoresheet emitter, never copied."""
    return json.loads((TASKS_DIR / task_id / "key" / "key.json").read_text())


def list_tasks() -> list:
    return sorted(p.name for p in TASKS_DIR.iterdir()
                  if p.is_dir() and (p / "meta.json").exists())


# --- workspace prep (shared key-exclusion mechanics) --------------------

def prepare_workspace(task: dict, dest: Path) -> Path:
    """Clone the task's fixture template to `dest` and git-init it.

    The answer key lives under bench/ablation-tasks/<task>/key/ — a
    different tree entirely — and the copy additionally ignores any
    key/answers directory defensively, so the invariant holds even if a
    future fixture grows one. Raises if the invariant is violated.
    """
    fixture = ROOT / task["fixture"]
    if not fixture.is_dir():
        raise SystemExit(f"fixture template missing: {fixture}")
    shutil.copytree(fixture, dest,
                    ignore=shutil.ignore_patterns(*EXCLUDED_FROM_WORKSPACE))
    assert_no_key_material(dest)
    subprocess.run(["git", "init", "-q"], cwd=dest, check=True)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True,
                   capture_output=True)
    subprocess.run(["git", "-c", "user.email=bench@example.com",
                    "-c", "user.name=bench", "commit", "-qm", "ablation fixture"],
                   cwd=dest, check=True, capture_output=True)
    return dest


def assert_no_key_material(workspace: Path) -> None:
    """The key-exclusion invariant, checked, not assumed."""
    leaks = [str(p) for p in workspace.rglob("*")
             if p.is_dir() and p.name in ("key", "answers")]
    leaks += [str(p) for p in workspace.rglob("key.json")]
    leaks += [str(p) for p in workspace.rglob("key.md")]
    if leaks:
        raise RuntimeError(f"answer-key material leaked into workspace: {leaks}")


def disabled_plugins_settings(out_dir: Path, name: str) -> Path:
    """Arm B must run with zero plugins — same blocking bench/run.py does."""
    settings_path = Path.home() / ".claude" / "settings.json"
    enabled = {}
    if settings_path.exists():
        enabled = json.loads(settings_path.read_text()).get("enabledPlugins", {})
    sf = out_dir / f"{name}-settings.json"
    sf.write_text(json.dumps(
        {"enabledPlugins": {k: False for k in enabled}}))
    return sf


# --- stream-json parsing ------------------------------------------------

def parse_stream_json(text: str) -> dict:
    """Pull the terminal `result` event out of a --output-format stream-json
    log. Returns {"cost_usd", "num_turns", "duration_ms", "result_text",
    "is_error", "found"} — all None/False when no result event exists
    (crash, kill): the scoresheet then says so instead of fabricating."""
    result = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("type") == "result":
            result = obj
    if result is None:
        return {"found": False, "cost_usd": None, "num_turns": None,
                "duration_ms": None, "result_text": None, "is_error": None}
    return {
        "found": True,
        "cost_usd": result.get("total_cost_usd"),
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "result_text": result.get("result"),
        "is_error": bool(result.get("is_error")),
    }


# --- fabrication check --------------------------------------------------

CLAIM_PATTERNS = [
    # sentences naming a test / test file / test run
    re.compile(r"[^.\n]*\btests?\b[^.\n]*", re.IGNORECASE),
    # sentences naming a concrete file path
    re.compile(r"[^.\n]*\b[\w./-]+\.(?:py|md|toml|json|txt)\b[^.\n]*"),
    # execution claims
    re.compile(r"[^.\n]*\b(?:ran|executed|verified|passes|passing|confirmed)\b[^.\n]*",
               re.IGNORECASE),
]


def extract_claims(result_text: str) -> list:
    """Every claim in an arm's final output that names a test/artifact or an
    execution. One row per claim; the adjudicator fills 'artifact_exists'
    and 'runnable' — the runner never judges them itself."""
    if not result_text:
        return []
    seen, claims = set(), []
    for pat in CLAIM_PATTERNS:
        for m in pat.finditer(result_text):
            claim = " ".join(m.group(0).split()).strip()
            if len(claim) < 15 or claim in seen:
                continue
            seen.add(claim)
            claims.append({"claim": claim, "artifact_exists": None,
                           "runnable": None})
    return claims


# --- arm B run ----------------------------------------------------------

def run_arm_b(task: dict, rep: int, out: Path, model: str,
              max_turns: int) -> dict:
    work = out / f"b-{rep}-workspace"
    prepare_workspace(task, work)
    sf = disabled_plugins_settings(out, f"b-{rep}")
    cmd = ["claude", "-p", "--settings", str(sf), "--model", model,
           "--max-turns", str(max_turns),
           "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "--verbose"]
    log = out / f"b-{rep}.stream.jsonl"
    t0 = time.monotonic()
    with log.open("w") as f:
        proc = subprocess.run(cmd, cwd=work, input=task["requirement"],
                              text=True, stdout=f, stderr=subprocess.STDOUT,
                              env={**os.environ})
    wall_clock_sec = round(time.monotonic() - t0, 1)
    assert_no_key_material(work)  # still true after the run

    parsed = parse_stream_json(log.read_text())
    touched = subprocess.run(["git", "status", "--porcelain", "-uall"],
                             cwd=work, capture_output=True, text=True
                             ).stdout.splitlines()
    return {
        "arm": "B", "rep": rep, "exit": proc.returncode,
        "model": model, "max_turns_budget": max_turns,
        "wall_clock_sec": wall_clock_sec,
        "cost_usd": parsed["cost_usd"],
        "turns": parsed["num_turns"],
        "cli_duration_ms": parsed["duration_ms"],
        "result_found": parsed["found"],
        "is_error": parsed["is_error"],
        "workspace": str(work), "stream_log": log.name,
        "files_touched": [t[3:] for t in touched if t.strip()],
        "final_output": parsed["result_text"],
    }


# --- scoresheet emission (JSON + markdown twin) -------------------------

def emit_scoresheet(task: dict, run: dict, out: Path) -> tuple:
    """One scoresheet per run. Verdict cells are BLANK (null / '') by
    contract — the runner never grades."""
    key = load_key(task["id"])
    sheet = {
        "protocol_note": ("verdict cells are intentionally blank; a human "
                          "or a documented independent grader session fills "
                          "them — the runner does not grade (bench/run.py "
                          "contract)"),
        "task": task["id"], "class": task["class"],
        "fixture": task["fixture"], "arm": run["arm"], "rep": run["rep"],
        "model": run["model"], "max_turns_budget": run["max_turns_budget"],
        "metrics": {
            "wall_clock_sec": run["wall_clock_sec"],
            "cost_usd": run["cost_usd"],
            "turns": run["turns"],
            "exit_code": run["exit"],
            "result_event_found": run["result_found"],
            "is_error": run["is_error"],
        },
        "requirement_met": [
            {"id": a["id"], "behavior": a["behavior"], "verdict": None,
             "evidence": None}
            for a in key["acceptance"]
        ],
        "fabrication_check": extract_claims(run["final_output"]),
        "files_touched": run["files_touched"],
        "adjudication_guidance": key["adjudication"],
        "workspace": run["workspace"],
        "stream_log": run["stream_log"],
    }
    name = f"scoresheet-{task['id']}-{run['arm']}-{run['rep']}"
    jpath = out / f"{name}.json"
    jpath.write_text(json.dumps(sheet, ensure_ascii=False, indent=2))

    md = [f"# Scoresheet — {task['id']} · arm {run['arm']} · rep {run['rep']}",
          "",
          "> Verdict cells are BLANK by protocol: the adjudicator fills them. "
          "The runner never grades.",
          "",
          f"- class: {task['class']}  ·  fixture: `{task['fixture']}`",
          f"- model: {run['model']}  ·  max-turns budget: {run['max_turns_budget']}",
          f"- wall-clock: {run['wall_clock_sec']}s  ·  cost_usd: {run['cost_usd']}"
          f"  ·  turns: {run['turns']}  ·  exit: {run['exit']}",
          f"- workspace: `{run['workspace']}`  ·  stream log: `{run['stream_log']}`",
          "", "## Requirement-met (one row per hidden-key acceptance item)", "",
          "| id | behavior | verdict | evidence |", "|---|---|---|---|"]
    for a in key["acceptance"]:
        md.append(f"| {a['id']} | {a['behavior']} |  |  |")
    md += ["", f"Adjudication guidance: {key['adjudication']}", "",
           "## Fabrication check (claims naming a test/artifact/execution)", "",
           "| claim | artifact exists? | runnable? |", "|---|---|---|"]
    claims = sheet["fabrication_check"]
    if claims:
        for c in claims:
            escaped = c["claim"].replace("|", "\\|")
            md.append(f"| {escaped} |  |  |")
    else:
        md.append("| (no artifact-naming claims found in final output) | — | — |")
    md += ["", "## Files touched", ""]
    md += [f"- `{f}`" for f in run["files_touched"]] or ["- (none)"]
    md.append("")
    mpath = out / f"{name}.md"
    mpath.write_text("\n".join(md))
    return jpath, mpath


# --- arm A preparation (documentation only; never executed here) --------

def arm_a_plan(task: dict, model: str, max_turns: int) -> str:
    tdir = Path(task["dir"]).relative_to(ROOT)
    return (
        f"# Arm A ({task['id']}) — run by the ORCHESTRATOR through the real board\n"
        f"# 1. Instantiate a fresh fixture clone (same mechanics as arm B):\n"
        f"#      python3 -c \"import sys; sys.path.insert(0, 'bench'); "
        f"import ablation; ablation.prepare_workspace("
        f"ablation.load_task('{task['id']}'), "
        f"__import__('pathlib').Path('/tmp/ablation-{task['id']}-a-<rep>'))\"\n"
        f"# 2. File the issue on the fixture host using {tdir}/issue.md as the body\n"
        f"#    (or pass the requirement text directly as the spawn task).\n"
        f"# 3. Spawn — same model tier and turn budget as arm B:\n"
        f"python3 spawn.py implementation \"$(cat {tdir}/requirement.md)\" "
        f"-C /tmp/ablation-{task['id']}-a-<rep> "
        f"--single-phase --model {model} --max-turns {max_turns} --unattended\n"
        f"# 4. After the run: emit the arm-A scoresheet from the transcript's\n"
        f"#    result event and the workspace:  python3 bench/ablation.py "
        f"emit-a --task {task['id']} --rep <rep> "
        f"--workspace /tmp/ablation-{task['id']}-a-<rep> --stream-log <log> --out <dir>\n"
    )


def emit_arm_a_sheet(task: dict, rep: int, workspace: str, stream_log: str,
                     out: Path, model: str, max_turns: int) -> tuple:
    """Post-hoc scoresheet for an arm-A run the orchestrator executed."""
    log_text = Path(stream_log).read_text() if Path(stream_log).exists() else ""
    parsed = parse_stream_json(log_text)
    touched = []
    if Path(workspace).is_dir():
        touched = [t[3:] for t in subprocess.run(
            ["git", "status", "--porcelain", "-uall"], cwd=workspace,
            capture_output=True, text=True).stdout.splitlines() if t.strip()]
    run = {"arm": "A", "rep": rep, "exit": None, "model": model,
           "max_turns_budget": max_turns,
           "wall_clock_sec": None,  # adjudicator fills from board timestamps
           "cost_usd": parsed["cost_usd"], "turns": parsed["num_turns"],
           "cli_duration_ms": parsed["duration_ms"],
           "result_found": parsed["found"], "is_error": parsed["is_error"],
           "workspace": workspace, "stream_log": stream_log,
           "files_touched": touched, "final_output": parsed["result_text"]}
    return emit_scoresheet(task, run, out)


# --- CLI ----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("run-b", "prepare-a", "emit-a"):
        p = sub.add_parser(name)
        p.add_argument("--task", required=True)
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
        if name == "run-b":
            p.add_argument("--reps", type=int, default=1)
            p.add_argument("--out", default=None)
        if name == "emit-a":
            p.add_argument("--rep", type=int, required=True)
            p.add_argument("--workspace", required=True)
            p.add_argument("--stream-log", required=True)
            p.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.cmd == "list":
        for t in list_tasks():
            meta = load_task(t)
            print(f"{t}  [{meta['class']}]  fixture={meta['fixture']}")
        return 0

    task = load_task(a.task)
    if a.cmd == "prepare-a":
        print(arm_a_plan(task, a.model, a.max_turns))
        return 0
    if a.cmd == "emit-a":
        j, m = emit_arm_a_sheet(task, a.rep, a.workspace, a.stream_log,
                                Path(a.out), a.model, a.max_turns)
        print(f"scoresheet: {j}\n            {m}")
        return 0

    # resolve() because `claude` runs with cwd=<workspace>: a relative
    # --settings/--out path would break out from under it.
    out = (Path(a.out).resolve() if a.out else Path(
        tempfile.mkdtemp(prefix=f"ablation-{a.task}-")))
    out.mkdir(parents=True, exist_ok=True)
    print(f"task {a.task}  arm B  reps {a.reps}  model {a.model}  "
          f"budget {a.max_turns}  →  {out}", file=sys.stderr)
    for i in range(1, a.reps + 1):
        print(f"  B-{i} …", file=sys.stderr, flush=True)
        run = run_arm_b(task, i, out, a.model, a.max_turns)
        j, m = emit_scoresheet(task, run, out)
        print(f"  B-{i}  exit {run['exit']}  wall {run['wall_clock_sec']}s  "
              f"cost {run['cost_usd']}  turns {run['turns']}\n"
              f"    scoresheet: {j.name} / {m.name}", file=sys.stderr)
    print("\nNext: the adjudicator fills every blank verdict cell against "
          "the hidden key. No pass/fail is computed by this runner.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
