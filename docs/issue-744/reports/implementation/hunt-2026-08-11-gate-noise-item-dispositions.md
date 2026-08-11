---
proposal: docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md
---

# Hunt record — gate-noise-item-dispositions

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the survey's "already fixed upstream, verified live" evidence for item 1 (and the untracked-file-staging half of item 4) was read from a git checkout that is a different, newer copy of tokenmaxxxer-core than the one actually cached at Claude Code's real plugin-cache path, and that real cache is stale and missing the fix.
Kind: design-error
Seed: docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md, docs/issue-744/reports/implementation/survey.md
cap_seconds: 180
tier: size:200+
diff_stat_lines: 488
started_at: 2026-08-11T07:57:25Z
ended_at: 2026-08-11T08:01:00Z

### Reproduce

```
$ diff /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh \
       /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/directive.sh

$ grep -rn "reconciled-index" /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/
# (no output — the string is entirely absent from the actual plugin cache tree)

$ grep -n "reconciled-index" /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/directive.sh
163:  regenerate and stage docs/specs/reconciled-index.md (python3

$ stat -f "%Sm %N" /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh
Aug 11 12:03:51 2026 .../plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh

$ cd /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core && \
  git show -s --format="%ci" 78f660d
2026-08-11 13:48:03 +0900
```

### Observed

Two distinct on-disk copies of tokenmaxxxer-core's `core/hooks/directive.sh`
exist on this machine, at different commits:

