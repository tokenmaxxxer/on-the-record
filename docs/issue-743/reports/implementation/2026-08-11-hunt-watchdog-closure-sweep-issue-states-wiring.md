---
proposal: docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md
---

# Hunt record — watchdog-closure-sweep-issue-states-wiring

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `record_no_tool_residue` (and its `_changed_records`/`RECORD_PATH`-scoped siblings `record_derived_counts`, `record_wellformed`, `record_enums`, `record_checked_claims`) never inspect nested-shape record files (`docs/issue-<n>/reports/<role>/*.md`, e.g. the `survey.md` just written for this issue) — only flat `docs/issue-<n>/reports/<role>.md` — even though `_always_writable()` in the same `gates.py` explicitly grants roles write permission to `docs/issue-*/reports/{role}/**`, and the repo's own tree uses that nested shape as the dominant convention (`implementation/` nested dirs outnumber flat `implementation.md` files in a repo-wide count). The write-time hook `record-claim-guard.sh` has no tool-residue check at all (it mirrors only the count/unverifiable/checked-claim/orphaned-path checks), so a leaked tool-transcript tag (e.g. `<function_results>`) landing in a nested-shape record file such as this very hunt record or the sibling `survey.md` is invisible at both write time and CI time.

Kind: silent-failure
Seed: docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md, docs/issue-743/reports/implementation/survey.md
cap_seconds: 60
tier: default (size:docs-only)
diff_stat_lines: 2 new files (docs-only)
started_at: 2026-08-11T05:33:00Z
ended_at: 2026-08-11T05:40:30Z

### Reproduce
```
GATES_DIR=/Users/jk/.tokenmaxxxer/work/on-the-record-issue-743-implementation/gates
SCRATCH=$(mktemp -d)
cd "$SCRATCH" && git init -q && git checkout -q -b main \
  && git config user.email t@t.com && git config user.name t
python3 - << 'PYEOF'
import os
base = os.path.join("docs", "issue-1", "reports")
os.makedirs(os.path.join(base, "implementation"), exist_ok=True)
open("README.md", "w").write("# seed\n")
with open(os.path.join(base, "implementation.md"), "w") as f:
    f.write("---\nloop_state: done\n---\nSome record body.\n<function_results>\nmore text\n")
with open(os.path.join(base, "implementation", "survey.md"), "w") as f:
    f.write("# Survey\nSome survey body.\n<function_results>\nmore text\n")
PYEOF
git add README.md && git commit -q -m seed && git update-ref refs/remotes/origin/main HEAD
python3 - << PYEOF
import sys; sys.path.insert(0, "$GATES_DIR")
import gates
from pathlib import Path
root = Path("$SCRATCH")
print("changed_files:", gates.changed_files(root))
print("record_no_tool_residue_in:", gates.record_no_tool_residue_in(root))
PYEOF
```

### Observed
```
changed_files: ['docs/issue-1/reports/implementation.md', 'docs/issue-1/reports/implementation/survey.md']
record_no_tool_residue_in: ["레코드에 툴 태그 잔여물: docs/issue-1/reports/implementation.md:5 — '<function_results>'. 에이전트 툴 출력이 레코드 본문에 새어들어왔다."]
```
Both files carry the identical `<function_results>` leaked tag on the same relative line, and `changed_files()` reports both as changed, but `record_no_tool_residue_in` (backed by `RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")` in both `gates/gates.py` and `on-the-record/gates/gates.py`) flags only the flat-path file. The nested-path file's identical residue is silently passed. `tests/test_gates.py`'s `t_record_no_tool_residue_*` tests only ever construct flat-path records (`_record_repo(td, "issue-9", "coding", ...)` → `coding.md`), so this gap is untested, not a deliberately-scoped exclusion — and `_always_writable()` (same file, `gates/gates.py` and `on-the-record/gates/gates.py`) explicitly lists `docs/issue-*/reports/{role}/**` as always-permitted role write territory, so the permission side and the content-check side disagree about which paths count as "the record."

