import json, re, os, collections

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "specs",
                            "guidance-reflection-rubric.md")

LENSES = ["compliance", "violation", "applicability"]


def extract_session(path):
    """Mirrors measure_skill_invocation.py's mounted-skill extraction: scan
    the session-log JSONL for the init/plugins line to get mounted skills,
    and concatenate assistant text/tool_use content as the deliverable text
    judges score against."""
    mounted = None
    text_parts = []
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            if '"subtype":"init"' in line and '"plugins":[' in line:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                plugins = obj.get("plugins", [])
                mounted = [p["name"] for p in plugins
                           if "/skill-registry/skills/" in p.get("path", "")]
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = obj.get("content")
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
    return mounted or [], "\n".join(text_parts)


def default_judge_fn(skill, lens, deliverable_text):
    """Default judge seam: shells to `spawn.py consult` for one lens. Not
    exercised by tests (judges are mocked there); kept as the live-run
    default per the executed-live acceptance path."""
    import subprocess
    prompt = (
        f"Rubric: {RUBRIC_PATH}\nSkill: {skill}\nLens: {lens}\n"
        f"Deliverable:\n{deliverable_text}\n"
        "Answer with exactly one of: yes, no, partial — then one line of evidence."
    )
    spawn_py = os.path.join(os.path.dirname(__file__), "..", "spawn.py")
    out = subprocess.run(
        ["python3", spawn_py, "consult", "implementation", prompt],
        capture_output=True, text=True, timeout=180,
    ).stdout.strip()
    first_line = out.splitlines()[0].strip().lower() if out else "partial"
    verdict = first_line if first_line in ("yes", "no", "partial") else "partial"
    evidence = out.splitlines()[1] if len(out.splitlines()) > 1 else "no evidence returned"
    return {"verdict": verdict, "evidence": evidence}


def majority(votes):
    """votes: list of {'verdict': ..., 'evidence': ...} dicts (one per lens).
    Returns (reflected, evidence)."""
    counts = collections.Counter(v["verdict"] for v in votes)
    top = counts.most_common()
    if len(top) == 1 or top[0][1] > top[1][1]:
        winner = top[0][0]
        evidence = next(v["evidence"] for v in votes if v["verdict"] == winner)
        return winner, evidence
    # no strict majority (even split, or 3-way tie) -> partial
    evidence = "; ".join(f"{v['verdict']}: {v['evidence']}" for v in votes)
    return "partial", evidence


def score_skill(skill, deliverable_text, judge_fn, panel_size=3):
    lenses = LENSES[:panel_size]
    votes = [judge_fn(skill, lens, deliverable_text) for lens in lenses]
    reflected, evidence = majority(votes)
    return {"skill": skill, "reflected": reflected, "evidence": evidence, "votes": votes}


def reflect_session(path, judge_fn=default_judge_fn, panel_size=3):
    mounted, deliverable_text = extract_session(path)
    if not mounted:
        return {"path": path, "status": "not-applicable", "reason": "no-mounted-skills"}
    rows = [score_skill(skill, deliverable_text, judge_fn, panel_size) for skill in mounted]
    return {"path": path, "status": "measured", "rows": rows}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: measure_skill_reflection.py <session-log-or-record-path> [...]",
              file=sys.stderr)
        sys.exit(1)
    for p in sys.argv[1:]:
        print(json.dumps(reflect_session(p)))