1. `/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core`
   — the checkout the survey describes reading ("A locally cached checkout
   of that repo (clean, tracking its own origin/main, distinct git
   history)"). It is a real git repo, `git log` shows `HEAD -> main
   [origin/main] 8178711`, working tree clean, and it **does** contain the
   issue-204 reconciled-index guidance text (commit `78f660d`, landed
   2026-08-11 13:48:03 +0900, file mtime 13:52).

2. `/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf`
   — Claude Code's own plugin-cache path (the standard
   `~/.claude/plugins/cache/<repo>/<component>/<hash>/` layout; this
   directory carries `hooks.json` and `.claude-plugin/plugin.json`, i.e. it
   is a resolved, installed plugin bundle, not a scratch clone). Its
   `directive.sh` file mtime is 12:03:51 — **before** commit `78f660d`
   landed — and a recursive grep for "reconciled-index" across this
   entire cache tree returns nothing: the guidance text the survey cites
   as "confirmed present in this session's own context" is not merely
   absent from this file, it is absent from the whole cached bundle. The
   same diff shows this stale cache also lacks the issue-203
   untracked-file-staging guidance and the issue-204 PR-trailer-phase-split
   and test-claim-guard text — i.e. none of the three directive-text fixes
   the survey leans on for items 1 and 4 are present in it.

The survey's evidentiary chain for items 1 and 4 is: "read
tokenmaxxxer-core's git history in a local checkout" plus "this session's
own SessionStart/UserPromptSubmit context already states the fixed
guidance verbatim" — but it never checks, or even names,
`~/.claude/plugins/cache/`, which is the directory Claude Code's plugin
system actually materializes installed plugin content into (evidenced by
its `hooks.json`/`plugin.json` presence and hash-suffixed component
layout, absent from the `runs/rulebooks` checkout). If a role session's
live hooks/directive text is generated from this cache rather than from
`runs/rulebooks` — which is exactly what the standard plugin-cache
mechanism is for — then the "already fixed upstream, verified live"
disposition for item 1 (and part of item 4) is unverified at best and
possibly false for any session whose plugin cache has not been refreshed
past 2026-08-11 12:03: it would still see the old, gate-friction-causing
directive text with no error, no warning, and no visible difference from
a session that correctly received the fix — a silent split between "the
upstream repo has the fix" and "this machine's installed plugin has the
fix" that the proposal treats as settled.

### Expected

Before declaring item 1 (and the untracked-staging portion of item 4)
resolved "upstream, verified live," the survey should have identified
which on-disk copy of tokenmaxxxer-core actually backs this session's
installed "core" plugin (e.g. by locating the plugin-cache path Claude
Code resolves hooks from and diffing it against the checkout used for
git-history verification), rather than treating a `git log`/`gh issue
list` read of one clean checkout as proof of what a live role session's
directive/hook text contains. Absent that check, the proposal's phase-2
record (`docs/issue-744/reports/implementation.md`) should not state item
1 as unconditionally resolved without first confirming (or triggering a
refresh of) the plugin cache that actually governs hook execution.

### Resolution

Verified, not disputed: two on-disk copies of tokenmaxxxer-core do exist,
and the plugins/cache one is stale. But this session's actual hook
invocation does not go through the stale copy, on two independent pieces
of evidence beyond the finding's own diff:

1. This session's own environment carries
   CLAUDE_PLUGIN_ROOT_CORE=/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core,
   and trailer-gate.sh's own first executable line sources
   "${CLAUDE_PLUGIN_ROOT_CORE:-...}/hooks/lib/gate-lib.sh" — when this
   variable is set, it takes precedence over any fallback path, so this
   session's gates resolve from runs/rulebooks, never from the orphaned
   plugins/cache directory.
2. Independent of env-var inspection: real historical denial messages
   from actual past role sessions (issue-759's own session logs, examined
   earlier in this survey) self-report their gate's path as
   .../marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/trailer-gate.sh
   — i.e. when trailer-gate.sh actually fired and denied a real commit
   today, the script's own BASH_SOURCE-derived self-path was already the
   runs/rulebooks copy, not plugins/cache. This is first-person evidence
   of which copy a live session executes, not an inference from
   configuration.

/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf carries
its own .orphaned_at marker (contents: a millisecond epoch timestamp),
consistent with it being a superseded artifact of Claude Code's generic
marketplace-plugin-install path that the CLAUDE_PLUGIN_ROOT_CORE override
(set by whatever provisioned this session, matching spawn.py's own
rulebook-checkout convention per the on-the-record handbook's
architecture section) has since bypassed — not a second, competing
source of truth a live role session could actually read from.

Residual risk this finding correctly surfaces, kept as a note rather than
a blocker: a session launched without CLAUDE_PLUGIN_ROOT_CORE set (e.g.
outside this provisioning path) would fall back to
"$(dirname BASH_SOURCE)/.." — wherever the hook script it actually runs
from resolves to — and could in principle read stale directive text with
no visible error. That is a provisioning-freshness question for
spawn.py/Claude Code's plugin cache, outside on-the-record's own write
set and outside #744's four items; not something this proposal's write
set can fix or needs to.

Closed. code_under_review: docs/issue-744/reports/implementation/survey.md, docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md

## before-landing

docs-only, no before-landing dispatch — every path in this commit's diff
is under docs/ (docs/issue-744/proposals/**, docs/issue-744/reports/**),
so the warrant plugin's docs-only fast path applies and the second
dispatch is skipped per that rule.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — `gates/test_record_lint.py`'s own two documented invocation methods now disagree: the new `@pytest.mark.xfail(strict=True)` test is correctly tolerated under `python3 -m pytest gates/test_record_lint.py -q` (pytest's xfail machinery catches any exception type as "expected"), but the file's own bare `__main__` runner (`_run_all()`, invoked via the file's own docstring-documented `python3 gates/test_record_lint.py`) only recognizes `except AssertionError` as an expected-and-tallied failure — it has no concept of `pytest.mark.xfail` at all, since that marker is inert metadata outside pytest's collector. The new test's body raises `FileNotFoundError` (not `AssertionError` — it writes to `d / "gates" / "real_module.py"` without first creating `d/gates`, a directory `_repo_with_record()` never creates), which propagates straight out of `_run_all()`'s try/except, aborts the whole script with an uncaught traceback, and returns exit code 1 without ever printing the promised `"N/M passed"` summary line. Each half is correct alone: pytest's broad xfail-catches-any-exception semantics is standard and correct; `_run_all()`'s narrow `except AssertionError` was sufficient for every prior test in the file, which only ever fails via a plain `assert`. Together, on the one invocation path the file itself documents as a first-class alternative to pytest, they cancel: the "this failure is expected" contract the xfail marker asserts is simply invisible to the runner that's supposed to also honor it.

Note: no live CI path currently invokes either form automatically — `.github/workflows/` was retired by #460 (confirmed via `on-the-record/hooks/gate-registration-guard.sh`'s own comment: "this repo runs no CI (#460) to run that pytest suite automatically"), so nothing currently asserts a specific exit code or pass count against this file in an automated way. The defect is real and reproduces today regardless: any human (or future CI) that follows the file's own docstring (`python3 gates/test_record_lint.py`) as an equally-valid invocation gets a crash, not a report.

Kind: composition
Seed: gates/test_record_lint.py — two new pytest test functions (see dispatcher prompt); specifically the `@pytest.mark.xfail(strict=True, ...)`-decorated `t_orphaned_path_reference_check_false_positives_documented_gap`
cap_seconds: 120
tier: size:21-200
diff_stat_lines: 50 (1 file changed, 50 insertions(+), per `git diff --stat origin/main -- gates/test_record_lint.py`)
started_at: 2026-08-11T08:08:00Z
ended_at: 2026-08-11T08:19:30Z

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-744-implementation
python3 gates/test_record_lint.py; echo "EXIT_CODE=$?"
```
Compare with the pytest path, which passes cleanly on the identical uncommitted working tree:
```
python3 -m pytest gates/test_record_lint.py -q
```

### Observed
Bare-runner invocation (`python3 gates/test_record_lint.py`) prints 8 `ok` lines, then crashes with an uncaught traceback instead of reaching the 9th test's tallying and the final summary line:
```
ok t_orphaned_path_reference_check_denies_genuinely_missing_path
Traceback (most recent call last):
  File ".../gates/test_record_lint.py", line 210, in <module>
    raise SystemExit(_run_all())
  File ".../gates/test_record_lint.py", line 199, in _run_all
    fn()
  File ".../gates/test_record_lint.py", line 188, in t_orphaned_path_reference_check_false_positives_documented_gap
    (d / "gates" / "real_module.py").write_text("# real file, not the ref\n")
  ...
FileNotFoundError: [Errno 2] No such file or directory: '.../gates/real_module.py'
EXIT_CODE=1
```
The pytest invocation of the same uncommitted working tree, by contrast, reports the xfail correctly: `........x` / `8 passed, 1 xfailed in 2.95s`.

### Expected
Both of the file's own documented invocation methods (`python3 gates/test_record_lint.py` and `python3 -m pytest gates/test_record_lint.py -q`, both listed in the module docstring) should treat the new test identically: either both report it as an expected/known gap, or both report it as a plain failure. Instead the bare runner crashes the entire script (no summary, no exit-code-1-with-FAIL-line, just a raw traceback) the moment it reaches the xfail-marked test, while pytest reports it cleanly as `1 xfailed`.

Closed. code_under_review: gates/test_record_lint.py, on-the-record/hooks/gate-registration-guard.sh, pytest.ini, conftest.py, gates/ci.py (grepped for any automated invoker of this file; none found — `.github/workflows/` retired per #460).
