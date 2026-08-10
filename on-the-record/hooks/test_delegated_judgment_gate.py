#!/usr/bin/env python3
"""issue #573 (implementation phase 2) — delegated-judgment-gate.sh, live-fired.

A synthetic TARGET repo (bare tmp dir, no on-the-record checkout of its
own — zero-install constraint) with two seeded roles (architecture,
security-threat-model), each with judgment_axes and a write_scope. The
real hook script is invoked exactly as the PreToolUse/Bash matcher would
invoke it, against a `gh pr create` Bash command on an `issue-<n>/<role>`
branch. `gh` itself is stubbed to a script that logs every invocation to
a file instead of touching the network, so tests can assert which of the
five issue-timeline events fired without needing real GitHub access.

  python3 on-the-record/hooks/test_delegated_judgment_gate.py
"""
from __future__ import annotations
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "delegated-judgment-gate.sh"

CMD = 'gh pr create --title x --body y --number 42'

ARCHITECTURE_ROLE = {
    "write_scope": ["docs/decisions/*.md", "docs/issue-<n>/reports/architecture.md"],
    "judgment_axes": ["maintenance_complexity"],
}
SECURITY_ROLE = {
    "write_scope": ["docs/issue-<n>/reports/security-threat-model.md"],
    "judgment_axes": ["attack_potential"],
}


def _stub_gh(bin_dir: Path, log: Path) -> None:
    script = bin_dir / "gh"
    script.write_text(
        "#!/usr/bin/env bash\n"
        f'printf \'%s\\n\' "$*" >> "{log}"\n'
        "exit 0\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def _init_target(target: Path, roles: dict[str, dict]) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    (target / "roles").mkdir(parents=True, exist_ok=True)
    for name, cfg in roles.items():
        (target / "roles" / f"{name}.json").write_text(json.dumps(cfg))
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=target, check=True)
    (target / "README.md").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=target, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
                     "commit", "-q", "-m", "init"], cwd=target, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(target)], cwd=target, check=True)
    subprocess.run(["git", "update-ref", "refs/remotes/origin/main", "main"], cwd=target, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "issue-42/gate"], cwd=target, check=True)
    return target


def _commit_change(target: Path, rel_path: str, content: str) -> None:
    p = target / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=target, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
                     "commit", "-q", "-m", "change"], cwd=target, check=True)


def _axis_block(axis: str, verdict: str, finding: dict | None = None) -> str:
    lines = [f"axis: {axis}", f"verdict: {verdict}", "citation: docs/product/priorities.md#p1"]
    if finding:
        lines.append(f"finding.target_path: {finding['target_path']}")
        lines.append(f"finding.required_fix: {finding['required_fix']}")
    body = "\n".join(lines)
    return f"<!-- axis_evaluation\n{body}\n-->\n"


