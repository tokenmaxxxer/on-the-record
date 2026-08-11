#!/usr/bin/env python3
"""Tests for pr-preflight.sh's ported check_body logic (issue #459) and
phase-1 closing-keyword refusal (issue #741 round 2).

pr-preflight.sh embeds its checker as inline Python inside a bash heredoc
(same shape as contract-guard.sh), so it isn't importable. Following
contract-guard.sh's own precedent (test_contract_guard.py exercises the
shell script end-to-end rather than importing internals), most of this
file duplicates the exact same pure `check_body`/`_plan_from_body`/
`_phase1_closes_ref` logic as plain Python and asserts against it directly
(no subprocess, no `gh`) — the fastest, most direct way to pin the core
decision logic since it takes no I/O. The `test_hook_*` functions at the
end are the one exception: they drive the real `pr-preflight.sh` script
end-to-end (subprocess, stub `gh`) for the issue #741 acceptance bar that
specifically needs the live hook, not just the duplicated logic.

Run: python3 on-the-record/hooks/test_pr_preflight.py
Exit 0 all pass / 1 on any failure. Prints PASS/FAIL per case.

Run: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -v
Collects and runs the `test_hook_*` end-to-end cases (pytest does not
collect the plain `run()` function above — it is not test_*-prefixed by
design, so it stays runnable standalone without a pytest dependency).
"""
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
PREFLIGHT = HOOKS_DIR / "pr-preflight.sh"

