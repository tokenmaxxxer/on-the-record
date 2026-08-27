---
issue: 2637
role: architecture-interface-contract-shape+silent-failure-audit-a86b8985
author: architecture-interface-contract-shape+silent-failure-audit-a86b8985
skills: architecture-interface-contract-shape (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review:
  - path: priorities.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: on-the-record/hooks/deliverable-guard.sh
    sha: same-commit
  - path: on-the-record/hooks/product-capture-stopgate.sh
    sha: same-commit
  - path: on-the-record/hooks/skill-verdict-guard.sh
    sha: same-commit
type: fix
breaking: none
verdict: pass
upstream:
  - path: docs/issue-2333/reports/implementation.md (consult-log.md per-session sharding — the directory/filename/aggregate-reader shape this issue mirrors)
    sha: same-commit
  - path: docs/issue-2348/reports/implementation.md (hook_fires.py/deviation_log.py extending #2333's shape, incl. the module-docstring divergence convention this record follows)
    sha: same-commit
---
skill-verdict: architecture-interface-contract-shape — applied: invoked; rule 12 (minimal reader contract hiding filename convention) + rule 8 (Open Host Service/Published Language for many unknown writer-sessions) applied to the directory+reader design
skill-verdict: silent-failure-audit — applied: invoked; audited the reader's directory-missing-vs-real-error distinction at priorities.py:114-118 (see "Silent-failure-audit finding" below)

# issue-2637 — architecture-interface-contract-shape+silent-failure-audit-a86b8985 record

## What was done

derived: `git diff --stat` on the files listed in `code_under_review` above (reproduced in "Diff stat" below) + `priorities.py` (new file, full contents read back this session).

Converted `docs/reports/product/priorities.md` (and its issue-scoped variant
`docs/issue-<n>/reports/product/priorities.md`) from a single append-only
file into a directory of one file per product-capture entry
(`docs/reports/product/priorities/<timestamp>-<pid>.md`), the same
conflict-elimination shape issue #2333 shipped for `consult-log.md` and
issue #2348 extended to `.orchestrate-hook-fires.log`/`deviation-log.md`.
This removes the collision class that hit PR #2632/#2633 (issue #2637
body: both landed disjoint, correct code changes but collided on this one
shared append-only file, costing a dedicated rebase session).

New/changed files:

- `priorities.py` (new, repo root) — `_priorities_dir()`,
  `_priorities_legacy_path()`, `_priorities_entry_path()` (writer-side path
  minter, one fresh path per call), `read_priorities()` (reader, returns
  entries in filename/chronological order as a list), `priorities_aggregate()`
  (concatenated-string reader, mirrors `_consult_log_aggregate()`'s
  single-string return shape for CLI printing).
- `spawn.py` — imports `priorities`, aliases `_priorities_aggregate` /
  `_priorities_entry_path`, adds two CLI subcommands: `priorities-path`
  (prints the path a session's next new entry belongs in — a session then
  writes it directly with its own Write/Edit call, no orchestrator/
  coordinator involved) and `priorities-log` (prints the reconstructed
  single-file view, mirroring `consult-log`/`deviation-log`).
- `on-the-record/hooks/deliverable-guard.sh` — widened the product-capture
  write exemption to also allow shard files under the new
  `priorities/`/`docs/issue-<n>/.../priorities/` directories (the legacy
  flat-file exemption is kept, unchanged, since the old file still exists
  on disk).
- `on-the-record/hooks/product-capture-stopgate.sh` — the "priorities"
  category's git-diff/git-log nudge check now targets the shard directory
  instead of a single file path, with a `git status --porcelain` fallback
  for a brand-new untracked shard (mirrors `deviation-log-guard.sh`'s own
  #2348 fix, same reasoning: `git diff`/`git log -p` never report
  untracked paths). The advisory message text for this category now names
  `priorities/ (spawn.py priorities-path; ...)` instead of `priorities.md`.
- `on-the-record/hooks/skill-verdict-guard.sh` — updated the end-of-session
  obligations reminder's product-capture sentence to mention the new
  `spawn.py priorities-path` entry point (wording only, no logic change).
- this record itself (new, uncommitted as of this session).

### Diff stat

acceptance: `git diff --stat -- on-the-record/hooks/deliverable-guard.sh on-the-record/hooks/product-capture-stopgate.sh on-the-record/hooks/skill-verdict-guard.sh spawn.py` — result:

```
 on-the-record/hooks/deliverable-guard.sh        | 24 ++++++++++++---
 on-the-record/hooks/product-capture-stopgate.sh | 41 +++++++++++++++++++++++--
 on-the-record/hooks/skill-verdict-guard.sh      |  3 +-
 spawn.py                                        | 22 +++++++++++++
 4 files changed, 82 insertions(+), 8 deletions(-)
```

Plus one new file, `priorities.py` (135 lines).

## Why

derived: `consult.py`/`hook_fires.py`/`deviation_log.py` read in full this session (module docstrings + `_consult_trace_dir`/`_consult_trace_path`/`_consult_log_aggregate` at consult.py:307-344, reproduced below) — precedent shape confirmed by direct reading, not by summary.

### Precedent followed (not invented)

Read `consult.py`'s `_consult_trace_dir()` / `_consult_trace_path()` /
`_consult_log_aggregate()` (issue #2333) and `hook_fires.py` /
`deviation_log.py` (issue #2348, which explicitly documents where and why
each diverges from #2333's shape in its own module docstring). The exact
text read this session, `consult.py:332-344`:

```python
def _consult_log_aggregate(issue: int | None, cwd: str | None = None) -> str:
    """이슈 #2333: 오늘까지의 단일-파일 뷰를 재구성하는 리더/애그리게이터
    — `_consult_trace_dir()` 아래 모든 세션 샤드를 파일명(=`<타임스탬프>-
    <pid>`, 타임스탬프가 고정 폭이라 사전순 정렬이 곧 시간순) 순으로 이어
    붙인다. ...
    """
    d = _sp._consult_trace_dir(issue, cwd)
    if not d.is_dir():
        return ""
    return "".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
```

Mirrored exactly:

- Directory named after the artifact, extension dropped
  (`consult-log.md` → `consult-log/`; here `priorities.md` →
  `priorities/`), issue-scoped variant one level under
  `docs/issue-<n>/reports/...`, same split every precedent uses.
- Shard filename `<timestamp>-<pid>.md`, timestamp
  `%Y%m%dT%H%M%S%f` UTC (fixed-width, microsecond resolution) — identical
  formula to `consult.py`'s `_consult_trace_path()` — so filename sort is
  chronological sort.
- Reader is a directory-glob-and-concatenate function returning the
  pre-migration single-file view, empty result (not an exception) when
  nothing has ever been captured — same shape as `_consult_log_aggregate()`
  / `_hook_fires_aggregate()` / `_deviation_log_aggregate()`.
- Write path needs no orchestrator/coordinator: a session calls
  `_priorities_entry_path()` (or `spawn.py priorities-path`) for its own
  unique path and writes its own entry directly, exactly like
  `_consult_trace_path()`/`_deviation_log_path()`.

### One genuine, stated divergence: one file per ENTRY, not one file per SESSION

derived: `deviation_log.py` module docstring, lines 1-27, read in full this session (point 1, reproduced below).

Every #2333/#2348 precedent shards by session: `consult.py` caches
`_CONSULT_SESSION_SHARD_ID` for a process's lifetime so repeated
`consult()` calls in one session land in the same shard file;
`deviation_log.py`'s `_deviation_log_shard_id()` explicitly re-finds and
reuses an existing shard for the same session. From `deviation_log.py`'s
own module docstring, point 1:

```
1. The writer is the session itself, appending a line by hand via its own
   Edit/Write tool calls mid-task -- never a subprocess `spawn.py` can cache
   a shard id inside for a process's lifetime (`consult.py`'s
   `_CONSULT_SESSION_SHARD_ID`) or a bash hook can hash from a stdin JSON
   payload it always receives (`hook_fires.py`'s `_hook_fires_shard_id()`).
```

Issue #2637's design contract instead calls for one file PER ENTRY. This
is not an invented third convention — it is the correct adaptation
because a product-capture entry is a single one-shot scribing act (the
orchestrator records one operator decision and moves on), not a burst of
repeated appends the way a session's several consult/deviation-log calls
can be within one turn. `_priorities_entry_path()` therefore mints a
fresh filename on every call and never caches/reuses one — simpler than
either precedent's shard-id-reuse machinery, and still exactly as
collision-safe (timestamp+pid). Stated in `priorities.py`'s own module
docstring as well, not just here.

### Migration decision: compatible reader, no rewrite of history (Step 4)

canonical: `docs/reports/product/priorities.md` read in full this session (10 entries, 202 lines); `docs/reports/consult-log.md` + `docs/reports/consult-log/` both inspected this session via `ls -la` (reproduced below) to confirm the precedent's own migration treatment.

Two options were on the table: (a) migrate all 10 existing `priorities.md`
entries into individual per-entry shard files, or (b) leave the legacy
flat file exactly as-is and make the reader read both it and the new
directory. Picked (b), simplest option that still satisfies "do not lose
or reorder any existing entry":

- No parsing/splitting risk: the 10 existing entries are multi-line,
  bullet-prefixed, sometimes containing nested quoted text with its own
  line breaks. Mechanically re-splitting them into individually-timestamped
  files risks silently mis-attributing a continuation line to the wrong
  entry, or losing exact original wording. Reading the file verbatim and
  never touching it again has zero such risk.
- Precedent already validates this half of the approach — the legacy file
  is left in place, untouched:

```
$ ls -la docs/reports/consult-log.md docs/reports/consult-log
-rw-rw-r-- 1 jwjung jwjung 35270  8월 27 17:38 docs/reports/consult-log.md
docs/reports/consult-log:
합계 ... (directory of per-session .md shard files)
```

  The difference from consult-log: `_consult_log_aggregate()` (quoted
  above) does NOT read the old flat file at all — its reader only ever
  covers the new directory going forward, acceptable there because
  nothing required the post-migration reader to keep surfacing
  pre-migration history. Issue #2637 explicitly requires no loss from the
  reader's perspective, so `read_priorities()` deliberately does more than
  `_consult_log_aggregate()`: it prepends the legacy file's full verbatim
  content ahead of the new directory's shards (`priorities.py:111-118`,
  quoted in full under "Silent-failure-audit finding" below). No entry is
  rewritten, re-timestamped, or re-split.

### requirements.md / philosophy.md / goals.md (Step 3 finding)

derived: `find` + `ls` commands below, executed this session against the live checkout.

`on-the-record/hooks/product-capture-stopgate.sh` handles all four
categories (`requirements`, `priorities`, `philosophy`, `goals`) through
the same generic per-category loop, and
`on-the-record/hooks/deliverable-guard.sh` exempts all four through the
same generic suffix/regex pattern — so the *mechanism* (advisory nudge +
write-exemption) is identical across all four categories. However, none
of the three other files (`requirements.md`, `philosophy.md`, `goals.md`)
under `docs/reports/product/` or any `docs/issue-<n>/reports/product/`
actually exists anywhere in the repo:

```
$ find . -path ./.git -prune -o -iname "requirements.md" -print -o -iname "philosophy.md" -print -o -iname "goals.md" -print 2>/dev/null | grep -v .git
./docs/specs/requirements.md
./docs/issue-54/proposals/requirements.md
```
(neither hit is under a `reports/product/` path — both are unrelated docs;
zero matches for the product-capture category files themselves.)

```
$ ls docs/reports/product/
2026-08-14-hiring-market-recon.md
priorities.md
quality-bar.md
```
(no `requirements.md`/`philosophy.md`/`goals.md` — only `priorities.md`
has ever actually been captured into.)

Conclusion: the three are NOT converted in this PR. Not because they use a
different write path (they use the identical generic mechanism) but
because (a) issue #2637's own scope names `priorities.md` specifically,
and it never landed a real conflict for the other three since none of
them has ever been written to, and (b) per the issue's own instruction,
converting them "even if identical" is a follow-up call, not something to
silently assume in this PR. If any of the three is ever written to and
collides the same way, `priorities.py`'s shape is the ready-made template.

## Silent-failure-audit finding

canonical: `priorities.py:111-119` (exact function body reproduced below, read back from disk this session).

`priorities.py`'s `read_priorities()` — the directory/file-missing check
and the real-error propagation are structurally separated, not
distinguished by an except-type list:

```python
    entries: list[str] = []
    legacy = _priorities_legacy_path(issue, cwd)
    if legacy.is_file():
        entries.append(legacy.read_text(encoding="utf-8"))
    d = _priorities_dir(issue, cwd)
    if d.is_dir():
        entries.extend(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
    return entries
```

(`priorities.py:114-118`, `entries: list[str] = []` at line 111.) The ONLY
silent-empty case is `legacy.is_file()` false AND `d.is_dir()` false
(neither the legacy file nor the shard directory exists — nothing has
ever been captured): the function returns `[]`, not an exception,
matching the old "file not found" empty state every #2333/#2348 reader
treats the same way (per `_consult_log_aggregate()`'s own `if not
d.is_dir(): return ""` branch, quoted above under "Precedent followed").
Every `read_text()` call is deliberately left OUTSIDE any try/except — a
permission-denied directory, an unreadable shard file, or a
malformed/undecodable entry (`UnicodeDecodeError`) propagates as a real
exception to the caller instead of being folded into the same `[]` an
absent directory produces. This is the audited distinction: presence
checks (`is_file()`/`is_dir()`) are the one legitimate "nothing happened
yet" branch; everything downstream of a positive presence check is
unguarded and surfaces.

## What did not work

canonical: before-landing warrant-hunter agent output (stance 0, "assume the gate just touched is bypassable"), reproduced verbatim below.

The before-landing warrant-hunter dispatch found a real bypass in the
first draft of `on-the-record/hooks/deliverable-guard.sh`'s new
`PRODUCT_CAPTURE_PRIORITIES_DIR_RE` regex — it used unanchored
`re.search()`, so a deliverable write ending in the shard-suffix pattern
but not actually located there was silently exempted. Hunter's literal
finding text:

```
FINDING — `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` in `on-the-record/hooks/deliverable-guard.sh`
is unanchored (`re.search` with no `^`), so a deliverable path like
src/docs/reports/product/priorities/hack.md is silently exempted from the
deny-only deliverable guard even though it is not actually inside
docs/reports/product/priorities/ — it only needs to end with that suffix.
Reproduced: an equivalent plain src/hack.md write is correctly denied
(exit 2), but src/docs/reports/product/priorities/hack.md sails through
with exit 0 and no stderr message, letting an orchestrator session write
directly into src/ (role-work territory) under this new exemption.
```

Full command-level reproduction and expected-vs-observed detail: the
hunt record written this session alongside this one (same uncommitted
delivery, lands in the same commit) — not yet independently committed at
Write time, so not backtick-cited here per this record's own citation
rule; its content is quoted above verbatim instead.

Fixed by anchoring both alternatives of the regex with `^` (the checked
path is already repo-root-relative by construction). Re-verified this
session — derived: two `deliverable-guard.sh` invocations run back to
back with `TOKENMAXXXER_SPAWNED` unset (reaches the orchestrator code
path), one with the exploit-shaped path, one with a genuine shard path:

```
$ env -u TOKENMAXXXER_SPAWNED bash -c '... file_path=src/docs/reports/product/priorities/hack.md ... | bash on-the-record/hooks/deliverable-guard.sh; echo "bypass exit: $?"'
orchestrate: this is an orchestrator session and src/docs/reports/product/priorities/hack.md is a deliverable path in a board repo. ...
bypass exit: 2

$ env -u TOKENMAXXXER_SPAWNED bash -c '... file_path=docs/reports/product/priorities/20260827T000000000000-999.md ... | bash on-the-record/hooks/deliverable-guard.sh; echo "legit exit: $?"'
legit exit: 0
```

Left unfixed, explicitly out of scope for issue #2637: the same function
has two PRE-EXISTING checks sharing the identical unanchored-suffix-match
class (`n.endswith(EXEMPT_SUFFIXES)` and the earlier
`PRODUCT_CAPTURE_ISSUE_RE.search(n)`, neither anchored with `^`) that
predate this change — this session did not introduce them; whether to fix
them is a separate follow-up call for a future session.

## Upstream basis

- `docs/issue-2333/reports/implementation.md` (and `consult.py`'s
  `_consult_trace_dir()`/`_consult_trace_path()`/`_consult_log_aggregate()`,
  read directly this session, unchanged by this PR, cited for their shape
  only — quoted verbatim above under "Precedent followed") — directory-of-
  shards + filename-sortable-is-chronological + directory-glob aggregate
  reader, the shape this issue mirrors.
- `docs/issue-2348/reports/implementation.md` (and `hook_fires.py`/
  `deviation_log.py`, read directly this session, unchanged by this PR,
  quoted verbatim above) — the module-docstring convention of stating any
  divergence from #2333's shape explicitly, which this record follows for
  the one-file-per-entry divergence and the compatible-reader divergence.
- `docs/reports/product/priorities.md` (read in full this session before
  any change — all 10 existing entries preserved verbatim, file untouched
  by this PR; the new reader treats it as the legacy block, see Why).

## Consumer audit (Step 2)

derived: `git grep` commands below, run against `HEAD` (the pristine pre-change tree, unaffected by this session's own uncommitted edits) — literal output reproduced, not summarized.

```
$ git grep -l "priorities.md" HEAD | wc -l
25
```

```
$ git grep -l "priorities.md" HEAD | sort
HEAD:docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md
HEAD:docs/issue-1111/reports/implementation.md
HEAD:docs/issue-1111/reports/implementation/survey.md
HEAD:docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md
HEAD:docs/issue-1117/reports/implementation.md
HEAD:docs/issue-1117/reports/implementation/deviation-log.md
HEAD:docs/issue-1117/reports/implementation/survey.md
HEAD:docs/issue-1118/decisions/generator-choice.md
HEAD:docs/issue-1118/reports/implementation.md
HEAD:docs/issue-1599/reports/implementation.md
HEAD:docs/issue-2285/reports/conformance-review.md
HEAD:docs/issue-2315/reports/conformance-review.md
HEAD:docs/issue-2382/reports/conformance-review.md
HEAD:docs/issue-2409/reports/execution-observation/deviation-log/20260826T043804395043-428239a958d68694.md
HEAD:docs/issue-2414/reports/conformance-review.md
HEAD:docs/issue-2467/reports/conformance-review.md
HEAD:docs/issue-2467/reports/execution-observation.md
HEAD:docs/issue-2629/reports/conformance-review.md
HEAD:docs/issue-2631/reports/execution-observation.md
HEAD:docs/issue-566/proposals/architecture.md
HEAD:docs/issue-566/proposals/implementation.md
HEAD:docs/issue-566/proposals/product-discovery.md
HEAD:docs/issue-688/reports/implementation/hunt-2026-08-11-delegated-judgment-corpus-path.md
HEAD:docs/reports/2026-08-11-hunt-generated-path-disjointness.md
HEAD:on-the-record/hooks/deliverable-guard.sh
```

A literal-string grep for `"priorities.md"` misses any consumer that
builds the path programmatically (e.g. `f"{cat}.md"`). Broader sweep to
catch those:

```
$ git grep -ln "priorities" HEAD -- "*.py" "*.sh"
HEAD:on-the-record/hooks/deliverable-guard.sh
HEAD:on-the-record/hooks/product-capture-stopgate.sh
HEAD:on-the-record/hooks/skill-verdict-guard.sh
```

Full consumer list and disposition (24 doc-only + 3 code, one code file
counted in both sweeps above):

| Consumer | Kind | Status |
|---|---|---|
| `on-the-record/hooks/deliverable-guard.sh` | code — write-permission exemption list | **Updated**: widened to also exempt the new `priorities/` shard directory (both bucket and issue-scoped forms), legacy exact-suffix exemption kept |
| `on-the-record/hooks/product-capture-stopgate.sh` | code — Stop-hook advisory nudge (git-diff/log/status check + message text) | **Updated**: `priorities` category now checks the shard directory with a `git status --porcelain` untracked-file fallback (mirrors `deviation-log-guard.sh`'s own #2348 fix); message text now names `priorities/` and `spawn.py priorities-path` |
| `on-the-record/hooks/skill-verdict-guard.sh` | code — end-of-session obligations reminder text | **Updated**: wording only, mentions `spawn.py priorities-path`; no logic change (this hook never reads/writes the file) |
| `docs/issue-1111/proposals/2026-08-13-product-capture-ownership.md` | doc — historical proposal | No-op: historical record of past design discussion, not live code |
| `docs/issue-1111/reports/implementation.md` | doc — historical report | No-op |
| `docs/issue-1111/reports/implementation/survey.md` | doc — historical report | No-op |
| `docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md` | doc — historical proposal | No-op |
| `docs/issue-1117/reports/implementation.md` | doc — historical report | No-op |
| `docs/issue-1117/reports/implementation/deviation-log.md` | doc — historical report | No-op |
| `docs/issue-1117/reports/implementation/survey.md` | doc — historical report | No-op |
| `docs/issue-1118/decisions/generator-choice.md` | doc — historical decision record | No-op |
| `docs/issue-1118/reports/implementation.md` | doc — historical report | No-op |
| `docs/issue-1599/reports/implementation.md` | doc — historical report | No-op |
| `docs/issue-2285/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2315/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2382/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2409/reports/execution-observation/deviation-log/20260826T043804395043-428239a958d68694.md` | doc — historical deviation-log shard | No-op |
| `docs/issue-2414/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2467/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2467/reports/execution-observation.md` | doc — historical report | No-op |
| `docs/issue-2629/reports/conformance-review.md` | doc — historical report | No-op |
| `docs/issue-2631/reports/execution-observation.md` | doc — historical report | No-op |
| `docs/issue-566/proposals/architecture.md` | doc — historical proposal (original design for issue #566) | No-op |
| `docs/issue-566/proposals/implementation.md` | doc — historical report | No-op |
| `docs/issue-566/proposals/product-discovery.md` | doc — historical proposal | No-op |
| `docs/issue-688/reports/implementation/hunt-2026-08-11-delegated-judgment-corpus-path.md` | doc — historical hunt report | No-op |
| `docs/reports/2026-08-11-hunt-generated-path-disjointness.md` | doc — historical hunt report | No-op |

Every historical doc reference above is prose describing a past session's
observations about `priorities.md`; none of them parse or execute against
the file programmatically, so none require updating for this change to be
correct — editing them would falsify a historical record, which
`docs/reports/consult-log.md` staying untouched after #2333 (confirmed
above under "Migration decision") already establishes as the house
convention for this exact situation.

Three secondary sweeps run to rule out any other functional consumer:

```
$ grep -rln "reports/product" --include="*.py" --include="*.sh" --include="*.json" . 2>/dev/null | grep -v .git
priorities.py
spawn.py
on-the-record/hooks/deliverable-guard.sh
on-the-record/hooks/product-capture-stopgate.sh
on-the-record/hooks/delegation-post-gate.sh
on-the-record/hooks/quality-bar-gate.sh
on-the-record/monitors/test_poll_heartbeat.py
on-the-record/hooks/skill-verdict-guard.sh
tests/run-orchestrate-tests.sh
```

canonical: individual `grep -n "reports/product"` on each of the four files below, run this session — literal matching lines reproduced.

The four hits not already accounted for above were individually
inspected — each is a false positive against a DIFFERENT bucket name that
happens to share the `reports/product` substring, not the
requirements/priorities/philosophy/goals category system:

```
on-the-record/hooks/delegation-post-gate.sh:15:# hunt (docs/issue-707/reports/product-discovery/hunt-after-proposal.md)
on-the-record/hooks/quality-bar-gate.sh:233:    "interaction-design": ["docs/issue-*/reports/product-discovery.md"],
on-the-record/monitors/test_poll_heartbeat.py:46:# (docs/issue-922/reports/product-discovery/survey.md).
tests/run-orchestrate-tests.sh:31:guard deny  guard-docs-in-board      docs/issue-3/reports/product.md yes
```

(`product-discovery` and `product.md` — different buckets entirely; no
changes needed.)

## Merge-demo transcript (Step 6 — primary acceptance criterion)

derived: literal shell transcript below, executed this session in three throwaway `git worktree`s off this branch's base commit, then torn down (see Cleanup transcript at the end of this section). No output below is fabricated or predicted — every block is copy-pasted from an actual command run this turn.

Base commit for the whole demo (this branch's HEAD, before any of this
session's own uncommitted changes):

```
$ git rev-parse HEAD
9a1de9bbdcc293d2c47a199985e5a312ca6df274
```

Three throwaway git worktrees created off that commit (isolated from this
session's real uncommitted working tree, so the demo never touches the
real deliverable files):

```
$ git worktree add /tmp/otr-demo-a -b otr-demo-throwaway-a 9a1de9bbdcc293d2c47a199985e5a312ca6df274
Preparing worktree (new branch 'otr-demo-throwaway-a')
HEAD is now at 9a1de9bb issue-2631: execution-observation - independent re-verify of role-name-list removal (#2636)

$ git worktree add /tmp/otr-demo-b -b otr-demo-throwaway-b 9a1de9bbdcc293d2c47a199985e5a312ca6df274
Preparing worktree (new branch 'otr-demo-throwaway-b')
HEAD is now at 9a1de9bb issue-2631: execution-observation - independent re-verify of role-name-list removal (#2636)

$ git worktree add /tmp/otr-demo-integration -b otr-demo-throwaway-integration 9a1de9bbdcc293d2c47a199985e5a312ca6df274
Preparing worktree (new branch 'otr-demo-throwaway-integration')
HEAD is now at 9a1de9bb issue-2631: execution-observation - independent re-verify of role-name-list removal (#2636)
```

Each branch simulates one concurrent session adding its own priorities
entry, deliberately with the file-creation/merge order INVERTED relative
to the filename-timestamp order — branch A's entry has the LATER
timestamp (`120500`) but is merged FIRST; branch B's entry has the
EARLIER timestamp (`090500`) but is merged SECOND. This inversion is what
makes the ordering demo below prove filename-driven order rather than
merge-order. NOTE — both paths below existed ONLY inside the throwaway
worktrees created above; both worktrees (and these paths with them) were
deleted in the Cleanup transcript at the end of this section, so neither
path exists in this repo checkout after this session:

- `otr-demo-a` (untracked/deleted after cleanup): `docs/reports/product/priorities/20260827T120500123456-11111.md`
- `otr-demo-b` (untracked/deleted after cleanup): `docs/reports/product/priorities/20260827T090500123456-22222.md`

```
$ cd /tmp/otr-demo-a && git add docs/reports/product/priorities/20260827T120500123456-11111.md && git commit -m "demo: session A adds its own priorities entry (throwaway)"
$ git log --oneline -1
9c47cec8 demo: session A adds its own priorities entry (throwaway)

$ cd /tmp/otr-demo-b && git add docs/reports/product/priorities/20260827T090500123456-22222.md && git commit -m "demo: session B adds its own priorities entry (throwaway)"
$ git log --oneline -1
5ee57272 demo: session B adds its own priorities entry (throwaway)
```

Real `git merge` commands into the integration branch, in sequence,
literal output:

```
$ cd /tmp/otr-demo-integration
$ git merge --no-ff otr-demo-throwaway-a -m "demo: merge session A"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T120500123456-11111.md | 5 +++++
 1 file changed, 5 insertions(+)
 create mode 100644 docs/reports/product/priorities/20260827T120500123456-11111.md
exit=0

$ git merge --no-ff otr-demo-throwaway-b -m "demo: merge session B"
Merge made by the 'ort' strategy.
 docs/reports/product/priorities/20260827T090500123456-22222.md | 5 +++++
 1 file changed, 5 insertions(+)
 create mode 100644 docs/reports/product/priorities/20260827T090500123456-22222.md
exit=0
```

acceptance: `git merge --no-ff otr-demo-throwaway-a -m "demo: merge session A"` then `git merge --no-ff otr-demo-throwaway-b -m "demo: merge session B"`, both run this session in `/tmp/otr-demo-integration` — result:

```
Merge made by the 'ort' strategy.  (x2, no CONFLICT line either time, exit=0 both times — full transcript immediately above)
```

Zero conflicts on either merge. Working tree confirmed clean after both
merges — `git status --porcelain` produced no output, both entries
present as regular tracked files, no unmerged paths:

```
$ git status --porcelain
$ ls docs/reports/product/priorities/
20260827T090500123456-22222.md
20260827T120500123456-11111.md
```

Reader demonstration — `priorities.py` copied (uncommitted, demo-only,
never committed to any throwaway branch) into the integration worktree
and run against the merged result:

```
$ python3 -c "
import priorities
entries = priorities.read_priorities(None, '.')
print('num entries (legacy block + shards):', len(entries))
for i, e in enumerate(entries):
    print(f'--- entry[{i}] (first 200 chars) ---')
    print(e[:200])
"
num entries (legacy block + shards): 3
--- entry[0] (first 200 chars) ---
# Priorities

Append-only, newest entry last.

- 2026-08-12: #745 is deliberately deprioritized (`infrastructure/no-direct-requirement`)
  behind #1110, the 7-scenario harness re-measurement, and the 
--- entry[1] (first 200 chars) ---
- 2026-08-27T09:05:00Z: [DEMO entry B, branch otr-demo-throwaway-b, merged
  SECOND into the integration branch, filename timestamp is EARLIER than
  entry A's] simulated concurrent product-capture se
--- entry[2] (first 200 chars) ---
- 2026-08-27T12:05:00Z: [DEMO entry A, branch otr-demo-throwaway-a, merged
  FIRST into the integration branch, filename timestamp is LATER than
  entry B's] simulated concurrent product-capture sessi
```

acceptance: `python3 -c "import priorities; ..."` above, run this session in `/tmp/otr-demo-integration` after both merges — result:

```
entries[1] = entry B's content (merged SECOND into git)
entries[2] = entry A's content (merged FIRST into git)
(full transcript with the exact printed text immediately above)
```

The reader's output order is the INVERSE of merge order and matches
filename-timestamp order exactly:

```
$ ls docs/reports/product/priorities/ | sort
20260827T090500123456-22222.md
20260827T120500123456-11111.md
```

(entry B's filename sorts first — matches `entries[1]` before `entries[2]`
exactly, proving `read_priorities()`'s ordering comes from
`sorted(d.glob("*.md"))`, filename sort, never from the order git merged
the two branches.) All 3 entries present, none lost, none reordered
relative to their own filename/timestamp — legacy block first (predates
both, by construction), then B, then A.

### Cleanup transcript

canonical: literal `git worktree`/`git branch` output below, run this session immediately after the reader demonstration above.

Worktrees and throwaway branches removed, back on the working branch,
nothing stray left:

```
$ git worktree remove /tmp/otr-demo-a --force
$ git worktree remove /tmp/otr-demo-b --force
$ git worktree remove /tmp/otr-demo-integration --force
$ git worktree list
/home/jwjung/.../on-the-record-issue-2637-...  9a1de9bb [issue-2637/architecture-interface-contract-shape+silent-failure-audit-a86b8985]

$ git branch -D otr-demo-throwaway-a otr-demo-throwaway-b otr-demo-throwaway-integration
otr-demo-throwaway-a branch deleted (was 9c47cec8).
otr-demo-throwaway-b branch deleted (was 5ee57272).
otr-demo-throwaway-integration branch deleted (was 9cd20dfa).

$ git branch --list "otr-demo-*"
(no output)
```

No branches remain, nothing pushed anywhere, this session's real working
tree was never checked out away from the working branch during the demo
(worktrees are separate checkouts of the same repo, confirmed by `git
worktree list` showing only this session's own working-branch entry
after cleanup, quoted above).

## Consumer-behavior verification (functional, not just static read)

derived: literal hook-invocation transcripts below, executed this session against the real hook scripts in this checkout with synthetic PreToolUse/Stop payloads.

`on-the-record/hooks/deliverable-guard.sh`, run directly with synthetic
PreToolUse payloads (`ORCH_PAYLOAD`), confirms the new shard path is
exempt, the legacy exact path is still exempt, and an unrelated
deliverable path is still denied:

```
$ echo '{"tool_name":"Write","tool_input":{"file_path":"docs/reports/product/priorities/20260827T000000000000-123.md"},"cwd":"'"$PWD"'","session_id":"t1"}' | bash on-the-record/hooks/deliverable-guard.sh; echo "exit: $?"
exit: 0
$ echo '{"tool_name":"Write","tool_input":{"file_path":"docs/reports/product/priorities.md"},"cwd":"'"$PWD"'","session_id":"t2"}' | bash on-the-record/hooks/deliverable-guard.sh; echo "exit: $?"
exit: 0
$ echo '{"tool_name":"Write","tool_input":{"file_path":"src/foo.py"},"cwd":"'"$PWD"'","session_id":"t3"}' | bash on-the-record/hooks/deliverable-guard.sh; echo "exit: $?"
orchestrate: this is an orchestrator session and src/foo.py is a deliverable path in a board repo. ...
exit: 2
```

`on-the-record/hooks/product-capture-stopgate.sh`, run against a synthetic
transcript containing a Korean priority-anchor sentence, in an isolated
throwaway git repo (`TOKENMAXXXER_SPAWNED` unset to reach the orchestrator
code path): nudges when no shard exists yet, goes silent once a shard is
present (via the new `git status --porcelain` fallback for the untracked
new file):

```
$ (no shard yet) ... | bash on-the-record/hooks/product-capture-stopgate.sh
{"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
"product-capture-stopgate: statements matching these categories were not
reflected in docs/reports/product/: priorities/ (spawn.py priorities-path;
e.g. \"...우선순위가 더 중요합니다\"). Record them as structured entries
before ending the turn."}}
RC=0

$ mkdir -p docs/reports/product/priorities && echo "- entry" > docs/reports/product/priorities/20260827T000000000000-1.md
$ (shard now exists) ... | bash on-the-record/hooks/product-capture-stopgate.sh
(no output)
RC=0
```

(Both throwaway git repos used for this specific test were separate `mktemp
-d` temp directories, not this checkout, and were deleted after the test;
neither path above exists anywhere in this repo.)

Both embedded Python heredocs (`deliverable-guard.sh`,
`product-capture-stopgate.sh`) also independently verified with
`python3 -m py_compile` against the extracted heredoc body — both compile
clean, exit 0. `spawn.py` itself imports clean (`python3 -c "import
spawn"`, exit 0) and both new subcommands were run live against this real
checkout:

```
$ python3 spawn.py priorities-path
/home/.../docs/reports/product/priorities/20260827T084956085408-4079287.md
$ python3 spawn.py priorities-log | head -5
# Priorities

Append-only, newest entry last.

- 2026-08-12: #745 is deliberately deprioritized ...
```

canonical: `git status --porcelain docs/` output captured this session immediately after the `rmdir` below, showing only `?? docs/issue-2637/` (matches the diff-stat/status reproduced throughout this record).

The empty directory this smoke-test call created was removed immediately
afterward (`rmdir docs/reports/product/priorities/`) so it is not staged
by this record.

## Open findings

derived: Consumer audit (Step 2) + Merge-demo transcript (Step 6) sections above — every consumer found is either updated or confirmed no-op with a stated reason, and the acceptance criterion ran for real with captured output.

None — no open findings, therefore no resolution path is needed. Every
step-2 consumer is accounted for (updated or confirmed no-op with a
stated reason), the step-3 requirements/philosophy/goals finding is
stated plainly with reproducible commands, the step-4 migration decision
(compatible reader, no history rewrite) is stated with rationale, and the
step-6 merge/read demonstration ran for real with captured output, not
simulated or asserted.

## Next steps

acceptance: `git merge --no-ff` (twice) + `python3 -c "import priorities; ..."`, all reproduced verbatim in the Merge-demo transcript section above — result:

```
Merge made by the 'ort' strategy.  (x2, zero CONFLICT lines, exit=0 both times)
entries[1] = entry B (merged SECOND); entries[2] = entry A (merged FIRST) — filename-sort order, not merge order
(full transcripts immediately above under Merge-demo transcript)
```

Nothing further is queued behind that executed evidence. The only
follow-up is out of scope and explicitly not assumed here: if
`requirements.md`/`philosophy.md`/`goals.md` are ever actually written to
and hit the same collision class, `priorities.py` is the ready template to
mirror — a decision for that future session, not this one.

canonical: `gh pr create` output, this session.

Landed: committed (`58ff8a61`), pushed, and opened as a PR this session —
`loop_state: landed` in the frontmatter reflects this. PR:

```
https://github.com/tokenmaxxxer/on-the-record/pull/2643
```
