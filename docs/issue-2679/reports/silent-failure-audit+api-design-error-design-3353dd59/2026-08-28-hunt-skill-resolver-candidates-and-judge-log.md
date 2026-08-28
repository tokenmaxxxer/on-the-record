---
proposal: docs/issue-2679/proposals/skill-resolver-candidates-and-judge-log.md
---

# Hunt record — skill-resolver-candidates-and-judge-log

## before-landing — stance 0: assume the gate/check just touched is bypassable — find the bypass

Verdict: FINDING — the new stderr audit-log lines in `consult.py`'s `_cross_family_skill_matches_with_consult()` don't cover the `remaining <= 0` early return (fast-path fills every requested slot), so that path silently prints nothing, indistinguishable from the pre-fix "no log at all" state the diff was written to eliminate.
Kind: silent-failure
Seed: consult.py diff (`_cross_family_skill_matches_with_consult`), spawn.py diff (`_spawn_one`'s `_cross_family_future is None` print), skills.py diff (`_available_skills_clause` + its two call sites)
cap_seconds: 120
tier: size:mid (diff_stat_lines: ~123 lines across 5 files)
diff_stat_lines: 116 (git diff --stat: consult.py +11, skills.py +25/-2, spawn.py +14/-2, two test files +73)
started_at: 2026-08-28T00:00:00Z
ended_at: 2026-08-28T00:20:00Z

The diff's own stated purpose (per its comments) is: "no stderr line" must no
longer be ambiguous between "judge succeeded" / "judge fail-opened" / "judge
was never invoked" — it adds a print on the `except Exception` fail-open path
(pre-existing), the "completed" success path (new), and *both* named
no-candidates early returns (`scored` empty, and post-fast-path `candidates`
empty; both new). It does not add one to the third early return in the same
function, three lines above the "candidates empty" check:

```python
outcome_prefix = f"fast-path:{','.join(fast_names)}" if fast_names else ""
remaining = k - len(fast_dirs)
if remaining <= 0:
    return fast_dirs, outcome_prefix   # <-- no print: judge never invoked, no log line
```

When exact-phrase fast-path picks alone fill the full `k` budget, the
function returns without ever calling `_skill_judge_consult`, exactly the
"judge never invoked" state the other three branches were just given a
distinct line for — but this one still emits nothing on stderr, so a spawn's
stderr log for this outcome is bit-for-bit identical to the log for a
crash-before-this-function-runs case, silently defeating the very
distinguishability the rest of the diff adds.

### Reproduce
```python
import sys, io
sys.path.insert(0, "gates")
sys.path.insert(0, ".")
import spawn
import consult
from pathlib import Path

fake_dir = Path("/tmp/fake-skill-dir")
scored = [(10.0, "my-skill", fake_dir, "skill-repo")]
spawn._bm25_cross_family_scores = lambda *a, **k: scored
spawn._skill_declared_phrases = lambda d: ["do the thing"] if d == fake_dir else []
spawn._CROSS_FAMILY_CONSULT_TOPN = 5
spawn._tokenize = lambda s: s.split()

buf = io.StringIO()
old_stderr = sys.stderr
sys.stderr = buf
try:
    picked, outcome = consult._cross_family_skill_matches_with_consult(
        "please do the thing now", "worker", None, None, None, k=1)
finally:
    sys.stderr = old_stderr

print("picked:", picked)
print("outcome:", outcome)
print("stderr captured:", repr(buf.getvalue()))
```
Run: `python3 <script above>` from repo root (module search path needs
`gates` first, matching how spawn.py/consult.py import each other in this
tree).

### Observed
```
picked: [PosixPath('/tmp/fake-skill-dir')]
outcome: fast-path:my-skill
stderr captured: ''
```
`outcome` correctly reports `fast-path:my-skill` (judge not invoked, filled
by fast-path alone) but stderr is empty — no audit line at all for this
"judge never invoked" state.

### Expected
Per the diff's own rationale (comment directly above the `scored` empty
check: "이 줄이 없다"가 성공과 not-invoked 두 상태를 동시에 뜻하게 된다"),
every "judge not invoked" branch should print a distinguishing line so
"nothing on stderr" never again means "judge succeeded, fail-opened, or
wasn't invoked" ambiguously. The `remaining <= 0` fast-path-fills-everything
return is such a branch and currently prints nothing, same as before this
diff.

### Resolution
Fixed same session, before landing: `consult.py`'s `remaining <= 0` branch
now prints `[{role}] skill_judge 자문 안 함 — fast-path 로 슬롯이 다 참:
{outcome_prefix}` before returning.
derived: re-ran this record's own repro script — result: `stderr captured`
now contains `"[worker] skill_judge 자문 안 함 — fast-path 로 슬롯이 다 참:
fast-path:my-skill\n"` instead of `''`.
Regression test added: `test/test_spawn_cross_family_skill_selection.py::
ConsultJudgeStageTest::test_fast_path_fills_all_slots_prints_distinguishable_line`.
checked: `python3 -m pytest -q test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest -k "fast_path or completed or no_bm25 or fail_open"` — result: 4 passed.
