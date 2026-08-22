import argparse, json, re, os, collections

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


def parse_consult_output(out):
    """`spawn.py consult` prints `json.dumps(verdict, indent=2)` — a
    pretty-printed `{"answer", "confidence", "caveats"}` object, not the
    plain "verdict-line / evidence-line" text default_judge_fn's own
    prompt asks for (consult_cmd's own JSON-format instruction overrides
    it). Parse that JSON directly instead of splitting lines, or a
    fragment like '"answer": "no",' leaks into evidence as raw JSON
    (issue #1999)."""
    try:
        obj = json.loads(out)
    except (json.JSONDecodeError, TypeError):
        obj = None
    if not isinstance(obj, dict):
        return {"verdict": "partial", "evidence": "judge-gave-no-rationale"}
    answer = str(obj.get("answer", "")).strip().lower()
    verdict = answer if answer in ("yes", "no", "partial") else "partial"
    caveats = [str(c).strip() for c in (obj.get("caveats") or []) if str(c).strip()]
    evidence = "; ".join(caveats) if caveats else "judge-gave-no-rationale"
    return {"verdict": verdict, "evidence": evidence}


def default_judge_fn(skill, lens, deliverable_text):
    """Default judge seam: shells to `spawn.py consult` for one lens. Not
    exercised by tests (judges are mocked there); kept as the live-run
    default per the executed-live acceptance path."""
    import subprocess
    prompt = (
        f"Rubric: {RUBRIC_PATH}\nSkill: {skill}\nLens: {lens}\n"
        f"Deliverable:\n{deliverable_text}\n"
        "Judge whether the deliverable reflects this skill's rules, quoting "
        "the deliverable or your own rationale as evidence."
    )
    spawn_py = os.path.join(os.path.dirname(__file__), "..", "spawn.py")
    out = subprocess.run(
        ["python3", spawn_py, "consult", "implementation", prompt],
        capture_output=True, text=True, timeout=180,
    ).stdout.strip()
    return parse_consult_output(out)


PAIRING_LINE_RE = re.compile(r"^(?P<artifact>\S+) ↔ (?P<skill>\S+) — .+$", re.MULTILINE)

ARTIFACT_LENSES = ["compliance", "violation", "applicability"]


def parse_pairing_lines(text):
    """Parse the `<artifact_path> ↔ <skill_name> — <trigger_line>` lines
    spawn.py (#2014) appends to the task text when `design-artifacts:` pairs
    resolved. Byte-inert (empty list) when no such lines are present."""
    return [{"artifact": m.group("artifact"), "skill": m.group("skill")}
            for m in PAIRING_LINE_RE.finditer(text)]


def read_artifact(workspace_root, artifact_path):
    """Read a declared artifact's file content relative to workspace_root.
    Returns None when the file is missing (feeds the `absent` verdict
    directly, no judge call needed)."""
    full_path = os.path.join(workspace_root, artifact_path)
    if not os.path.isfile(full_path):
        return None
    with open(full_path, "r", errors="replace") as fh:
        return fh.read()


def default_artifact_judge_fn(skill, lens, artifact_text):
    """Judge seam for artifact-conformance: same one-skill/one-lens/one-text
    shape as default_judge_fn, but asks whether the artifact *follows* the
    named skill's methodology rather than whether a deliverable reflects it.
    Not exercised by tests (judges are mocked there)."""
    import subprocess
    prompt = (
        f"Rubric: {RUBRIC_PATH}\nSkill: {skill}\nLens: {lens}\n"
        f"Artifact:\n{artifact_text}\n"
        "Judge whether this artifact actually follows this skill's "
        "methodology/procedure, quoting the artifact or your own rationale "
        "as evidence."
    )
    spawn_py = os.path.join(os.path.dirname(__file__), "..", "spawn.py")
    out = subprocess.run(
        ["python3", spawn_py, "consult", "implementation", prompt],
        capture_output=True, text=True, timeout=180,
    ).stdout.strip()
    return parse_consult_output(out)


def _artifact_majority(votes):
    """Like majority(), but for the full/partial/absent vocabulary: no
    strict majority collapses to 'partial' rather than re-using majority()'s
    yes/no-shaped tie evidence formatting verbatim would still be correct,
    but this keeps the two vocabularies visibly separate per the proposal's
    Rationale."""
    counts = collections.Counter(v["verdict"] for v in votes)
    top = counts.most_common()
    if len(top) == 1 or top[0][1] > top[1][1]:
        winner = top[0][0]
        evidence = next(v["evidence"] for v in votes if v["verdict"] == winner)
        return winner, evidence
    evidence = "; ".join(f"{v['verdict']}: {v['evidence']}" for v in votes)
    return "partial", evidence


def score_artifact(artifact_path, skill, artifact_text, judge_fn, panel_size=3):
    if artifact_text is None:
        return {"artifact": artifact_path, "skill": skill, "verdict": "absent",
                "evidence": "artifact file missing from workspace", "votes": []}
    lenses = ARTIFACT_LENSES[:panel_size]
    votes = [judge_fn(skill, lens, artifact_text) for lens in lenses]
    verdict, evidence = _artifact_majority(votes)
    return {"artifact": artifact_path, "skill": skill, "verdict": verdict,
            "evidence": evidence, "votes": votes}


def reflect_artifacts(session_path, workspace_root, judge_fn=default_artifact_judge_fn,
                       panel_size=3):
    _, text = extract_session(session_path)
    pairings = parse_pairing_lines(text)
    if not pairings:
        return {"path": session_path, "status": "not-applicable",
                "reason": "no-pairing-lines"}
    rows = []
    for pairing in pairings:
        artifact_text = read_artifact(workspace_root, pairing["artifact"])
        rows.append(score_artifact(pairing["artifact"], pairing["skill"],
                                    artifact_text, judge_fn, panel_size))
    return {"path": session_path, "status": "measured", "rows": rows}


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
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--workspace", default=None,
                         help="workspace root to score design artifacts against")
    args = parser.parse_args()
    for p in args.paths:
        print(json.dumps(reflect_session(p)))
        if args.workspace is not None:
            print(json.dumps(reflect_artifacts(p, args.workspace)))
