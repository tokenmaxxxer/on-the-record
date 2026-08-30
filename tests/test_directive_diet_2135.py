"""Issue #2324 — turn-count reduction via action batching.

Measured first (per this issue's own explicit ordering): 10 real session
transcripts under `$MUSTER_WORKSPACE_ROOT` were instrumented for batching
headroom using `docs/issue-2324/_assets/measure_batching_headroom.py`.
Result: 57/713 turns (~8.0%) have an adjacent single-small-call pair with
no detected dependency — below this delivery's own stated 10-15%
"worth a directive rewrite" threshold. Full table, method, and per-
transcript numbers: `docs/issue-2324/reports/diagnose-first-3c31bf9d.md`.

Per the issue's own STOP-AND-REPORT clause ("if the measured headroom is
small... do NOT force a directive change to manufacture a bigger
effect"), no new directive text was written. Investigation into why the
headroom is already this low found the reason: issue #2262's
`_TURN_BUDGET_PROSE` (materialized to
`.on-the-record/directive/turn-budget.md`) already mandates exactly what
this issue's Ask #1 requests — compound Bash (`&&`/`|`) for related greps
in one turn, and foreground `Task`-tool subagent fan-out for wide
exploration — and aims it at investigation-phase calls specifically,
matching PR #2839/#2841's re-aiming evidence that batching pays off in
investigation, not editing.

This test file is the gate named in issue #2324's own Acceptance
section (`tests/test_directive_diet_2135.py` — the name predates this
delivery: `git log --all -S test_directive_diet_2135` shows a file of
this name existed under issue #2135/#2262's original work and was
removed only as part of issue #2525's blanket plugin-test-suite
retirement, not for cause specific to this content; new narrow test
files have continued to land under `tests/` after that retirement, e.g.
issue #2468's `tests/test_tmp_resource_gc.py`). It has two jobs:

1. Regression-guard the existing #2262 batching directive text (the
   thing this issue's measurement found already covers its own ask) —
   if that text is ever weakened or removed, this test catches it even
   though this delivery did not author it.
2. Unit-test the headroom-measurement tool itself
   (`measure_batching_headroom.py`) against small synthetic fixtures,
   including this issue's own empty-state requirement: a genuinely
   serial-dependent adjacent pair (Grep finds a path, Read opens that
   exact path) must NOT be counted as batchable — no forced batching
   where a real dependency exists.

  python3 -m pytest tests/test_directive_diet_2135.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import directive_assembly as da  # noqa: E402

sys.path.insert(0, str(ROOT / "docs" / "issue-2324" / "_assets"))
import measure_batching_headroom as mbh  # noqa: E402


# --------------------------------------------------------------------------
# 1. Regression guard: the #2262 directive already says what #2324 asked for
# --------------------------------------------------------------------------

def test_turn_budget_directive_file_carries_batching_guidance():
    """`.on-the-record/directive/turn-budget.md` is what a spawned
    session actually reads (issue #2204's `--append-system-prompt`
    delivery), but it is gitignored (`.gitignore`: `.on-the-record/
    directive/`) — a per-workspace file materialized fresh at spawn
    bootstrap, not something a fresh checkout/CI run would have on disk.
    The committed, canonical source is `directive_section_files()`'s
    output, which `materialize_directive_sections()` writes verbatim
    into that gitignored path — so exercise the real assembly function
    (same code path a live spawn uses) rather than reading the
    workspace artifact directly."""
    files = da.directive_section_files(
        skills_mounted=False, checkpoint_block=None, code_scoped=False
    )
    text = files["turn-budget.md"]
    # (1) compound-bash-in-one-turn guidance for related greps
    assert "&&" in text and "grep" in text.lower()
    # (2) foreground subagent fan-out for wide exploration (issue #2262
    # operator comment: run_in_background is banned in headless spawns,
    # foreground Task batching is not)
    assert "Task" in text
    assert "Explore" in text or "서브에이전트" in text


def test_turn_budget_prose_constant_matches_materialized_file():
    """`_TURN_BUDGET_PROSE` (the source constant `directive_assembly.py`
    materializes into the workspace file above) must stay the thing
    actually shipped — guards against the constant and the file drifting
    apart silently."""
    files = da.directive_section_files(
        skills_mounted=False, checkpoint_block=None, code_scoped=False
    )
    assert "turn-budget.md" in files
    assert files["turn-budget.md"] == da._TURN_BUDGET_PROSE


# --------------------------------------------------------------------------
# 2. Unit tests for the headroom-measurement tool this issue's finding
#    rests on (docs/issue-2324/_assets/measure_batching_headroom.py)
# --------------------------------------------------------------------------

def _write_fixture_log(lines):
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, encoding="utf-8"
    )
    for obj in lines:
        f.write(json.dumps(obj) + "\n")
    f.close()
    return f.name


def _assistant_line(msg_id, blocks):
    return {"type": "assistant", "message": {"id": msg_id, "content": blocks}}


def _user_result_line(tool_use_id, text):
    return {
        "type": "user",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": text,
                }
            ]
        },
    }


def _tool_use(tid, name, input_):
    return {"type": "tool_use", "id": tid, "name": name, "input": input_}


def test_multi_tool_use_blocks_sharing_a_message_id_are_one_turn():
    """The parsing pitfall this file's own docstring warns about: the
    stream-json log emits one JSONL line per content block, so two
    tool_use blocks under the SAME message.id are one logical turn (a
    batched turn), not two. A naive line-counting parser would report
    this fixture as 2 single-tool turns instead of 1 two-tool turn."""
    lines = [
        _assistant_line("m1", [{"type": "thinking", "thinking": "..."}]),
        _assistant_line("m1", [_tool_use("t1", "Grep", {"pattern": "foo"})]),
        _assistant_line("m1", [_tool_use("t2", "Grep", {"pattern": "bar"})]),
        _user_result_line("t1", "no matches"),
        _user_result_line("t2", "no matches"),
    ]
    path = _write_fixture_log(lines)
    turns, _ = mbh.load_turns(path)
    assert len(turns) == 1
    assert len(turns[0]) == 2


def test_independent_adjacent_single_small_calls_count_as_batchable():
    lines = [
        _assistant_line("m1", [_tool_use("t1", "Grep", {"pattern": "foo"})]),
        _user_result_line("t1", "src/a.py:1:foo"),
        _assistant_line("m2", [_tool_use("t2", "Grep", {"pattern": "bar"})]),
        _user_result_line("t2", "src/b.py:2:bar"),
    ]
    path = _write_fixture_log(lines)
    result = mbh.measure(path)
    assert result["total_turns"] == 2
    assert result["single_small_call_turns"] == 2
    assert result["batchable_adjacent_pairs"] == 1


def test_empty_state_serial_dependent_pair_is_not_forced_batchable():
    """Issue #2324's own empty-state acceptance leg: a task that
    genuinely needs serial dependent calls must not be counted as
    batchable headroom. Fixture: Grep's result names an exact path, and
    the very next call is a Read of that exact path — a textbook
    dependency (you cannot know what to Read until Grep tells you)."""
    lines = [
        _assistant_line(
            "m1", [_tool_use("t1", "Grep", {"pattern": "TODO", "path": "."})]
        ),
        _user_result_line("t1", "docs/issue-2324/_assets/some_discovered_file.py:9:TODO"),
        _assistant_line(
            "m2",
            [_tool_use("t2", "Read", {"file_path": "docs/issue-2324/_assets/some_discovered_file.py"})],
        ),
        _user_result_line("t2", "<file contents>"),
    ]
    path = _write_fixture_log(lines)
    result = mbh.measure(path)
    assert result["total_turns"] == 2
    assert result["single_small_call_turns"] == 2
    assert result["batchable_adjacent_pairs"] == 0


def test_compound_bash_is_not_counted_as_small():
    """A Bash call already using `&&`/`|` is the #2262-recommended output
    shape, not remaining headroom — must not double-count already-batched
    work as still-batchable."""
    tu = mbh._tool_use = None  # not used; direct classify_small check below
    assert mbh.classify_small({"name": "Bash", "input": {"command": "pytest -q && ruff check ."}}) is False
    assert mbh.classify_small({"name": "Bash", "input": {"command": "git status"}}) is True
    assert mbh.classify_small({"name": "Edit", "input": {}}) is False


def test_measurement_artifact_committed_and_reproducible():
    """The `docs/issue-2324/_assets/measure_batching_headroom.py` script
    cited by `derived:` in the record must exist in the working tree so
    the headroom table is reproducible, not a one-off number."""
    script = ROOT / "docs" / "issue-2324" / "_assets" / "measure_batching_headroom.py"
    assert script.exists()
