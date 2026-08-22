import json, re, glob, os, sys, statistics

sys.path.insert(0, os.path.dirname(__file__))
import measure_skill_invocation as msi

WORK_DIR = os.path.expanduser("~/.tokenmaxxxer/work/")

MIN_GROUP_N = 3

BIAS_CAVEAT = (
    "CAVEAT (correlation-only): role and task-difficulty are uncontrolled "
    "confounds -- sessions were not randomly assigned to skill-invoked vs "
    "not-invoked (or reflected vs not-reflected). Any gap between groups may "
    "reflect who/what tends to invoke or reflect skills, not an effect of "
    "the skill itself. No causal claims."
)

REVIEW_ROUND_RE = re.compile(r"git push")
GATE_REFUSAL_RE = re.compile(r"hook error")
ACCEPTANCE_FAILURE_RE = re.compile(
    r"result: fail|FAILED|AssertionError|acceptance.*fail", re.IGNORECASE
)


def today_logs():
    files = glob.glob(os.path.join(WORK_DIR, "*.session*.log"))
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d")
    return sorted(f for f in files if f".session.{today}" in f or f".session{today}" in f)


def session_metrics(path):
    """Cheap regex-based outcome proxies read directly from the raw session
    log text: review_rounds ~= number of git-push cycles submitted for
    review, gate_refusals = PreToolUse hook-error blocks, acceptance_failed
    = whether any acceptance/test-failure marker appears."""
    try:
        with open(path, "r", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None
    return {
        "path": path,
        "review_rounds": len(REVIEW_ROUND_RE.findall(text)),
        "gate_refusals": len(GATE_REFUSAL_RE.findall(text)),
        "acceptance_failed": 1 if ACCEPTANCE_FAILURE_RE.search(text) else 0,
    }


def invocation_label(path):
    base = re.sub(r"\.session(\.\d{8}T\d{6}\.\d+)?\.log$", "", os.path.basename(path))
    result = msi.analyze(base, path)
    if result["status"] != "measured":
        return None
    return "invoked" if result["skill_calls"] > 0 else "not-invoked"


def load_reflection_labels(artifact_path):
    """artifact_path: a JSONL file of measure_skill_reflection.reflect_session()
    output (scope A's artifact). Returns {session_path: 'reflected'|'not-reflected'}."""
    labels = {}
    if not artifact_path or not os.path.exists(artifact_path):
        return labels
    with open(artifact_path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("status") != "measured":
                continue
            reflected_any = any(row.get("reflected") == "yes" for row in obj.get("rows", []))
            labels[obj["path"]] = "reflected" if reflected_any else "not-reflected"
    return labels


def group_sessions(paths, reflection_artifact=None):
    """Returns (group_a_name, group_a_metrics, group_b_name, group_b_metrics,
    grouping_basis). Prefers reflection labels (scope A's artifact) when
    available for a session; falls back to invocation labels otherwise."""
    reflection_labels = load_reflection_labels(reflection_artifact)
    used_reflection = bool(reflection_labels)
    groups = {}
    for path in paths:
        m = session_metrics(path)
        if m is None:
            continue
        if path in reflection_labels:
            label = reflection_labels[path]
        else:
            label = invocation_label(path)
        if label is None:
            continue
        groups.setdefault(label, []).append(m)
    basis = "reflection" if used_reflection else "invocation"
    if used_reflection:
        a, b = "reflected", "not-reflected"
    else:
        a, b = "invoked", "not-invoked"
    return a, groups.get(a, []), b, groups.get(b, []), basis


def group_summary(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0}
    return {
        "n": n,
        "review_rounds_mean": statistics.mean(r["review_rounds"] for r in rows),
        "gate_refusals_mean": statistics.mean(r["gate_refusals"] for r in rows),
        "acceptance_failure_rate": statistics.mean(r["acceptance_failed"] for r in rows),
    }


def render_report(a_name, a_rows, b_name, b_rows, basis):
    lines = []
    lines.append(f"# Skill outcome-contrast ({basis}-based grouping)")
    lines.append("")
    if len(a_rows) < MIN_GROUP_N or len(b_rows) < MIN_GROUP_N:
        lines.append(
            f"underpowered: {a_name}=n{len(a_rows)}, {b_name}=n{len(b_rows)} "
            f"(minimum {MIN_GROUP_N} per group) -- no comparison numbers emitted."
        )
        lines.append("")
        lines.append(BIAS_CAVEAT)
        return "\n".join(lines)
    a_sum = group_summary(a_rows)
    b_sum = group_summary(b_rows)
    lines.append(f"| group | n | review_rounds mean | gate_refusals mean | acceptance_failure_rate |")
    lines.append(f"|---|---|---|---|---|")
    for name, s in ((a_name, a_sum), (b_name, b_sum)):
        lines.append(
            f"| {name} | {s['n']} | {s['review_rounds_mean']:.2f} | "
            f"{s['gate_refusals_mean']:.2f} | {s['acceptance_failure_rate']:.2f} |"
        )
    lines.append("")
    lines.append(BIAS_CAVEAT)
    return "\n".join(lines)


if __name__ == "__main__":
    reflection_artifact = None
    paths = None
    for arg in sys.argv[1:]:
        if arg.startswith("--reflection-artifact="):
            reflection_artifact = arg.split("=", 1)[1]
        else:
            paths = (paths or []) + [arg]
    if paths is None:
        paths = today_logs()
    a_name, a_rows, b_name, b_rows, basis = group_sessions(paths, reflection_artifact)
    print(render_report(a_name, a_rows, b_name, b_rows, basis))
