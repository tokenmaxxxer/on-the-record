---
code_under_review:
  - on-the-record/hooks/record-tiering-directive.sh
  - on-the-record/hooks/record-tiering-guard.sh
  - on-the-record/hooks/test_record_tiering_directive.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented `docs/issue-745/proposals/product-discovery.md` Item 2
candidate 1 (citation-informed section tiering) per the approved
phase-1 proposal (`docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md`,
approved via the issue-level comment `APPROVE issue-760/implementation`,
single-account mode).

Added a directive+gate pair scoped to exactly one section, the only
one `docs/issue-745/reports/product-discovery/current-state.md`
measured at zero cross-issue citation: `## What did not work` in
`docs/issue-<n>/reports/implementation.md`.

- `on-the-record/hooks/record-tiering-directive.sh` — new
  `UserPromptSubmit` hook, role-session-only (`CLAUDE_ROLE` gate,
  fails open otherwise), `ORCHESTRATE_OFF` kill switch, same
  fail-closed-only-on-genuine-error trap style as
  `record-claim-shape-directive.sh`. Prints a static
  `<record-tiering-directive>` block stating the bare-marker rule and
  the real-content exception (no gates module to generate from — the
  rule lives inline in the paired guard, not in a separate `gates/*.py`
  module).
- `on-the-record/hooks/record-tiering-guard.sh` — new `PreToolUse` hook
  on `Write|Edit|MultiEdit`, scoped to
  `docs/issue-<n>/reports/implementation.md` only. For `Write`, checks
  the write's `content` directly. For `Edit`/`MultiEdit`, reads the
  target file's current on-disk content and applies the same edit(s) a
  real Edit/MultiEdit call would apply, then checks the reconstructed
  full content (falls back to the changed fragment only when the file
  can't be read). Extracts the `## What did not work` section body; if
  the trimmed body starts with "none" (case-insensitive) and is not
  itself the bare marker (`None.`/`None`, optional trailing
  whitespace, nothing else), denies (exit 2). A body not starting with
  "none" is never inspected further, and content with no section
  heading at all is a no-op — this is a content-shape rule on the
  self-declared-empty branch only, never a length threshold on content
  in general. Fails closed on genuine error, `ORCHESTRATE_OFF` kill
  switch.
- `on-the-record/hooks/test_record_tiering_directive.py` — tests
  covering both hooks: guard denies a padded "None — ..." body, allows
  a bare `None.` body, allows a bare `None` (no period) body, never
  denies real content of any length, ignores non-matching paths
  (non-`docs/issue-*/reports/` and non-`implementation.md` report
  files), ignores content without the section heading, works through
  the `Edit` tool's `new_string`, tolerates a malformed payload without
  denying, denies a heading-then-body split across two separate `Edit`
  calls (regression test for the before-landing hunt finding below),
  and falls back to fragment-only checking when the target file can't
  be read; directive states the bare-marker rule and the "real entry"
  exception, is silent without `CLAUDE_ROLE`, and fails open when
  `ORCHESTRATE_OFF=1`. Full count: see `## Test baseline` below.
- `on-the-record/hooks/hooks.json` — registered
  `record-tiering-directive.sh` under `UserPromptSubmit` (after
  `record-claim-shape-directive.sh`) and `record-tiering-guard.sh`
  under the existing `PreToolUse`/`Write|Edit|MultiEdit` matcher block
  (after `record-claim-guard.sh`).
- `docs/specs/enforcement-boundary.md` — new rows for both hooks,
  verdict `contract`, inserted after the `record-claim-guard.sh` row.
- `docs/specs/generated-paths.md` — new rows for both hooks, `n/a`,
  "reads/validates only, no write call", inserted between
  `record-claim-shape-directive.sh` and `report-framing-check.sh`.
- Ran `python3 gates/spec_index.py --update` after editing
  `docs/specs/*` (required by `spec-index-preflight.sh` whenever a
  `docs/specs/*` file changes). Neither edited file is in
  docs/specs/reconciled-index.md's tracked-document table — `derived:
  grep -n "enforcement-boundary\|generated-paths"
  docs/specs/reconciled-index.md` returns no rows — so the regen
  produced no diff; docs/specs/reconciled-index.md is unchanged in
  this commit.

Both new hook files are executable (`chmod +x`), required because
`hooks.json` invokes them by raw path.

## Why

The pre-registered metric package
(`boilerplate_output_token_share`/30%/`cross_issue_citation_rate`
5-point guardrail/per-category independent revert) is copied verbatim
from the issue body — unchanged, see "Pre-registered package" below.
The phase-1 proposal's own after-proposal hunt finding (see the
`## after-proposal — stance 0` section of the hunt record referenced
under `## Hunt` below) found that a directive-only design duplicates
an already-existing, already-silently-ignored directive for this exact
section, so the proposal was revised to pair the directive with a
narrowly scoped mechanical gate instead of directive-only — that gate
is what this delivery implements.

