"""Acceptance gate for issue #1131: consumer -> upstream defect channel.

The channel itself is a Claude Code command element
(on-the-record/commands/report-upstream.md), interpreted by an LLM
session rather than a deterministic program (req#7 — hooks/command
elements only, no CI/service to execute end-to-end). This gate therefore
checks the two structural guarantees the issue's Acceptance section
names:

  1. the command's own instructions produce a draft with version sha +
     repro + observation-context sections, run the dedup check before
     the user-confirmation step, and gate any filing call behind that
     confirmation step, with the unreachable-upstream fallback landing
     in docs/reports/upstream-findings/ (empty-state per issue #1131 Acceptance
     bullet 1);
  2. the PR-creation prohibition is enforced structurally, not just
     stated in prose — by driving the real
     upstream-defect-scope-guard.sh hook (call-shape/argument assertion,
     issue #1131 Acceptance bullet 2), not by re-reading the command
     doc's own claims about itself.
"""
import json
import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMAND_DOC = REPO_ROOT / "on-the-record" / "commands" / "report-upstream.md"
SCOPE_GUARD = REPO_ROOT / "on-the-record" / "hooks" / "upstream-defect-scope-guard.sh"
FINDINGS_DIR = REPO_ROOT / "docs" / "reports" / "upstream-findings"


def _run_guard(command):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(REPO_ROOT),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(SCOPE_GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_command_doc_exists():
    assert COMMAND_DOC.is_file()


def t_draft_carries_version_sha_repro_and_context_sections():
    text = COMMAND_DOC.read_text(encoding="utf-8")
    assert "Plugin version" in text
    assert "rev-parse HEAD" in text
    assert "Reproduction" in text
    assert "Observation context" in text


def t_dedup_check_runs_before_confirmation_step():
    text = COMMAND_DOC.read_text(encoding="utf-8")
    dedup_idx = text.find("중복 체크")
    confirm_idx = text.find("미리보기 + 확인")
    assert dedup_idx != -1 and confirm_idx != -1
    assert dedup_idx < confirm_idx


def t_no_filing_before_confirmation():
    text = COMMAND_DOC.read_text(encoding="utf-8")
    confirm_idx = text.find("미리보기 + 확인")
    filing_idx = text.find("gh issue create", confirm_idx)
    assert confirm_idx != -1
    assert filing_idx != -1
    assert filing_idx > confirm_idx
    # no `gh issue create` call-shape appears anywhere before the
    # confirmation step is reached in the instructions
    before_confirm = text[:confirm_idx]
    assert "gh issue create" not in before_confirm


def t_unreachable_upstream_falls_back_to_local_draft():
    text = COMMAND_DOC.read_text(encoding="utf-8")
    assert "docs/reports/upstream-findings/" in text
    assert FINDINGS_DIR.is_dir()
    fixture = FINDINGS_DIR / "2026-08-13-watcher-registry-stale-pid.md"
    assert fixture.is_file()


def t_pr_creation_denied():
    pr_shapes = [
        "gh pr create --repo tokenmaxxxer/on-the-record --title x --body y",
        "GH_REPO=tokenmaxxxer/on-the-record gh pr create --title x --body y",
        "gh api --method POST repos/tokenmaxxxer/on-the-record/pulls -f title=x",
        "gh api graphql -f query='mutation { createPullRequest(input: {}) { pullRequest { id } } }'",
        "hub pull-request -m 'x'",
        "curl -X POST https://api.github.com/repos/tokenmaxxxer/on-the-record/pulls -d '{}'",
        "curl -X POST https://api.github.com/graphql -d '{\"query\":\"mutation { createPullRequest(input: {}) { pullRequest { id } } }\"}'",
    ]
    for shape in pr_shapes:
        r = _run_guard(shape)
        assert r.returncode == 2, "expected denial for: %s" % shape


def t_issue_creation_still_allowed():
    r = _run_guard("gh issue create --repo tokenmaxxxer/on-the-record --title x --body y")
    assert r.returncode == 0


def t_no_pr_creation_call_shape_in_channel_code():
    # the command doc must never instruct an actual PR-creation call —
    # every mention of `gh pr create` in the doc appears only inside the
    # prohibition language, never as a step to execute.
    text = COMMAND_DOC.read_text(encoding="utf-8")
    steps_section = text.split("## 무엇을 하지 않나")[0]
    for m in re.finditer(r"gh\s+pr\s+create", steps_section):
        window = steps_section[max(0, m.start() - 80):m.end() + 200]
        assert "절대" in window or "PR 경로는 존재하지 않는다" in window
