"""Tests for scripts/lint/silent_failure.py (issue #3228).

Wiring note: this file's own presence is what wires the lint into this
repo's automatically-run checks -- pytest.ini has no per-file
registration step (`norecursedirs` only excludes a few known
directories), so any `test_*.py` file anywhere in the tree is collected
by a plain `python3 -m pytest` run, which is how this repo already runs
its full suite (see gates/probe_full_suite_is_one_command.py's own
docstring: python test files need no registry entry, only non-Python
shell test files do). `scripts/lint/silent_failure.py --self-check` is a
standalone script and would NOT run on its own without something
invoking it; `test_self_check_passes` below is that something.
`gates/check_runner.py` separately re-runs both of this issue's
`## Acceptance` `check:` lines verbatim against this PR's head commit --
the other place this repo already runs checks automatically.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT = REPO_ROOT / "scripts" / "lint" / "silent_failure.py"

sys.path.insert(0, str(LINT.parent))
import silent_failure as sf  # noqa: E402


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LINT), *args],
                           capture_output=True, text=True, timeout=30)


def test_self_check_passes():
    r = _run("--self-check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "FAIL" not in r.stdout


# ---------------------------------------------------------------------
# History proof: reconstructed pre-repair sites vs. the real repaired
# code, for all seven defects issue #3228 names. Mirrors
# scripts/lint/silent_failure.py's own `_CAUGHT_BEFORE`/`_MISSED_BEFORE`
# self-check fixtures -- kept as separate pytest assertions too so a CI
# failure here shows up per-site rather than as one bundled self-check
# verdict.
# ---------------------------------------------------------------------

_CAUGHT = ["site3_git_failure_conflation.py", "site4_missing_timeout.py"]
_MISSED = [
    "site1_2_consumer_preconditions.py",
    "site5_delegation_state_wildcard.py",
    "site6_forgeable_evidence.py",
    "site7_amendment_channel_fixture.py",
]


def test_all_seven_before_fixtures_parse_cleanly():
    """Must-not: reconstructing the seven historical sites is itself
    only meaningful if the lint can read and parse every one of them --
    a parse failure here would silently exclude a site from the
    catch/miss count below instead of reporting it."""
    for name in _CAUGHT + _MISSED:
        r = sf.scan_file(sf._FIXTURES / "history_before" / name)
        assert r.error is None, f"{name}: {r.error}"


def test_catches_sites_3_and_4_before_repair():
    for name in _CAUGHT:
        r = sf.scan_file(sf._FIXTURES / "history_before" / name)
        assert r.findings, f"expected a finding in pre-repair {name}"


def test_stays_quiet_on_all_seven_sites_after_repair():
    for name in _CAUGHT + _MISSED:
        r = sf.scan_file(sf._FIXTURES / "history_after" / name)
        assert r.error is None, f"{name}: {r.error}"
        assert not r.findings, (
            f"repaired {name} should be quiet, got: "
            f"{[f.render() for f in r.findings]}")


def test_documents_five_of_seven_as_out_of_scope():
    """Explicit, plain statement of what this mechanism does not catch
    (issue's own ask: 'if it is not all seven, say which it misses and
    why'). Sites 1/2 (statvfs/zero-inode, one function), 5 (fnmatch
    wildcard), 6 (evidence provenance), 7 (test-fixture realism) involve
    no subprocess call site at all -- the chosen mechanism structurally
    cannot see them. 2 of 7 caught, 5 of 7 (grouped as 4 fixtures, since
    sites 1 and 2 share one function) out of scope by construction."""
    assert len(_CAUGHT) == 2
    assert len(_MISSED) == 4  # covers defects 1, 2, 5, 6, 7 (1+2 share a fixture)


# ---------------------------------------------------------------------
# Must-not demonstrations: never a silent pass on what the lint could
# not read or parse.
# ---------------------------------------------------------------------

def test_unreadable_file_is_reported_not_skipped(tmp_path):
    ghost = tmp_path / "does_not_exist.py"
    r = sf.scan_file(ghost)
    assert r.error is not None
    assert not r.findings


def test_syntax_error_file_is_reported_not_skipped():
    r = sf.scan_file(sf._FIXTURES / "syntax_error" / "bad_syntax.py")
    assert r.error is not None
    assert "syntax error" in r.error.lower()


def test_cli_reports_read_and_parse_errors_and_exits_nonzero(tmp_path):
    missing = tmp_path / "gone.py"
    r = _run(str(missing), str(sf._FIXTURES / "syntax_error"))
    assert r.returncode != 0
    assert "cannot read" in r.stdout
    assert "syntax error" in r.stdout


def test_empty_state_refuses_a_clean_pass():
    summary = sf.scan_targets([str(sf._FIXTURES / "no_subprocess")])
    assert summary.call_sites == 0
    assert not summary.errors
    r = _run(str(sf._FIXTURES / "no_subprocess"))
    assert r.returncode != 0
    assert "no subprocess call sites" in r.stdout


# ---------------------------------------------------------------------
# Regression guard: the two real FUNCTIONS sites 3 and 4 actually lived
# in stay quiet today -- this is what "wires" the lint against a future
# reintroduction at these exact sites. Deliberately scoped to those two
# functions, not the whole file: running the lint unfiltered over
# scripts/issue-3127/verify_preregistration.py also surfaces SF003
# candidates in `_repo_owner_repo`/`_pr_merge_commit`/`_pr_commit_order`/
# `_first_pr_commit_touching` -- helpers where EVERY failure mode
# (command failure, malformed JSON, an absent field) deliberately
# collapses to the same `None`-means-"fail closed, exclude" signal,
# which their one caller always treats identically. That is a different,
# and correct, pattern from the site-3 bug (a command failure conflated
# with a genuinely-valid empty result that fed two DIFFERENT downstream
# branches) -- but this per-function AST lint cannot see the caller to
# tell the two apart, so it flags both alike. Issue #3228 named sites 3
# and 4 specifically, not these other pre-existing helpers, and "do not
# fix more sites" means this PR does not retroactively annotate or
# rewrite them; each would need its own `# silent-failure: allow
# <reason>` (the escape hatch this lint provides for exactly this case)
# or a rule refinement, as a separate, later decision.
# ---------------------------------------------------------------------

_REGRESSION_TARGET = "scripts/issue-3127/verify_preregistration.py"
_REGRESSION_FUNCTIONS = ("_run_git", "_first_commit_for_path")


def _line_ranges_for(path: Path, names) -> list:
    import ast as _ast
    tree = _ast.parse(path.read_text(encoding="utf-8"))
    ranges = []
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and node.name in names:
            ranges.append((node.lineno, node.end_lineno))
    return ranges


def test_real_repaired_functions_stay_quiet():
    target = REPO_ROOT / _REGRESSION_TARGET
    ranges = _line_ranges_for(target, _REGRESSION_FUNCTIONS)
    assert len(ranges) == len(_REGRESSION_FUNCTIONS), (
        f"expected to find {_REGRESSION_FUNCTIONS} in {target}")
    r = sf.scan_file(target)
    assert r.error is None, f"{target}: {r.error}"
    in_scope = [f for f in r.findings
                if any(lo <= f.line <= hi for lo, hi in ranges)]
    assert not in_scope, (
        f"{_REGRESSION_FUNCTIONS} should be quiet, got: "
        f"{[f.render() for f in in_scope]}")


def test_allow_marker_exempts_a_call_from_sf001_and_sf002(tmp_path):
    src = tmp_path / "allowed.py"
    src.write_text(
        "import subprocess\n"
        "\n"
        "def fire_and_forget():\n"
        "    subprocess.Popen(['true'])  # silent-failure: allow test double, never awaited\n"
    )
    r = sf.scan_file(src)
    assert r.error is None
    assert not r.findings