## Upstream

Based on: docs/issue-760/proposals/2026-08-11-citation-informed-section-tiering.md

## Pre-registered package (copied verbatim from the issue body, unchanged)

- 주 지표: `boilerplate_output_token_share` — 이름붙은 저인용 절 집합에 쓴
  출력 토큰 ÷ 기록 전체 출력 토큰, 등급화 형식으로 쓰인 다음 20개 기록에
  대해 측정.
- 임계값: 등급화 이전 기준선(같은 측정, 같은 절 집합, 직전 20개 기록) 대비
  30% 이상 감소.
- 가드레일: `cross_issue_citation_rate` — 고인용 카테고리
  (`proposals/*.md`, `reports/<role>.md`, `docs/reports/*.md`)의
  인용률이 current-state.md 가 세운 각 카테고리 기준선보다 5%p 넘게
  떨어지지 않아야 하며, 주 지표 값 옆에 명시적으로 함께 적는다.
- 결정 규칙: 주 지표가 임계 이상이고 모든 카테고리 가드레일이 허용 범위
  안 → 유지. 토큰 감소가 부족 → 저인용 절 집합을 좁게 그린 것이므로 다음
  측정 라운드의 인용률로 넓혀서 재시도(가드레일을 느슨하게 하지 않는다).
  어떤 카테고리든 가드레일 위반 → 그 카테고리의 등급화만 즉시 되돌린다.