# --- ported from gates/flows.py::_plan_from_body ---------------------------
_PLAN_STEP_RE = re.compile(r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$")


def _plan_from_body(issue_body):
    lines = (issue_body or "").splitlines()
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped == "## 실행 계획" or stripped.startswith("## 실행 계획 "):
            start = i + 1
            break
    if start is None:
        return None
    steps = []
    in_fence = False
    for line in lines[start:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        if stripped.startswith("##"):
            break
        mm = _PLAN_STEP_RE.match(stripped)
        if not mm:
            continue
        done = mm.group(1) in ("x", "X")
        step_n = int(mm.group(2))
        roles = [r.strip() for r in mm.group(3).split("‖")]
        steps.append({"step": step_n, "roles": roles, "done": done})
    return steps


# --- ported from gates/pr_reference.py::check_body --------------------------
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")


def _phase1_closes_ref(issue, body):
    """Ported from pr-preflight.sh's phase-1 author-written closing-keyword
    refusal (issue #741 round 2) — the same finditer-over-search semantics
    as gates/ci.py::_closes_ref_for_issue: returns the first _CLOSES_REF
    match whose own issue number equals `issue`, scanning every match
    (not just the first) so a decoy reference to a different issue earlier
    in the body cannot hide a real match further along."""
    for m in _CLOSES_REF.finditer(body or ""):
        if int(m.group(2)) == issue:
            return m
    return None


def check_body(issue, body, phase, plan=None):
    body = body or ""
    if phase == "phase2":
        if plan:
            incomplete = [s for s in plan if not s["done"]]
            max_step = max(s["step"] for s in plan) if plan else 0
            only_last_incomplete = (
                len(incomplete) == 1 and incomplete[0]["step"] == max_step
            )
            if incomplete and not only_last_incomplete:
                mm = _CLOSES_REF.search(body)
                if mm and int(mm.group(2)) == issue:
                    return ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return []
        mm = _CLOSES_REF.search(body)
        if not mm or int(mm.group(2)) != issue:
            return [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return []
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return []


def run():
    failures = []

    def case(name, cond):
        if cond:
            print(f"PASS: {name}")
        else:
            print(f"FAIL: {name}")
            failures.append(name)

    # red: phase2, Closes #447, plan has an incomplete non-final step
    # (mirrors #447/#458) -> deny.
    plan_bad = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": False},
        {"step": 3, "roles": ["c"], "done": True},
    ]
    bad1 = check_body(447, "Closes #447", "phase2", plan_bad)
    case("phase2 Closes with incomplete non-final step -> denied", len(bad1) > 0)

    # red: phase2, no Closes/Fixes/Resolves at all, plan is None
    # (mirrors #448) -> deny.
    bad2 = check_body(448, "just some text, no closing keyword", "phase2", None)
    case("phase2 no closing keyword, plan None -> denied", len(bad2) > 0)

    # green: phase1, plain #459 reference -> no denial.
    bad3 = check_body(459, "Refs #459, work in progress", "phase1", None)
    case("phase1 plain #459 reference -> allowed", len(bad3) == 0)

    # green: phase2, Closes #459, plan None -> no denial.
    bad4 = check_body(459, "Closes #459", "phase2", None)
    case("phase2 Closes #459, plan None -> allowed", len(bad4) == 0)

    # green: phase2, Closes #459, plan all steps done -> no denial.
    plan_done = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": True},
    ]
    bad5 = check_body(459, "Closes #459", "phase2", plan_done)
    case("phase2 Closes #459, plan all done -> allowed", len(bad5) == 0)

    # green: phase2, only-final-step-incomplete -> Closes required and allowed.
    plan_final_incomplete = [
        {"step": 1, "roles": ["a"], "done": True},
        {"step": 2, "roles": ["b"], "done": False},
    ]
    bad6 = check_body(459, "Closes #459", "phase2", plan_final_incomplete)
    case("phase2 Closes #459, only final step incomplete -> allowed", len(bad6) == 0)

    # sanity: _plan_from_body parses the expected shape.
    body_with_plan = (
        "intro\n\n## 실행 계획\n"
        "- [x] step 1 role-a\n"
        "- [ ] step 2 role-b\n\n## other\nnoise\n"
    )
    parsed = _plan_from_body(body_with_plan)
    case(
        "_plan_from_body parses steps",
        parsed == [
            {"step": 1, "roles": ["role-a"], "done": True},
            {"step": 2, "roles": ["role-b"], "done": False},
        ],
    )
    case("_plan_from_body returns None with no header", _plan_from_body("no header here") is None)

    # --- phase-1 author-written closing-keyword refusal (issue #741 round 2) ---

    # regression, pinned exactly as tests/test_gates.py::
    # t_pr_reference_phase1_does_not_gate_closing_keywords_itself: check_body
    # itself must stay unchanged — it does not gate closing keywords in its
    # phase1 branch, that is _phase1_closes_ref's job, checked separately.
    case(
        "check_body(126, 'Closes #126', 'phase1') == [] (unchanged, gate lives outside check_body)",
        check_body(126, "Closes #126", "phase1") == [],
    )
    case(
        "_phase1_closes_ref(126, 'Closes #126') finds it -> would deny",
        _phase1_closes_ref(126, "Closes #126") is not None,
    )

    # red: PR #763 real-world shape — author wrote a plain '#743' reference
    # AND 'Closes #743' in the same phase-1 body. check_body allows it
    # (plain ref present), the new check must catch the Closes.
    body_763 = "some proposal text\n\n#743\n\nCloses #743"
    case(
        "PR #763 shape: check_body('phase1') allows (plain ref present)",
        check_body(743, body_763, "phase1") == [],
    )
    closes_763 = _phase1_closes_ref(743, body_763)
    case(
        "PR #763 shape: _phase1_closes_ref finds 'Closes #743' -> would deny",
        closes_763 is not None and closes_763.group(1).lower() == "closes",
    )

    # red: decoy-reference shape (after-proposal hunt finding, pinned) — a
    # closing keyword for a DIFFERENT issue (#999) appears earlier in the
    # body than the real 'Closes #743'. A single .search() call would stop
    # at the #999 match and miss the real one; finditer must not.
    body_decoy = "Fixes #999, unrelated context. Closes #743"
    naive_search = _CLOSES_REF.search(body_decoy)
    case(
        "decoy shape: a naive .search() call would find the wrong issue (#999)",
        naive_search is not None and int(naive_search.group(2)) == 999,
    )
    closes_decoy = _phase1_closes_ref(743, body_decoy)
    case(
        "decoy shape: _phase1_closes_ref still finds the real 'Closes #743' via finditer",
        closes_decoy is not None and int(closes_decoy.group(2)) == 743,
    )

    # green regression: phase1, plain '#459' reference only, no closing
    # keyword at all -> check_body allows AND the new check finds nothing
    # to deny (mirrors the existing "phase1 plain #459 reference" case).
    body_plain_only = "Refs #459, work in progress"
    case(
        "phase1 plain #459 reference only: check_body allows (existing case)",
        check_body(459, body_plain_only, "phase1") == [],
    )
    case(
        "phase1 plain #459 reference only: _phase1_closes_ref finds nothing -> allowed",
        _phase1_closes_ref(459, body_plain_only) is None,
    )

    if failures:
        print(f"\n{len(failures)} failure(s): {failures}")
        return 1
    print(f"\nAll {5 + 2 + 1} checks passed" if False else "\nAll checks passed")
    return 0


# --- end-to-end: drives the real pr-preflight.sh (issue #741 round 2) -----
#
# Everything above duplicates the checker logic as plain Python. These
# cases instead run the actual `pr-preflight.sh` script as a subprocess
# against a stub `gh`, per this delivery's own acceptance bar: a
# docs-only phase-1 PR body carrying an author-written `Closes #<issue>`
# must be refused at `gh pr create` time, and a legitimate phase-2 PR must
# still pass through unaffected by the new phase-1-only check.

FAKE_GH_PREFLIGHT = """#!/usr/bin/env python3
import json, os, sys

fixtures = json.load(open(os.environ["GH_FIXTURES"]))
argv = sys.argv[1:]

if argv[:2] == ["issue", "view"]:
    if "comments" in argv:
        print(json.dumps(fixtures.get("issue_comments", [])))
    elif "body" in argv:
        print(json.dumps(fixtures.get("issue_body", "")))
    else:
        sys.exit(1)
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH_PREFLIGHT)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _repo_dir(tmp_path, approvers, branch):
    d = tmp_path / "repo"
    (d / "docs" / "specs").mkdir(parents=True)
    (d / "docs" / "specs" / "approvers.md").write_text(
        "\n".join(f"- {a}" for a in approvers) + "\n"
    )
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=d, check=True)
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
         "commit", "-q", "--allow-empty", "-m", "init"],
        cwd=d, check=True,
    )
    return d


def _run_preflight(cmd, repo_dir, fixtures, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))

    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(PREFLIGHT)],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(repo_dir), timeout=20,
    )


def test_hook_denies_phase1_docs_only_pr_with_author_written_closes(tmp_path):
    """PR #763 real-world shape, driven through the actual hook: a docs-only
    phase-1 PR (no approval comment yet, so phase1) whose author wrote both
    a plain '#743' reference and 'Closes #743' into the body must be
    refused at `gh pr create` time — the issue #741 acceptance bar this
    delivery exists to satisfy."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-743/implementation")
    fixtures = {"issue_comments": []}  # no approval yet -> phase1
    body = "some proposal text, #743, and Closes #743"
    cmd = f'gh pr create --title "proposal" --body "{body}"'
    r = _run_preflight(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "closing" in r.stderr.lower() or "closing" in r.stderr


def test_hook_allows_legitimate_phase2_pr(tmp_path):
    """A genuine phase-2 delivery PR (approval comment present, body
    correctly carries 'Closes #<issue>') must pass through untouched —
    the new phase-1-only check must not reach it."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-743/implementation")
    fixtures = {
        "issue_comments": [
            {"body": "APPROVE issue-743/implementation", "author": {"login": "alice"}},
        ],
        "issue_body": "some issue body, no plan section",
    }
    body = "Closes #743"
    cmd = f'gh pr create --title "delivery" --body "{body}"'
    r = _run_preflight(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


# --- issue #854: heredoc --body extraction truncated at an embedded quote --
#
# PR #844's real `gh pr create --body "$(cat <<'EOF' ... EOF)"` command
# (recovered verbatim from the spawning session's log) is embedded below
# unmodified, plus the same body turned into a `gh pr edit 844 --body ...`
# call with 'Closes #839' appended after the heredoc's own literal,
# unescaped '"무리"' quote — the exact real-world shape that let issue #839
# get auto-closed by a phase-1 PR (docs/issue-854/reports/implementation/
# survey.md has the full incident timeline). Neither command ever actually
# ran through this hook in that incident (the closing PR body edit was made
# directly on github.com, outside any Bash-tool call — confirmed via the
# PR's GraphQL userContentEdits) — these two tests instead confirm the
# hook's *own* behavior against the real command text, independent of how
# that incident happened: the old quote-balance --body regex truncated the
# captured body at the first literal '"' inside the heredoc (before the
# body's 'Closes #839' line even that far in), so a hypothetical in-session
# call carrying this exact shape would have slipped past the phase-1
# closing-keyword refusal too.

REAL_PR844_CREATE_CMD = 'gh pr create --title "issue-839: phase-1 survey + proposal for generated-paths.md row fix + gate-registration-guard classification check" --body "$(cat <<\'EOF\'\n## Summary\n\nAddresses #839 — phase 1 (research + proposal) only, per role-handoff contract v3 s19. No code changes land in this PR; phase 2 opens on Approve.\n\n- `stop-poll-rearm.sh` has no write call in its own file text, but `docs/specs/generated-paths.md` records it `out-of-tree` instead of `n/a` per the spec\'s own file-level grep unit — the row landed wrong in `d4a8228` alongside `poll-rearm.sh`\'s row.\n- `gate-registration-guard.sh` (issue #759) only checks that a spec row *exists* for a newly-staged hook, never that its classification matches what the same commit\'s source derives — so the wrong row landed without the PreToolUse gate catching it.\n- Survey (`docs/issue-839/reports/implementation/survey.md`) decides both judgment calls the issue hands over: (1) fix the doc cell, don\'t change the spec\'s file-level unit — confirmed the unit is already specified by the spec and its origin proposal (issue-684), and changing it would only affect this one row anyway; (2) extend `gate-registration-guard.sh` to reuse `gates/test_generated_paths.py`\'s existing classification derivation, restricted to newly-staged hook scripts — verified live that this is feasible and bounded, not "무리" (impractical).\n- After-proposal warrant hunt (stance 0) found the ported classification check only validates value *shape* (n/a / out-of-tree / issue-scoped, placeholder presence), not truthfulness of an `out-of-tree` claim against a writer hook\'s actual constructed path — a pre-existing gap in `gates/test_generated_paths.py::check()` itself, not introduced here. Folded into the proposal\'s Rationale and Out of scope as an explicit, honest limitation rather than left implicit.\n\n## Test plan\n\n- [ ] Human approver (`docs/specs/approvers.md`) reviews and Approves per contract v3 s19, opening phase 2.\n- [ ] Phase 2: land the `docs/specs/generated-paths.md` row fix and the `gate-registration-guard.sh` extension exactly as scoped in the proposal\'s "What will be done".\n- [ ] Phase 2: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` on the branch vs `origin/main`, failure-set diff = exactly minus one failure (`t_all_generators_recorded_and_disjoint`), pasted into the phase-2 record.\nEOF\n)"\n'

REAL_PR844_EDIT_WITH_CLOSES_CMD = 'gh pr edit 844 --body "$(cat <<\'EOF\'\n## Summary\n\nAddresses #839 — phase 1 (research + proposal) only, per role-handoff contract v3 s19. No code changes land in this PR; phase 2 opens on Approve.\n\n- `stop-poll-rearm.sh` has no write call in its own file text, but `docs/specs/generated-paths.md` records it `out-of-tree` instead of `n/a` per the spec\'s own file-level grep unit — the row landed wrong in `d4a8228` alongside `poll-rearm.sh`\'s row.\n- `gate-registration-guard.sh` (issue #759) only checks that a spec row *exists* for a newly-staged hook, never that its classification matches what the same commit\'s source derives — so the wrong row landed without the PreToolUse gate catching it.\n- Survey (`docs/issue-839/reports/implementation/survey.md`) decides both judgment calls the issue hands over: (1) fix the doc cell, don\'t change the spec\'s file-level unit — confirmed the unit is already specified by the spec and its origin proposal (issue-684), and changing it would only affect this one row anyway; (2) extend `gate-registration-guard.sh` to reuse `gates/test_generated_paths.py`\'s existing classification derivation, restricted to newly-staged hook scripts — verified live that this is feasible and bounded, not "무리" (impractical).\n- After-proposal warrant hunt (stance 0) found the ported classification check only validates value *shape* (n/a / out-of-tree / issue-scoped, placeholder presence), not truthfulness of an `out-of-tree` claim against a writer hook\'s actual constructed path — a pre-existing gap in `gates/test_generated_paths.py::check()` itself, not introduced here. Folded into the proposal\'s Rationale and Out of scope as an explicit, honest limitation rather than left implicit.\n\n## Test plan\n\n- [ ] Human approver (`docs/specs/approvers.md`) reviews and Approves per contract v3 s19, opening phase 2.\n- [ ] Phase 2: land the `docs/specs/generated-paths.md` row fix and the `gate-registration-guard.sh` extension exactly as scoped in the proposal\'s "What will be done".\n- [ ] Phase 2: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` on the branch vs `origin/main`, failure-set diff = exactly minus one failure (`t_all_generators_recorded_and_disjoint`), pasted into the phase-2 record.\n\nCloses #839\nEOF\n)"\n'


def test_hook_allows_real_pr844_create_command_unmodified(tmp_path):
    """PR #844's actual `gh pr create` command, byte-for-byte from the
    session log, carries no closing keyword (only 'Addresses #839') — must
    pass through untouched on the issue-839/implementation branch with no
    approval comment yet (phase1)."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-839/implementation")
    fixtures = {"issue_comments": []}  # no approval yet -> phase1, matches the incident
    r = _run_preflight(REAL_PR844_CREATE_CMD, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


def test_hook_denies_pr844_body_shape_with_closes_after_embedded_quote(tmp_path):
    """Same real body, as a `gh pr edit 844` call, with 'Closes #839'
    appended after the body's own literal '"무리"' quote — must be denied
    (exit 2) on the issue-839/implementation branch, phase1. Red before the
    heredoc-aware --body extraction fix (the old quote-balance regex
    truncated the capture at '"무리"' and never saw 'Closes #839'); green
    after it."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-839/implementation")
    fixtures = {"issue_comments": []}
    r = _run_preflight(REAL_PR844_EDIT_WITH_CLOSES_CMD, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "closing" in r.stderr.lower()


def test_hook_denies_synthetic_heredoc_body_with_embedded_quote_and_closes(tmp_path):
    """Minimal, non-issue-839-specific pin of the same defect class: any
    heredoc --body containing a literal unescaped '"' before a downstream
    'Closes #<issue>' must still be denied in phase1."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-854/implementation")
    fixtures = {"issue_comments": []}
    cmd = (
        'gh pr create --title "proposal" --body "$(cat <<\'EOF\'\n'
        '## Summary\n\nAddresses #854 — phase 1.\n\n'
        '- decided not "무리" (impractical) to do X\n\n'
        'Closes #854\n'
        'EOF\n)"'
    )
    r = _run_preflight(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "closing" in r.stderr.lower()


def test_hook_denies_dash_heredoc_body_with_tab_indented_terminator_and_closes(tmp_path):
    """Before-landing hunt finding (docs/issue-854/reports/implementation/
    2026-08-12-hunt-heredoc-aware-body-extraction.md, stance 0): `cat
    <<-EOF` (the dash form) permits a tab-indented terminator line in real
    bash. The first cut of `_HEREDOC_BODY_RE` only tolerated *trailing*
    whitespace after the delimiter word, never *leading* whitespace before
    it, so a tab-indented `\tEOF` terminator failed to match at all and
    fell through to the old quote-balance regex — reintroducing the exact
    truncation-before-Closes bug this fix exists to close. Must deny."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-854/implementation")
    fixtures = {"issue_comments": []}
    cmd = (
        'gh pr create --title "x" --body "$(cat <<-EOF\n'
        '## Summary\n\nAddresses #854 - phase 1.\n\n'
        '- decided not "무리" (impractical) to do X\n\n'
        'Closes #854\n'
        '\tEOF\n)"'
    )
    r = _run_preflight(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 2, r.stderr
    assert "closing" in r.stderr.lower()


def test_hook_allows_synthetic_heredoc_body_with_embedded_quote_no_closes(tmp_path):
    """Same embedded-quote heredoc shape but with no closing keyword
    anywhere — a legitimate phase-1 body (plain '#854' reference only) must
    still pass; the heredoc-aware extraction must not over-trigger on the
    embedded quote itself."""
    repo_dir = _repo_dir(tmp_path, ["alice"], "issue-854/implementation")
    fixtures = {"issue_comments": []}
    cmd = (
        'gh pr create --title "proposal" --body "$(cat <<\'EOF\'\n'
        '## Summary\n\nAddresses #854 — phase 1.\n\n'
        '- decided not "무리" (impractical) to do X\n'
        'EOF\n)"'
    )
    r = _run_preflight(cmd, repo_dir, fixtures, tmp_path)
    assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    sys.exit(run())