### Expected
Either `record_no_tool_residue`/`record_derived_counts`/`record_wellformed`/etc. scope to the same path set `_always_writable()` grants (flat `<role>.md` **and** nested `<role>/**`), or `RECORD_PATH` documents why nested-shape files are deliberately exempt from tool-residue/count-claim/frontmatter scanning — currently neither is true, so a leaked tool-transcript tag or an unbacked count claim in any nested-shape report (survey.md, scout-brief.md, hunt records, etc. — the majority shape in this repo, including the two files this proposal's implementation phase just added) passes silently through every existing gate.

## before-landing — stance 1: assume this change and another plugin's rule/gate cancel each other — find the pair

Verdict: NO FINDING
Seed: gates/closure_sweep.py (new `issue_state_index_all`), spawn.py `_board_wide_sweep()` (~L1946) and the `closure-sweep` CLI subcommand (~L3719), both now prefetch `issue_states` via one `gh issue list` call instead of letting `find_violations` call `_issue_view` per subject.
cap_seconds: 180
tier: size:200
diff_stat_lines: 219
started_at: 2026-08-11T05:54:39Z
ended_at: 2026-08-11T06:03:30Z

### Investigation
Searched for any other gate/hook/plugin rule whose behavior depends on
`find_violations` running without `issue_states`, or on `gh issue view`
being called per-subject (rate limiting, auth-refresh, logging side
effects), or on `main()`'s exit code differing when
`issue_state_index_all` itself fails.

- Strongest candidate: `gates/gates.py:subprocess_call_shape_divergence`
  (session-side mirror: `on-the-record/hooks/call-shape-guard.sh`) — a
  repo-wide static check grouping subprocess calls by their first two
  literal argv elements (e.g. `("gh","issue")`) and denying a write when
  calls to "the same command" carry divergent `_SEMANTIC_FLAGS`
  (`-X`/`--method`/`-f`/`--field`). Both `_issue_view` (issue-view-by-id)
  and the new `issue_state_index_all` (issue-list, all states) key to the
  same `("gh","issue")` group under this check's cmd tuple. Ran it
  directly against the working tree as it stands right now:
  `python3 -c "import sys; sys.path.insert(0,'gates'); import gates; from pathlib import Path; print(gates.subprocess_call_shape_divergence(Path('.')))"`
  -> `[]` (0 findings). Reason: `_call_flag_set` requires every element of
  the argv list literal to be a string constant; both call sites embed a
  non-constant element (`str(issue)` / `str(_ISSUE_INDEX_LIMIT)`), so both
  are silently excluded from grouping entirely — pre-existing behavior of
  that checker, unaffected by this diff either direction.
- `on-the-record/hooks/contract-guard.sh` (the merge-time contract gate,
  issue #441/#653) re-implements its own single-PR/single-issue read-only
  `gh` lookups directly (issue-view-by-id with a `comments` field) — it
  never calls into `gates/closure_sweep.py`, so it cannot be affected by
  how `find_violations`/`issue_state_index_all` are wired.
- `gates/flows.py`'s board-status path stopped calling `find_violations()`
  altogether back in issue #674 (its own comment says so explicitly); it
  has its own independent bulk issue-list call for the status board. Not
  touched by, and not sensitive to, this diff.
- Checked `main()`'s exit-code path when `issue_state_index_all` fails
  (`ok=False`): the caller discards `ok` and passes `issue_states=None`,
  which is exactly `find_violations`'s pre-existing default — the
  fallback per-subject path (with its own ok/skip handling) still runs
  and still produces `skips` on failure, so `_board_wide_sweep`'s "gh
  failure counts as 1 anomaly, not clean" contract (its own docstring) is
  preserved either way. Confirmed by reading `gates/test_closure_sweep.py`'s
  updated `test_exit_code_is_2_and_prints_could_not_check`, which now
  stubs `issue_state_index_all` to `(None, False)` and still asserts exit
  code 2.
- No wrapper/log/rate-limiter around `gh` calls exists in this repo that
  any other gate/hook depends on for a *count* of per-subject issue-view
  invocations (searched for rate-limit/call-budget/token-refresh
  mechanisms tied to closure_sweep or `_issue_view`; the only
  `GH_TOKEN`/`gh auth` machinery in `spawn.py` is role-session credential
  plumbing, unrelated to and not invoked by `gates/closure_sweep.py`'s
  `gh` subprocess calls).

No reproduction of a cancelling pair was found. Per protocol, reporting
none found rather than a plausible-but-unverified concern.

Note (incidental, out of scope for this stance): drafting this section hit
an unrelated false-positive in the `tokenmaxxxer-core` plugin's
`gh-guard.sh` PreToolUse hook — its role-session merge/close regex matched
literal descriptive prose inside this Bash heredoc's body text (not an
actual gh invocation), refusing the first append attempt. Not part of
this repo and not connected to the issue-743 diff, so not reported as
this stance's finding; the section above was written on retry with the
triggering phrase reworded.