Section set in scope for this delivery: `## What did not work` in
`docs/issue-<n>/reports/implementation.md` only (the sole zero-citation
section `current-state.md` actually measured — see the phase-1
proposal's Rationale and survey for the evidence trail).

## What did not work

- First cut of the guard's deny message read "Issue #760: ..."
  (capitalized). The two tests asserting a lowercase `"issue #760" in
  r.stderr` (matching this plugin's existing convention, e.g.
  `record-claim-guard.sh`'s "issue #310"/"issue #333" messages) both
  failed on the capitalization mismatch. Fixed by rewording the deny
  message to end with "...but is not the bare marker (issue #760)." —
  reran the affected tests directly and both passed.
- Before-landing hunt (see `## Hunt` below) found the guard's
  fragment-only content check — inspecting only each `Write`/`Edit`
  call's own `content`/`new_string`, never the file's actual resulting
  state — could be bypassed by splitting the section heading and the
  padded "None..." body across two separate `Edit` calls; each call's
  own fragment never contained both together, so both exited 0 even
  though the combined on-disk result was exactly the shape the guard
  exists to catch. Fixed by having the guard read the target file's
  current on-disk content for `Edit`/`MultiEdit` and apply the same
  edit(s) before checking, instead of checking the changed fragment
  alone; see `## Hunt` below for the full finding and resolution.

## Baseline measurement (pre-tiering, this delivery's window)

`boilerplate_output_token_share`, char-length proxy method (same
git-log-proxy method the phase-1 survey used — see
docs/issue-760/reports/implementation/survey.md's own caveat on
divergence from `current-state.md`'s ledger-log method), over the same
20 most-recently-touched `docs/issue-<n>/reports/<role>.md` files still
on disk:

```
$ python3 - <<'PY'
import re
from pathlib import Path
files = [
"docs/issue-742/reports/implementation.md",
"docs/issue-759/reports/implementation.md",
"docs/issue-743/reports/implementation.md",
"docs/issue-749/reports/conformance-review.md",
"docs/issue-741/reports/implementation.md",
"docs/issue-729/reports/implementation.md",
"docs/issue-731/reports/implementation.md",
"docs/issue-730/reports/implementation.md",
"docs/issue-732/reports/implementation.md",
"docs/issue-726/reports/conformance-review.md",
"docs/issue-719/reports/implementation.md",
"docs/issue-659/reports/execution-observation.md",
"docs/issue-674/reports/implementation.md",
"docs/issue-706/reports/implementation.md",
"docs/issue-711/reports/implementation.md",
"docs/issue-659/reports/implementation.md",
"docs/issue-699/reports/implementation.md",
"docs/issue-698/reports/implementation.md",
"docs/issue-695/reports/implementation.md",
"docs/issue-692/reports/implementation.md",
]
SECTION_RE = re.compile(r"(?m)^## What did not work\s*\n(.*?)(?=\n## |\Z)", re.S)
total_chars_all = 0
empty_section_chars_all = 0
n_empty = n_real = n_missing = 0
for f in files:
    p = Path(f)
    if not p.exists():
        n_missing += 1
        continue
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    total_chars_all += len(text)
    m = SECTION_RE.search(text)
    if not m:
        n_missing += 1; continue
    body = m.group(1).strip()
    if re.match(r"(?i)^none\b", body) or not body:
        n_empty += 1; empty_section_chars_all += len(m.group(0))
    else:
        n_real += 1
print(n_empty, n_real, n_missing, total_chars_all, empty_section_chars_all)
print(empty_section_chars_all / total_chars_all * 100)
PY
9 8 3 159159 522
0.3279739128795733
```

Pre-tiering baseline: `boilerplate_output_token_share` ≈ 0.328% over
this 20-record window (this is the same figure and method the phase-1
survey already established — reproduced fresh above, unchanged, since
none of the 20 files changed between survey and delivery). This is the
placeholder baseline; the official post-tiering comparison should
re-derive both windows with `current-state.md`'s own ledger-log method
(Write-call content from session logs, `/4` divisor) for methodological
consistency, per the survey's own caveat.

`cross_issue_citation_rate` guardrail baselines (from `current-state.md`
§2, unchanged, copied for reference — `derived: grep -n
"93.8\|64.1\|65.8" docs/issue-745/reports/product-discovery/current-state.md`):
`proposals/*.md` 93.8%, `reports/<role>.md` 64.1%, repo-wide
`docs/reports/*.md` 65.8%. Tolerance: 5 percentage points per category,
independently revertible.

## Next steps

Per the issue's own Acceptance empty-state clause: fewer than 20
post-tiering `docs/issue-<n>/reports/implementation.md` records exist
yet (the tiering ships in this same commit), so the measurement window
is held open — recording the baseline above and stopping here, not
forcing a verdict early.

Owner/trigger for the official re-measurement: the next
`product-discovery`-role session that revisits `#745`'s tracked items,
or any session opening a follow-up issue against `#760`, re-derives
`boilerplate_output_token_share` with `current-state.md`'s own
ledger-log method once 20 `docs/issue-<n>/reports/implementation.md`
records exist with a commit date after this commit lands. At that
point: compare against the baseline above, check each
`cross_issue_citation_rate` category against its `current-state.md`
baseline with 5-point tolerance, keep tiering if the primary metric
clears 30% and all guardrails hold, widen the low-citation section set
if the primary metric falls short, revert only the offending category
if a guardrail breaks.

## Test baseline

`derived: python3 -m pytest -q on-the-record/hooks/test_record_tiering_directive.py`:

```
..............                                                           [100%]
14 passed in 0.43s
```

`derived: python3 -m pytest -q` (full suite, this branch's working
tree, uncommitted):

```
........................................................................ [ 44%]
........................................................................ [ 50%]
.............F.......................................................... [ 56%]
........................................................................ [ 62%]
........................................................................ [ 69%]
........................................................................ [ 76%]
........................................................................ [ 82%]
........................................................................ [ 88%]
...............................................................s..s..... [ 95%]
.....................................................                    [100%]
1132 passed, 1 failed, 2 skipped in 152.10s (0:02:32)
```

The one failure, tests/test_gates.py `t_rulebook_version_is_recorded`,
is pre-existing and unrelated to this delivery: `derived: git stash &&
python3 -m pytest -q tests/test_gates.py::t_rulebook_version_is_recorded;
git stash pop` reproduces the identical failure on the committed HEAD
state (no working-tree changes from this session applied) — the test
asserts the checked-out rulebook plugin directory carries no
uncommitted changes (`'커밋안됨' not in v`), which is a property of this
session's own local rulebook checkout, not of any file this delivery
touches. No new failures: 0 regressions introduced by this delivery's
changes, 1 pre-existing unrelated failure confirmed present before this
session's changes were applied (and the count grew from 1130 to 1132
passed between the two full-suite runs above only because the
guard-bypass fix's two new regression tests were added in between).

## Hunt

Before-landing hunt (`warrant-hunter`, stance 0, cap 180s — diff is 299
lines across 6 files, `derived: git diff --stat` — over the 200-line
size threshold) dispatched against this same diff. Full record in
docs/issue-760/reports/implementation/hunt-2026-08-11-citation-informed-section-tiering.md,
`## before-landing — stance 0` section (appended below the phase-1
`## after-proposal — stance 0` section already there).

Finding: a fragment-only content check let an author bypass the guard
by splitting the section heading and a padded "None..." body across
two separate `Edit` calls — each call's own fragment never contained
both, so both exited 0 even though the combined on-disk result was
exactly the shape the guard exists to deny. Resolved in this same
commit: the guard now reads the target file's current on-disk content
for `Edit`/`MultiEdit` and applies the edit(s) before checking, instead
of checking the changed fragment alone (falls back to fragment-only
only when the file can't be read). Reproduced via a new regression
test — see `## Test baseline` above and the hunt record's own
`### Resolution` for the reproduction.

closed_checks:
- check: before-landing hunt stance 0 (bypass-of-the-mechanism-just-implemented)
  code_sha: same as code_under_review above (working-tree files, no
  commit sha assigned to this pre-commit transition)
  finding: fragment-only check bypassable via a two-call Edit split
  (see hunt record's `## before-landing — stance 0` for the full
  reproduction).
  resolution: guard reconstructs full content for Edit/MultiEdit before
  checking; regression test added and passing (see `## Test baseline`).

resolved_findings:
- finding: before-landing hunt stance 0 — heading/body split across two
  Edit calls bypassed record-tiering-guard.sh.
  resolution: on-the-record/hooks/record-tiering-guard.sh now reads and
  reconstructs the target file's full content for Edit/MultiEdit before
  checking the section body, closing the split-call bypass; verified by
  test_record_tiering_directive.py::t_split_edit_heading_then_padded_body_is_still_denied
  (see `## Test baseline` above, 14 passed).

## Doc placement (ladder outcomes)

- [x] No new env var, config key, dependency, or migration/setup step
  introduced — no handbook entry needed.
- [x] No changed public signature/wire format, and no new
  library-or-format-over-alternative decision made during this
  delivery (all three alternatives — directive-only, template
  scaffold, length-based gate — were already decided and recorded in
  the phase-1 proposal's own `## Rationale`, unchanged here) — no new
  decisions file needed under this issue's tree.
- [x] Benchmark/investigation numbers (pre-tiering baseline, test
  counts) recorded in this report.

## Acceptance verification

- 등급화된 형식이 실제로 저인용 절의 분량을 줄인다 — checked: 20-record
  post-tiering window — result: unverifiable, reason: fewer than 20
  post-tiering records exist yet (tiering ships in this same commit);
  pre-tiering baseline (≈0.328%) recorded above per the issue's own
  empty-state clause, window held open, re-measurement owner/trigger
  named in `## Next steps`.
- 고인용 카테고리의 인용률이 기준선 대비 5%p 넘게 떨어지지 않는다 —
  checked: `cross_issue_citation_rate` per category — result:
  unverifiable, reason: no new post-tiering records exist yet to
  re-measure against; baselines only (93.8% / 64.1% / 65.8%) recorded
  above per the issue's own empty-state clause.
- Mechanism-level: the guard denies a padded self-declared-empty body
  and never denies real content, including across a split Edit — checked:
  test_record_tiering_directive.py (all cases) — result: pass, derived:
  `python3 -m pytest -q on-the-record/hooks/test_record_tiering_directive.py`
  (see `## Test baseline` above).

## Open findings

None outstanding — the one before-landing hunt finding is resolved in
this same commit and closed above.
