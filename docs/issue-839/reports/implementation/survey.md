# Current-state survey — issue #839, implementation phase 1

## Write set this proposal will freeze

- `docs/specs/generated-paths.md` (fix the `stop-poll-rearm.sh` row)
- `on-the-record/hooks/gate-registration-guard.sh` (extend the newly-staged
  hook-script check to compare classification, not just row existence)
- `on-the-record/hooks/test_gate_registration_guard.py` (regression case for
  the extension)
- docs/issue-839/reports/implementation.md (phase-2 output, not written
  until the Approve — path does not exist in the tree yet, listed here per
  issue-834's own proposal precedent)

`gates/test_generated_paths.py` is explicitly **not** in the write set —
Decision 1 below keeps its derivation unit unchanged; no code in that file
needs to move.

## Decision 1 — fix the doc cell, or change the spec's unit?

canonical: `docs/specs/generated-paths.md` lines 3-5, current branch HEAD
(`origin/main` `303f816`, working tree clean before this session's edits)

```
3	write-producing call (`write_text`, `open(..., "w")`, `.mkdir(`,
4	`shutil.copy`/`move`) found by grep across `on-the-record/hooks/*.sh`. A
```

The spec's own stated unit is a file-level grep: one row per
write-producing call that appears in that file's own text.

canonical: `gates/test_generated_paths.py` lines 54-60, this session's
read — `_hooks_with_write_calls()` implements exactly that: it globs
`on-the-record/hooks/*.sh` and regex-searches each file's own text; it
never follows a `source`/`.` statement into another file:

```
54	def _hooks_with_write_calls() -> set[str]:
55	    names = set()
56	    for p in sorted(HOOKS_DIR.glob("*.sh")):
57	        text = p.read_text(encoding="utf-8", errors="replace")
58	        if _WRITE_CALL_RE.search(text):
59	            names.add(p.name)
60	    return names
```

canonical: `on-the-record/hooks/stop-poll-rearm.sh` line 34, this session's
read — the only write-adjacent thing in the file is a `source`, not a write
call itself:

```
34	. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/poll-rearm.sh"
```

The actual `mkdir -p`/`git clone` calls live in `poll-rearm.sh`
(`on-the-record/hooks/poll-rearm.sh` lines 48-49 inside
`poll_rearm_resolve_checkout()`, line 57 inside `poll_rearm_arm_if_due()`),
which `stop-poll-rearm.sh` calls as a sourced function, not inline text.

derived: `python3 -c` run against `gates/test_generated_paths.py`'s own
`_hooks_with_write_calls()`, this session

```
$ python3 -c "
import sys; sys.path.insert(0, 'gates')
import test_generated_paths as t
w = t._hooks_with_write_calls()
print('stop-poll-rearm.sh' in w, 'poll-rearm.sh' in w)
"
False True
```

So the test's `n/a` derivation for `stop-poll-rearm.sh` is not a bug in the
test — it is the file-level unit working exactly as
`docs/specs/generated-paths.md` lines 3-5 (quoted above) already define it.

canonical: `docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md`
lines 79-81, this session's read — the origin proposal that created this
mechanism states the unit explicitly, and it is file-level, not
call-graph-level:

```
79	   - derive the actual generator inventory by parsing
80	     `on-the-record/hooks/*.sh` for write-producing calls
81	     (`write_text`, `open(..., "w")`, `mkdir`) and extracting the
```

canonical: same file, lines 39-50, this session's read — the Rationale
section explicitly chose a static-source completeness test over a runtime
interception hook, and gives the reason:

```
39	**Alternative considered: a runtime PreToolUse hook that intercepts every
40	write and checks it live, instead of a static-source enforcement test.**
41	Rejected — the issue explicitly asks for the `test_boundary.py`
...
48	the same trigger event... a static test that reads the hook source and
49	checks the constructed-path shape has no such registration problem and
50	runs in CI on every change, catching the defect before a session ever
```

Nowhere in that proposal's Rationale, Constraints, or "What will be done"
is cross-file / sourced-library write attribution mentioned — the design
intent was mechanical simplicity mirroring `gates/test_boundary.py`, not
tracing execution/call graphs across files.

**Blast radius if the unit were changed instead:** the only way "attribute
a sourced library's write to the caller" could ever change a row is if a
hook sources another hook file at all.

derived: `grep -rlnE` across `on-the-record/hooks/*.sh`, this session

```
$ grep -rlnE '^\s*\.\s+"|^\s*source\s+' on-the-record/hooks/*.sh
on-the-record/hooks/directive.sh
on-the-record/hooks/stop-poll-rearm.sh
```

Only two hooks source anything, and both source the same file
(`poll-rearm.sh`).

canonical: `on-the-record/hooks/directive.sh` line 24, this session's read
— `directive.sh` already matches the write-call regex directly in its own
file text regardless of sourcing (its embedded `cat <<'NOTE'` help-text
heredoc literally contains the string `git clone`, matched as a
false-positive substring, not through any call-graph reasoning):

```
$ grep -nE "write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)|mkdir\s+-p|git\s+clone" on-the-record/hooks/directive.sh
24:  git clone https://github.com/tokenmaxxxer/on-the-record.git ~/.claude/tokenmaxxxer/on-the-record
```

So `directive.sh`'s row (`out-of-tree`, already correct) would not change
under either unit. Changing the spec's unit to trace `source` chains
would, in the current tree, alter exactly one row — `stop-poll-rearm.sh`.

canonical: this survey's own `grep -rlnE` output quoted immediately above
— the issue's warning that other source-family rows would need the same
re-review names a set this grep shows has size one, not open-ended, once
actually checked.

**Decision: fix the doc cell, do not change the unit.** The file-level
grep unit is the one the spec already documents (lines 3-5 above) and the
one issue #684's own proposal specified (lines 79-81 above); it is simpler
than a source-chain-tracing unit (no relative-path resolution, no "does
the sourced file's write function actually get called on this path"
reasoning, no risk of a hook that sources a write-capable library but
never invokes the writing function being mis-flagged as a writer); and,
checked above rather than assumed, it only produces one incorrect row
today. This also matches issue #684's own Rationale, which rejected a
strictly more powerful runtime mechanism for the same reason — the
simpler static mechanism already satisfies the acceptance criteria.

The replacement row must not claim `stop-poll-rearm.sh` "reads/validates
only" the way every other `n/a` row currently reads — that phrase would be
false, since the hook does cause a write, indirectly, every time it runs.
It needs verdict text that says why it is `n/a` under this unit while
pointing at where the real write is recorded (the `poll-rearm.sh` row,
already `out-of-tree`).

derived: `python3 -c` run against a patched in-memory copy of the spec
text (no file on disk changed), this session — shows the exact
replacement row makes the derivation pass with zero other rows affected

```
$ python3 -c "
import sys; sys.path.insert(0, 'gates'); import test_generated_paths as t
spec = t.SPEC.read_text(encoding='utf-8')
old = \"| \`stop-poll-rearm.sh\` | out-of-tree | safe — same shared checkout clone via \`poll-rearm.sh\`'s \`poll_rearm_resolve_checkout()\` |\"
new = \"| \`stop-poll-rearm.sh\` | n/a | reads/validates only in its own file — no write call greppable in this file itself; the actual write happens via the sourced \`poll-rearm.sh\`'s \`poll_rearm_arm_if_due()\`, already recorded out-of-tree on that row |\"
patched = spec.replace(old, new)
recorded = t._recorded_rows(patched)
all_hooks = t._all_hooks(); writers = t._hooks_with_write_calls()
n_a = all_hooks - writers
problems = []
problems += [n for n in all_hooks if n not in recorded]
problems += [n for n in sorted(n_a & recorded.keys()) if recorded[n][0] != 'n/a']
problems += [n for n in sorted(writers & recorded.keys()) if recorded[n][0] not in ('out-of-tree','issue-scoped')]
print('problems:', problems)
"
problems: []
```

## Decision 2 — extend gate-registration-guard.sh to check classification match?

canonical: `on-the-record/hooks/gate-registration-guard.sh` lines 9-15,
this session's read — the hook's own header already states its design
precedent: it ports the same derive-and-compare presence check the two
test modules already implement inline, specifically because a
repo-checkout-relative import cannot be guaranteed at hook-invocation
time. It currently checks row existence only, never classification
correctness.

canonical: same file, lines 139-147, this session's read

```
139	def recorded_names(text):
140	    out = set()
141	    for line in text.splitlines():
142	        if not line.startswith("|") or _SEP_ROW.match(line):
143	            continue
144	        m = _ROW_RE.match(line)
145	        if not m:
146	            continue
147	        name, verdict = m.group(1).strip(), m.group(2).strip()
```

Two facts settle feasibility here, both checked live rather than assumed.

First: `enforcement-boundary.md` is a 2-column table
(`mechanism | verdict`) and `generated-paths.md` is a 3-column table
(`mechanism | classification | verdict`).

canonical: `docs/specs/enforcement-boundary.md` line 12 and
`docs/specs/generated-paths.md` line 13, this session's read, headers
respectively `| mechanism | verdict | ... |`-shaped prose and
`| mechanism | classification | verdict |`.

The guard's shared `_ROW_RE` is non-greedy (`(.+?)` up to the next `|`),
so on a 3-column row `m.group(2)` (bound to the name `verdict` at line
147 above) is already the classification column, not the free-text
verdict.

derived: `python3 -c` run against the guard's own `_ROW_RE`, this session

```
$ python3 -c "
import re
_ROW_RE = re.compile(r\"^\|\s*\`?([^\`|]+?)\`?\s*\|\s*(.+?)\s*\|\", re.MULTILINE)
line = \"| \`stop-poll-rearm.sh\` | out-of-tree | safe — same shared checkout clone via \`poll-rearm.sh\`'s \`poll_rearm_resolve_checkout()\` |\"
print(_ROW_RE.match(line).groups())
"
('stop-poll-rearm.sh', 'out-of-tree')
```

So the guard already has the classification value in hand for every
`generated-paths.md` row it reads — it just discards it after checking
non-emptiness.

Second: the guard's own trigger is narrow by design.

canonical: `on-the-record/hooks/gate-registration-guard.sh` lines 17-26,
this session's read — only a newly-staged hook script (`git diff --cached
--name-status` status `A`/`R`/`C`) fires this check at all; editing an
already-registered module ("M") is untouched.

That means a classification-match extension only ever needs to derive
write-call presence and issue-placeholder shape for the small set of files
in this commit's `hook_scripts` list (already computed at line 128 of the
same file), never the whole `on-the-record/hooks/` directory. The same two
regexes `gates/test_generated_paths.py` already carries are directly
portable into the guard's Python heredoc.

canonical: `gates/test_generated_paths.py` lines 23-30, this session's
read — `_WRITE_CALL_RE` and `_ISSUE_PLACEHOLDER_RE`, the two regexes the
extension would duplicate inline, the same way `recorded_names()`/
`_ROW_RE` already duplicate `test_generated_paths.py`'s
`_recorded_rows()`/`_ROW_RE` rather than importing the module.

canonical: this issue's own body, section "왜 게이트가 못 막았나" — states
that `d4a8228` added both `poll-rearm.sh` and `stop-poll-rearm.sh` as
newly-staged hook scripts in one commit; the guard's existence check
passed for both since both got rows; the classification on one row was
wrong and nothing in the commit path caught it before landing. This is the
exact gap issue #839 reports. A classification-match extension restricted
to `hook_scripts` — reject the commit if a newly-staged hook file has no
write call in its own staged text but is recorded anything other than
`n/a`, or has a write call but is recorded `collision-risk` or a value
outside `{out-of-tree, issue-scoped}`, or is recorded `issue-scoped` with
no issue-placeholder in its own staged text — would have caught this exact
commit at commit time, using logic already exercised by this survey's
Decision 1 verification above.

One correctness detail the extension must not skip: the existing guard
already prefers staged index content over disk content for the spec files
themselves.

canonical: `on-the-record/hooks/gate-registration-guard.sh` lines 154-168,
this session's read — `read_spec()` tries `git show :path` first, disk
fallback second, precisely because the spec row can be part of the same
commit.

The classification check must read the newly-staged hook script's own
content the same way (`git show :path` for each path in `hook_scripts`),
not assume disk equals index — the same principle already applied to the
spec side, extended to the hook-script side for consistency, not a new
principle invented here.

**Decision: yes, extend it.** Reuse is not infeasible — it is a
same-shape, bounded copy of logic the guard already ports inline from the
same source, restricted to the commit's own newly-staged files, with no
risk to already-registered hooks (the guard's narrow trigger, unchanged,
still leaves any plain "M" edit to an existing hook untouched). This
directly closes the gap #839 names: registered-but-wrong-verdict is
exactly what an existence-only check cannot see and a classification-match
check can.

canonical: `on-the-record/hooks/test_gate_registration_guard.py` lines
91-104 (`t_new_hook_script_with_both_rows_in_same_commit_passes`), this
session's read — this existing green case stages a hook with no write
call (`"#!/usr/bin/env bash\nexit 0\n"`) and a row recorded `n/a`; the
extension's `n/a`-must-match branch would still pass it (no write call,
recorded `n/a` — consistent), so the extension does not regress this
existing fixture by inspection of its shape.

## Scout skip record (scout-directive mandatory skip line)

Skip condition: **the spec leaves no design decision open**, for both
decisions, once actually read rather than assumed. Decision 1's unit was
already specified by `docs/specs/generated-paths.md` lines 3-5 (quoted
above) and settled upstream in
`docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md`
(Rationale and "What will be done" sections quoted above — file-level
static grep chosen over a runtime/call-graph mechanism, with a stated
reason) — this proposal applies that existing spec correctly rather than
inventing a new one. Decision 2's shape was already specified by
`gate-registration-guard.sh`'s own header comment (lines 9-15, quoted
above — ports the same derive-and-compare presence check the two test
modules already implement inline) — extending presence-only to
classification-match-also is a continuation of that already-decided
inline-porting design, not a fresh one. Neither decision is product-shaped
(no user-facing surface, no category of comparable products to sample);
both are internal governance-tooling consistency questions fully
answerable by reading this repo's own prior decisions and running the
existing derivation code against the proposed fix, which this survey did
directly (the two `python3 -c` verifications above) rather than deferring
to external scouting. No web/product scouting was run.

## Baseline: main HEAD test state

canonical: `git rev-parse HEAD` and `git rev-parse origin/main`, this
session — both resolve to `303f81654a123ddfefe3f3b0181b126642911c67`,
showing branch HEAD and main HEAD are the literal same commit at survey
time.

Because of that, a single pytest run *is* both the branch-side and the
main-side result for the "failure set" comparison the issue's Acceptance
section asks for — there is no diff yet to produce two different failure
sets from; that comparison becomes meaningful once phase 2 lands the fix
on top of this commit.

canonical: this session's run of
`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`, branch
`issue-839/implementation` at `303f816`, no local changes

```
$ python3 -m pytest gates/ tests/ on-the-record/hooks/ -q
...
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
1 failed, 1209 passed, 2 skipped, 1 xfailed in 191.10s (0:03:11)
```

canonical: same pytest run's failure output — the assertion message
matches issue #839's own quoted reproduction verbatim:
`stop-poll-rearm.sh 는 write 호출이 없는데 docs/specs/generated-paths.md 는
n/a 가 아닌 'out-of-tree' 로 기록했다`.

canonical: `docs/issue-834/reports/implementation/survey.md` lines
172-176, this session's read — that survey recorded the identical
`1 failed, 1209 passed, 2 skipped, 1 xfailed` baseline as pre-existing and
out-of-scope for its own change, independent corroboration that this
failure is stable, isolated to this one row, and not flaking or
compounding with unrelated suite state.