def _run(target: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": CMD}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                           capture_output=True, text=True, env=env)


def _product_corpus(target: Path, mentions: list[str]) -> None:
    d = target / "docs" / "product"
    d.mkdir(parents=True, exist_ok=True)
    (d / "priorities.md").write_text(
        "# priorities\n" + "\n".join(f"- see {m}" for m in mentions))


def t_no_trigger_no_side_effects(tmp_path: Path):
    target = _init_target(tmp_path / "t1", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "bin1", tmp_path / "gh1.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "gh pr comment 1 --body x"}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert not log.exists()
    assert not (target / "docs" / "issue-42" / "decisions").exists()


def t_escalate_on_empty_corpus(tmp_path: Path):
    target = _init_target(tmp_path / "t2", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    bin_dir, log = tmp_path / "bin2", tmp_path / "gh2.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    assert not (target / "docs" / "issue-42" / "decisions").exists()
    assert "Verdict" in log.read_text() and "escalate" in log.read_text()


def t_escalate_on_no_quorum(tmp_path: Path):
    target = _init_target(tmp_path / "t3", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    bin_dir, log = tmp_path / "bin3", tmp_path / "gh3.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    assert not (target / "docs" / "issue-42" / "decisions").exists()
    assert "escalate" in log.read_text()


def t_auto_approve_single_role(tmp_path: Path):
    target = _init_target(tmp_path / "t4", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(_axis_block("maintenance_complexity", "supports"))
    bin_dir, log = tmp_path / "bin4", tmp_path / "gh4.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    auto = list((target / "docs" / "issue-42" / "decisions").glob("auto-*.md"))
    assert len(auto) == 1
    text = auto[0].read_text()
    assert "decision: approve" in text
    assert "Judgment opened" in log.read_text()
    assert "approve" in log.read_text()


def t_auto_reject_with_finding_and_remediation(tmp_path: Path):
    target = _init_target(tmp_path / "t5", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(_axis_block(
        "maintenance_complexity", "contradicts",
        {"target_path": "docs/decisions/foo.md", "required_fix": "simplify it"}))
    bin_dir, log = tmp_path / "bin5", tmp_path / "gh5.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    decisions = target / "docs" / "issue-42" / "decisions"
    auto = list(decisions.glob("auto-*.md"))
    assert "decision: reject" in auto[0].read_text()
    rem = list(decisions.glob("remediation-*.md"))
    assert len(rem) == 1
    rem_text = rem[0].read_text()
    assert "routed_to: architecture" in rem_text
    assert "round: 1" in rem_text
    assert "status: open" in rem_text
    assert "Remediation routed" in log.read_text()


def t_all_five_issue_timeline_events_fire_across_reject_flow(tmp_path: Path):
    target = _init_target(tmp_path / "t6", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    bin_dir, log = tmp_path / "bin6", tmp_path / "gh6.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    decisions = target / "docs" / "issue-42" / "decisions"
    for i in range(4):
        # each round's required_fix differs — a genuinely new (still
        # failing) remediation attempt, so only the round bound (not the
        # repeat-contradiction check) is what exhausts it here.
        record.write_text(_axis_block(
            "maintenance_complexity", "contradicts",
            {"target_path": "docs/decisions/foo.md", "required_fix": f"attempt {i}"}))
        _run(target, bin_dir)
    text = log.read_text()
    assert "Judgment opened" in text
    assert "Verdict" in text
    assert "Remediation routed" in text
    assert "Escalated" in text
    rem = sorted(decisions.glob("remediation-*.md"))
    assert len(rem) == 4
    assert "status: escalated" in rem[-1].read_text()
    assert "round: 4" in rem[-1].read_text()


def t_loop_bound_exhausted_escalates_at_round_4(tmp_path: Path):
    target = _init_target(tmp_path / "t7", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    bin_dir, log = tmp_path / "bin7", tmp_path / "gh7.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    decisions = target / "docs" / "issue-42" / "decisions"
    for i in range(3):
        record.write_text(_axis_block(
            "maintenance_complexity", "contradicts",
            {"target_path": "docs/decisions/foo.md", "required_fix": f"attempt {i}"}))
        _run(target, bin_dir)
    rem_before = sorted(decisions.glob("remediation-*.md"))
    assert all("status: open" in p.read_text() for p in rem_before)
    record.write_text(_axis_block(
        "maintenance_complexity", "contradicts",
        {"target_path": "docs/decisions/foo.md", "required_fix": "attempt 3"}))
    _run(target, bin_dir)
    rem_after = sorted(decisions.glob("remediation-*.md"))
    assert "status: escalated" in rem_after[-1].read_text()
    assert "round: 4" in rem_after[-1].read_text()


def t_repeat_contradiction_from_same_role_escalates_before_round_3(tmp_path: Path):
    target = _init_target(tmp_path / "t8", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(_axis_block(
        "maintenance_complexity", "contradicts",
        {"target_path": "docs/decisions/foo.md", "required_fix": "simplify it"}))
    bin_dir, log = tmp_path / "bin8", tmp_path / "gh8.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    decisions = target / "docs" / "issue-42" / "decisions"
    _run(target, bin_dir)  # round 1: open
    _run(target, bin_dir)  # round 2: same role, same path -> repeat -> escalate before round 3
    rem = sorted(decisions.glob("remediation-*.md"))
    assert len(rem) == 2
    assert "status: open" in rem[0].read_text()
    assert "status: escalated" in rem[1].read_text()
    assert "round: 2" in rem[1].read_text()


def t_multi_role_panel_quorum_and_unanimous_support_approves(tmp_path: Path):
    target = _init_target(
        tmp_path / "t9",
        {"architecture": ARCHITECTURE_ROLE, "security-threat-model": SECURITY_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    (target / "docs" / "issue-42" / "reports").mkdir(parents=True, exist_ok=True)
    _commit_change(target, "docs/issue-42/reports/security-threat-model.md", "seed")
    _product_corpus(target, ["foo.md", "security-threat-model.md"])
    arch_record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    arch_record.write_text(_axis_block("maintenance_complexity", "supports"))
    sec_record = target / "docs" / "issue-42" / "reports" / "security-threat-model.md"
    sec_record.write_text(_axis_block("attack_potential", "supports"))
    bin_dir, log = tmp_path / "bin9", tmp_path / "gh9.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    auto = list((target / "docs" / "issue-42" / "decisions").glob("auto-*.md"))
    assert len(auto) == 1
    text = auto[0].read_text()
    assert "decision: approve" in text
    assert "role: architecture" in text
    assert "role: security-threat-model" in text


def t_partial_support_with_no_opinion_escalates_not_approves(tmp_path: Path):
    target = _init_target(
        tmp_path / "t10",
        {"architecture": ARCHITECTURE_ROLE, "security-threat-model": SECURITY_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    (target / "docs" / "issue-42" / "reports").mkdir(parents=True, exist_ok=True)
    _commit_change(target, "docs/issue-42/reports/security-threat-model.md", "seed")
    _product_corpus(target, ["foo.md", "security-threat-model.md"])
    arch_record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    arch_record.write_text(_axis_block("maintenance_complexity", "supports"))
    sec_record = target / "docs" / "issue-42" / "reports" / "security-threat-model.md"
    sec_record.write_text(_axis_block("attack_potential", "no-opinion"))
    bin_dir, log = tmp_path / "bin10", tmp_path / "gh10.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    r = _run(target, bin_dir)
    assert r.returncode == 0
    assert not (target / "docs" / "issue-42" / "decisions").exists()
    assert "escalate" in log.read_text()


def t_kill_switch_disables_the_gate(tmp_path: Path):
    target = _init_target(tmp_path / "t11", {"architecture": ARCHITECTURE_ROLE})
    _commit_change(target, "docs/decisions/foo.md", "x")
    _product_corpus(target, ["foo.md"])
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(_axis_block("maintenance_complexity", "supports"))
    bin_dir, log = tmp_path / "bin11", tmp_path / "gh11.log"
    bin_dir.mkdir()
    _stub_gh(bin_dir, log)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": CMD}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env["ORCHESTRATE_OFF"] = "1"
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert not log.exists()
    assert not (target / "docs" / "issue-42" / "decisions").exists()


def _stub_gh_with_stdin(bin_dir: Path, log: Path) -> None:
    script = bin_dir / "gh"
    script.write_text(
        "#!/usr/bin/env bash\n"
        f'printf \'%s\\n\' "$*" >> "{log}"\n'
        f'cat >> "{log}"\n'
        f'printf \'\\n---\\n\' >> "{log}"\n'
        "exit 0\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def _run_cmd(target: Path, bin_dir: Path, cmd: str) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                           capture_output=True, text=True, env=env)


def t_framing_snapshot_baseline_on_delivery_merged_no_prior_records(tmp_path: Path):
    target = _init_target(tmp_path / "f1", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "binf1", tmp_path / "ghf1.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    r = _run_cmd(target, bin_dir, "gh pr merge 42 --squash")
    assert r.returncode == 0
    text = log.read_text()
    assert "issue comment 42" in text
    assert "## Framing snapshot — delivery-merged (42 / PR #42)" in text
    assert "**Resolved problem:**" in text
    assert "**Prior cost:**" in text
    assert "**Newly possible:**" in text
    assert "**Still broken:**" in text
    assert "no prior record; issue body is the baseline" in text


def t_framing_snapshot_on_issue_reopened_cites_role_record(tmp_path: Path):
    target = _init_target(tmp_path / "f2", {"architecture": ARCHITECTURE_ROLE})
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "## What was done\nWired the reversibility axis.\n\n"
        "## What did not work\nFirst attempt used the wrong glob.\n")
    bin_dir, log = tmp_path / "binf2", tmp_path / "ghf2.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    r = _run_cmd(target, bin_dir, "gh issue reopen 42")
    assert r.returncode == 0
    text = log.read_text()
    assert "## Framing snapshot — issue-reopened (42)" in text
    assert "Wired the reversibility axis." in text
    assert "First attempt used the wrong glob." in text
    assert "docs/issue-42/reports/architecture.md" in text


def t_framing_snapshot_on_issue_closed_cites_decision_record(tmp_path: Path):
    target = _init_target(tmp_path / "f3", {"architecture": ARCHITECTURE_ROLE})
    decisions = target / "docs" / "issue-42" / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    (decisions / "auto-1.md").write_text("---\ndecision: approve\ntimestamp: x\n---\n")
    bin_dir, log = tmp_path / "binf3", tmp_path / "ghf3.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    r = _run_cmd(target, bin_dir, "gh issue close 42")
    assert r.returncode == 0
    text = log.read_text()
    assert "## Framing snapshot — issue-closed (42)" in text
    assert "Decision recorded: approve" in text
    assert "docs/issue-42/decisions/auto-1.md" in text


def t_framing_snapshot_fails_closed_on_unresolvable_citation(tmp_path: Path):
    target = _init_target(tmp_path / "f4", {"architecture": ARCHITECTURE_ROLE})
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "## What was done\nWired the reversibility axis.\n"
        "Citation: docs/does/not/exist.md\n")
    bin_dir, log = tmp_path / "binf4", tmp_path / "ghf4.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    r = _run_cmd(target, bin_dir, "gh issue reopen 42")
    assert r.returncode == 0
    assert not log.exists()


def t_framing_snapshot_field_not_found_cites_baseline_not_record(tmp_path: Path):
    # issue #597 conformance-review R6: a record exists (so the
    # no-records-at-all baseline branch does not fire), but it carries none
    # of the fields build_framing_snapshot looks for. The per-field fallback
    # sentence must cite the baseline form, never the record's own path —
    # citing the record would claim it contains text it does not.
    target = _init_target(tmp_path / "f5", {"architecture": ARCHITECTURE_ROLE})
    record = target / "docs" / "issue-42" / "reports" / "architecture.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text("## Unrelated heading\nNothing the gate looks for.\n")
    bin_dir, log = tmp_path / "binf5", tmp_path / "ghf5.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    r = _run_cmd(target, bin_dir, "gh issue reopen 42")
    assert r.returncode == 0
    text = log.read_text()
    assert "## Framing snapshot — issue-reopened (42)" in text
    assert "No newly-possible prose found" in text
    assert "No prior-cost prose found" in text
    assert "no prior record; issue body is the baseline" in text
    assert "docs/issue-42/reports/architecture.md" not in text


def t_review_verdict_without_citation_gets_flagged(tmp_path: Path):
    target = _init_target(tmp_path / "g1", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "bing1", tmp_path / "ghg1.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {
        "command": "gh pr comment 42 --body 'Verdict: Absent — this claim is not implemented.'"}})
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    text = log.read_text()
    assert "pr comment 42" in text
    assert "Review-is-role-work audit (issue #641)" in text


def t_review_verdict_with_role_record_citation_not_flagged(tmp_path: Path):
    target = _init_target(tmp_path / "g2", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "bing2", tmp_path / "ghg2.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {
        "command": "gh pr comment 42 --body 'Verdict: Absent per "
                   "docs/issue-42/reports/conformance-review.md.'"}})
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert not log.exists()


def t_review_verdict_in_role_session_not_flagged(tmp_path: Path):
    target = _init_target(tmp_path / "g3", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "bing3", tmp_path / "ghg3.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    env = dict(os.environ)
    env["CLAUDE_ROLE"] = "conformance-review"
    payload = json.dumps({"tool_name": "Bash", "tool_input": {
        "command": "gh pr comment 42 --body 'Verdict: Absent — this claim is not implemented.'"}})
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert not log.exists()


def t_non_verdict_comment_not_flagged(tmp_path: Path):
    target = _init_target(tmp_path / "g4", {"architecture": ARCHITECTURE_ROLE})
    bin_dir, log = tmp_path / "bing4", tmp_path / "ghg4.log"
    bin_dir.mkdir()
    _stub_gh_with_stdin(bin_dir, log)
    env = dict(os.environ)
    env.pop("CLAUDE_ROLE", None)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {
        "command": "gh pr comment 42 --body 'PR opened, ready for review.'"}})
    env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    env.pop("ORCHESTRATE_OFF", None)
    r = subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                        capture_output=True, text=True, env=env)
    assert r.returncode == 0
    assert not log.exists()


def t_no_import_gates_and_no_checkout_resolve_in_the_hook_source():
    text = SCRIPT.read_text()
    assert "import gates" not in text
    assert "_checkout_resolve" not in text
    assert "TOKENMAXXXER_CHECKOUT" not in text


if __name__ == "__main__":
    import inspect
    import tempfile
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and inspect.isfunction(v)]
    for t in tests:
        params = inspect.signature(t).parameters
        if params:
            with tempfile.TemporaryDirectory() as td:
                t(Path(td))
        else:
            t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
