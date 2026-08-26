---
issue: 2409
role: conformance-review
author: conformance-review
loop_state: reported
code_under_review:
  - directive_assembly.py
  - spawn.py
  - scripts/related_files.py
  - scripts/session_waste_metrics.py
  - tests/test_directive_diet_2135.py
  - tests/test_spawn_directive_assembly.py
  - tests/test_related_files.py  # untracked on this branch; lives on origin/issue-2409/implementation
  - tests/test_session_waste_metrics.py  # untracked on this branch; lives on origin/issue-2409/implementation
  - docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json  # untracked on this branch; lives on origin/issue-2409/implementation, added at 980d6db9
type: review
breaking: none — read-only review, no code or record edited outside this file
verdict: Incorrect
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26), sub-clause NR1b — see "CHANGES-round re-review" section below for the full basis
evidence: see "CHANGES-round re-review" section below and requirement block NR1b's updated verdict
upstream:
  - path: docs/issue-2409/reports/implementation.md  # untracked on this branch; lives on origin/issue-2409/implementation
    sha: 1b09aca4ba812f7b4fefc5de40cfd255189f210c
  - path: docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json  # untracked on this branch; lives on origin/issue-2409/implementation, added at 980d6db9
    sha: 980d6db9ad853fc17ce23805413ed3f991945a0c
  - path: docs/issue-2409/reports/conformance-review.md
    sha: 8121072e4efd9ab92d54f844bed39005a03d5346  # this role's own prior-round record, same branch — superseded by this revision, not deleted (git history retains it)
subject: commit 1b09aca4ba812f7b4fefc5de40cfd255189f210c (origin/issue-2409/implementation, PR #2416 tip) — see "CHANGES-round re-review" section below for the full basis
test: see "CHANGES-round re-review" section below for the full list of independent commands rerun
result: failed
assertedBy: conformance-review
---

# issue-2409 — conformance-review record

Note: `docs/issue-2409/reports/implementation.md` (untracked here) lives
only on `origin/issue-2409/implementation`, not on this role's own
branch (`issue-2409/conformance-review`). Every citation to it below is
pinned to the sha this session read it at (`git show <sha>:<path>`, run
against a worktree built from that branch this session).

## Revision note

This record supersedes this same role's prior-round verdict on this
branch (commit `1bfc914d`).
derived: `git show 1bfc914d:docs/issue-2409/reports/conformance-review.md`
(run live this session) — result: frontmatter `result: failed`; Open
findings' own set-size check reads "9 + 7 + 1 = 17" (below-clause +
satisfied + partial) against the then-current 17-requirement Acceptance
text, i.e. 9/17 = 52.9% below-clause — run live this session, read
directly.
On 2026-08-26 the operator amended issue #2409's `## Acceptance` section
(narrowed from a corpus-scale 5x proof to "design + small-scale
verification, honestly bounded" — see the issue's own "Scope amendment,
2026-08-26" paragraph). This session re-derives verdicts against the
CURRENT (amended) issue body, per this round's own instruction, rather
than reusing the prior round's now-superseded requirement set. The prior
record is not deleted — it remains in git history at `1bfc914d` and is
cited above as this role's own upstream basis — per the finding-record
skill's "never fix or patch what was found" and this round's own "no
verification, record, or observer step removed" obligation (checked
fresh as NR6 below, not merely assumed from the prior round).

canonical: `gh issue view 2409` (run live this session) — result: the
`## Acceptance` section now reads six `check:` bullets each carrying a
`must not:` clause, plus a "Scope amendment, 2026-08-26" paragraph
naming PR #2420's prior `failed` verdict as the reason for the
narrowing — run live this session, spec version pinned to this text
(no other Acceptance version exists on the issue at review time).

## CHANGES-round re-review

Since this role's prior round (`8121072e`), `origin/issue-2409/implementation`
gained two new commits: `980d6db9` ("commit generated per-turn-breakdown
artifact (NR1b fix)") and `1b09aca4` ("skill-verdict addendum for CHANGES
round").

canonical: `git fetch origin issue-2409/implementation` then `git log
origin/issue-2409/implementation -1 --oneline` (run live this session) —
result: tip `1b09aca4`, two commits ahead of the previously-reviewed
`64028704`.
canonical: `git diff 64028704 origin/issue-2409/implementation --stat`
(run live this session) — result: 2 files changed, 118 insertions(+):
`docs/issue-2409/reports/implementation.md` (untracked here; lives on
origin/issue-2409/implementation) (+22) and a new file,
`docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
(untracked here; lives on origin/issue-2409/implementation, added at
`980d6db9`) (+96). No code file (`directive_assembly.py`, `spawn.py`,
`scripts/related_files.py`, `scripts/session_waste_metrics.py`) changed.
canonical: `git diff 64028704 origin/issue-2409/implementation --stat --
'roles/specs/*.json' 'pipeline.py' '*consult*'` and `git status --short
on-the-record/hooks/` (both run live this session, against a fresh
worktree at the new tip) — both empty — re-confirms NR3-mustnot/NR6a/NR6b
still hold; those 15 sub-clauses' verdicts are carried forward unchanged
from `8121072e` per verdict-assignment rule 4 (their evidence is
untouched by this diff).

The fix commit's own claim (`docs/issue-2409/reports/implementation.md`,
untracked here, at `980d6db9`, quoted in full under NR1b's evidence
below): a real JSON artifact was committed and its content was
independently diff-checked byte-for-byte against a fresh regeneration.

canonical: independently reran the equivalent regeneration this session
(script content matching `docs/issue-2409/reports/implementation.md`'s
own documented `canonical:` command verbatim, untracked here, run
against a worktree built from `origin/issue-2409/implementation`) then
diffed the output against
`docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
(untracked here) — result: empty diff (exit 0) — the committed artifact
is confirmed byte-for-byte reproducible, corroborating that specific
claim.

However, independently reading `scripts/session_waste_metrics.py`
(`sed -n '135,225p'`, run live this session) shows the codebase itself
distinguishes two different shapes: `per_turn_breakdown(events)` (used
by `analyze()`, which is what `--md`'s single-session per-turn table is
built from — "One row per tool_use, in stream order" per its own
docstring) versus `batch_summary(paths)` (used by `--batch`, which
"One `analyze()` per path, plus a corpus-level rollup" per its own
docstring, and whose `per_session` list comprehension at
`scripts/session_waste_metrics.py:216-222` explicitly does not carry the
`per_turn` key forward — only `session_log`, `wall_clock_ms`,
`num_turns`, `bash_total`, `bash_other_share`, `hook_refusals`,
`named_offenders`).

canonical: `grep -c "per_turn"
docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
(untracked here, run live this session against the new-tip worktree) —
result: `0` — the committed artifact contains no per-turn rows anywhere.
canonical: `grep -oE '"[a-z_]+":'
docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json
| sort -u` (untracked here, run live this session) — result: thirteen
keys, all session-level or corpus-level aggregates (`bash_total`,
`hook_refusals_total`, `named_offenders_total`, `per_session`,
`sessions`, etc.) — none named `turn` or `tool` or `per_turn`.
canonical: `grep -rln "| turn | tool" docs/issue-2409/reports/`
(run live this session, against the same worktree) — result: no match
anywhere under the reviewed tree — no per-turn markdown table (the
`_fmt_md()`/`--md` output shape NR1a's own evidence names) is committed
either.

This means the fix commit published a session-level/corpus-level
**rollup** (`batch_summary()`'s shape), not a **per-turn breakdown**
(`per_turn_breakdown()`'s shape) — the two are distinct outputs the
script's own code already separates, and the amended check 1's literal
text asks specifically for "a per-turn breakdown for a role session
(what each turn's tool call was for)", not a cross-session aggregate.
See the updated NR1b verdict below for the resulting Incorrect
assignment (raised from Absent, per verdict-assignment rule 2: an
artifact was actively produced and the record's own prose claims it
"addresses ... NR1b", but what was produced is not the artifact type the
clause names — a present-but-wrong deliverable, not an omission).

## What was done

A per-requirement conformance verdict (Present|Surface|Absent|Incorrect)
against issue #2409's amended `## Acceptance` text (six `check:`
bullets, each split into its testable sub-clauses per the
requirement-extraction skill's rule 1), for commit `02aba0a9`
(origin/issue-2409/implementation, PR #2416) — re-derived independently
this session, not carried over unread from the prior round's record.

canonical: `git worktree add /tmp/wt-2409-impl2 origin/issue-2409/implementation`
(run live this session) — result: checked out at tip `64028704`.
canonical: `git diff 02aba0a9 64028704 --stat` (run live this session,
against that worktree) — result: one file changed,
`64028704:docs/issue-2409/reports/consult-log/20260825T121835309474-132427.md`
(untracked here), 4 insertions — confirms nothing under review changed
between the reviewed sha and the branch tip, matching the prior round's
own finding (1bfc914d), re-confirmed live rather than assumed.

canonical: `env -u CORE_BUILD_NOW python3 -m pytest
tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py
tests/test_related_files.py tests/test_session_waste_metrics.py -q -m ""
-p xdist -n0` (run live this session, against the worktree) — result:
`79 passed, 1 skipped in 2.81s` — same pass/skip counts as this role's
own prior-round rerun (1bfc914d) and the implementation record's own
pasted line; wall time differs, expected across separate runs.

canonical: `git diff origin/main...origin/issue-2409/implementation
--stat -- 'roles/specs/*.json' 'pipeline.py' '*consult*'` (run live this
session) — result: empty except the one `consult-log/` entry (an
issue-scoped record path, not a role-spec/pipeline/consult-mechanism
file) — re-confirms NR6 below.

canonical: `git diff origin/main...origin/issue-2409/implementation
--numstat -- spawn.py directive_assembly.py` (run live this session) —
result: `2 0 spawn.py`, `72 6 directive_assembly.py` — net-additive,
matching the prior round's own numbers, re-derived rather than cited.

canonical: `git status --short on-the-record/hooks/` (run live this
session, against the worktree) — result: empty — no gate script
touched.

canonical: `grep -n "| turn | tool"
02aba0a9:docs/issue-2409/reports/implementation.md` (untracked here,
run live this session) — result: no match — no committed instance of a
per-turn-breakdown table exists in the record (see NR1 below).

canonical: `git diff origin/main...origin/issue-2409/implementation
--name-status -- 'docs/issue-2409/*'` (run live this session) — result:
three added files (`consult-log/...md`, `reports/implementation.md`,
`implementation/deviation-log/...md`) — no generated
session-waste-metrics output file among them, re-confirming the above.

## Why

derived: `gh issue view 2409` (`## Acceptance`, six `check:` bullets
plus their `must not:` clauses, amended 2026-08-26), split into NR1-NR6
sub-clauses in this record's "Requirement verdicts" section below, per
the requirement-extraction skill's rule 1 (split bundled obligations)
and rule 6 (dimension-tag). This round's own instruction ("Re-derive
verdicts against the CURRENT issue body, not the prior round's
requirement set") and the finding-record skill's rule against builder
self-report as sole evidence both require independent re-derivation —
every claim cited above and below was run live this session against the
real repo, not copied from the implementation record or from this
role's own prior-round record.

## What did not work

None of this session's independent reruns failed: the worktree build,
the pytest rerun, the `related_files.py` rerun (cited under NR2 below),
and every diff/grep/status check succeeded on the first attempt.
canonical: this session's own commands pasted above and below, all
reporting non-error results.

## Upstream basis

`git show 02aba0a9:docs/issue-2409/reports/implementation.md` (untracked
here) — the delivery under review; every number and claim in it cited
below was independently re-run this session rather than taken at face
value.

This role's own prior-round record (`1bfc914d`, this branch) — the
R1-R18 verdict set against the pre-amendment Acceptance text. Where a
new sub-clause below traces to unchanged evidence already independently
verified there, this record re-confirms it live rather than silently
citing the old verdict, per verdict-assignment rule 6 (re-check before
finalizing an Absent) — but does carry forward the underlying fact
(e.g., "gate scripts untouched") per rule 4 where the diff since
`1bfc914d` genuinely does not touch that evidence.

`gh issue view 2409` (read live this session) — the amended spec text.

## Requirement verdicts

Verification method per requirement is Inspection for structural
properties (constant/function existence, file diffs), Demonstration for
the two live-fire mechanism checks, and Test (reusing the existing
79-passed suite per verification-method-selection rule 4) — assigned
per requirement below, per the verification-method-selection skill.

---
requirement: NR1a — the record states how to regenerate the per-turn
  breakdown artifact (an actual command)
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 1,
  clause "the ... how to regenerate it are in the record"
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here), "Acceptance evidence (executed)" section: `python3
  scripts/session_waste_metrics.py <session_log> [--md]` and `python3
  scripts/session_waste_metrics.py --batch '<glob>'`.
canonical: both commands independently rerun this session against real
  paths — result: both produce output in the documented shape (a
  per-turn `| turn | tool | detail |` table for `--md`, a
  `batch_summary()` dict for `--batch`) — run live this session.
rationale: the literal clause (a stated, working regenerate command) is
  satisfied.
---
requirement: NR1b — the per-turn breakdown artifact itself is published
  (reachable as an actual output "in the record", not only as
  unexercised script capability), so the waste classes "can be tracked
  over time rather than re-derived by hand"
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 1,
  clauses "publish a per-turn breakdown" and "the artifact ... [is] in
  the record"
verdict: Incorrect
evidence: commit `980d6db9` (on
  `origin/issue-2409/implementation`) committed
  `docs/issue-2409/reports/implementation/artifacts/session-waste-batch-rollup-2314-2331-2348-2382-2393.json`
  (untracked here) and its own `implementation.md` prose (untracked
  here) explicitly claims "This addresses conformance-review PR #2420's
  NR1b finding." Independently confirmed this session (see
  "CHANGES-round re-review" above) that the committed file is a
  `batch_summary()`-shaped session/corpus rollup (13 aggregate keys, 0
  occurrences of `per_turn`), not a `per_turn_breakdown()`-shaped
  per-turn table — `grep -c "per_turn"` on the committed file returns
  `0`, and `grep -rln "| turn | tool" docs/issue-2409/reports/` (the
  `_fmt_md()` table header NR1a's own evidence names) matches nothing
  anywhere in the reviewed tree.
spec_vs_built: spec asks for "a per-turn breakdown for a role session
  (what each turn's tool call was for)" — a turn-by-turn table, one row
  per tool_use event, per `per_turn_breakdown()`'s own docstring ("One
  row per tool_use, in stream order"). What was built and committed is
  a per-session/cross-session aggregate rollup (`batch_summary()`'s
  shape: `bash_total`, `hook_refusals_total`, `named_offenders_total`,
  a `per_session` list of session-level counts) — the same script
  already implements both shapes as distinct functions, and the
  `per_session` comprehension at `scripts/session_waste_metrics.py:216-222`
  explicitly drops the `per_turn` key `analyze()` produces. The
  committed artifact is real and byte-for-byte reproducible (confirmed
  this session), but it is not the artifact type the clause names.
canonical: see the four `canonical:` citations under "CHANGES-round
  re-review" above (grep for `per_turn`, key enumeration, `| turn |
  tool` search, and the independent byte-for-byte regeneration diff) —
  re-checked live this session per verdict-assignment rule 6 before
  raising the verdict from Absent to Incorrect.
rationale: NR1a (the capability and its command) remains satisfied. This
  sub-clause is raised from Absent to Incorrect, not left Absent,
  because a concrete artifact now exists and is affirmatively presented
  in the record as resolving this exact finding — that is a
  present-but-wrong deliverable (the wrong one of the script's own two
  output shapes), not an omission, per verdict-assignment rule 2. A
  future reader consulting the committed artifact for "what each turn's
  tool call was for" would find no such data — only session-level
  counts — so the underlying gap this finding originally named
  (nothing a reader can consult without running the per-turn tool
  themselves) is unresolved despite the new commit.
---
requirement: NR2a — a stated mechanism exists intended to reduce the
  exploratory-Bash class
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 2
verdict: Present
evidence: `02aba0a9:scripts/related_files.py` plus
  `_TASK_LOOKUP_PROSE`/`task-lookup.md` in
  `02aba0a9:directive_assembly.py:187-205`.
canonical: `python3 scripts/related_files.py 2409` (run live this
  session, against the worktree) — result: `docs/issue-2409/` (3 files)
  plus issue-mentioning files outside that tree, matching the `git diff
  --stat` file list with no extra or missing entries — run live this
  session.
rationale: mechanism exists, is documented, and independently produces
  the correct one-call lookup this session.
---
requirement: NR2b — a single live demonstration that the mechanism works
  as designed is given
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 2
  ("a single live demonstration that the mechanism works as designed is
  sufficient")
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here), "Measured, live, this session (exploratory-Bash
  mechanism)" bullet: `related_files.py` run live for 5 real issue
  numbers, returning each issue's docs tree plus issue-mentioning files
  in exactly one call each.
canonical: the same `related_files.py` rerun cited under NR2a,
  independently reproduced this session — result: matches the record's
  own per-issue counts for issue 2409 (one call, correct file set) — run
  live this session.
rationale: a genuine live demonstration exists and independently
  reproduces.
---
requirement: NR2c — the record states plainly that this is design-level
  evidence, not a measured session-level improvement
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 2
  ("state plainly that this is design-level evidence, not a measured
  session-level improvement")
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here): "This proves the lookup functions correctly against
  real data; it does not by itself prove a full re-run session would
  only make 1 call instead of the ~21-per-session lookup-shaped calls
  made historically (a session might still make follow-up greps the
  lookup's output doesn't answer)."
canonical: `grep -n "does not by itself prove"
  02aba0a9:docs/issue-2409/reports/implementation.md` (run live this
  session) — result: one match, the sentence quoted above — read
  directly, run live this session.
rationale: this sentence states the substance the clause requires
  (functional proof, not a proven session-level reduction) in plain
  terms, even though it does not use the literal words "design-level
  evidence" — the requirement asks for the substance to be stated
  plainly, not for exact phrase matching, and the substance is present.
---
requirement: NR2-mustnot — the new lookup mechanism must not itself
  become a new required round-trip (N greps -> lookup + still-needed
  greps = N+1 calls) without disclosing that in the record
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 2
  `must not:` clause
verdict: Present
evidence: the same sentence cited under NR2c explicitly discloses that
  "a session might still make follow-up greps the lookup's output
  doesn't answer" — the exact N+1 risk the clause names.
rationale: the `must not` is a disclosure obligation, not a prohibition
  on the risk existing at all; the risk is disclosed, satisfying the
  clause.
---
requirement: NR3a — a mechanism surfaces likely hook refusals as an
  up-front contract rather than one-at-a-time rejections
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 3
verdict: Present
evidence: `02aba0a9:directive_assembly.py:206-232`, `_HOOK_CONTRACT_PROSE`
  — six numbered rules, each traced this session to a real gate
  (heredoc-command-refusal-gate.sh, record-claim-guard.sh,
  acceptance-command-real-run-guard.sh/live-fire-claim-real-run-guard.sh,
  spec-index-preflight.sh, gate-registration-guard.sh,
  approval-gate.sh/pr-preflight.sh via CORE_BUILD_NOW); registered
  always-on by `directive_section_files()`
  (`02aba0a9:directive_assembly.py:349`).
canonical: `sed -n '206,232p' directive_assembly.py` (run this session,
  against the worktree) — result: exactly 6 numbered rules — run live
  this session, read directly.
rationale: mechanism exists, is always-delivered, and its six rules were
  independently checked against the real gate list this session.
---
requirement: NR3b — a single live demonstration that a session carrying
  the new contract avoids at least one refusal shape it would otherwise
  have hit is given
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 3
  ("a single live demonstration that a session carrying the new
  contract avoids at least one refusal shape it would otherwise have
  hit is sufficient")
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here), "Measured, live, this session (hook-refusal
  mechanism)" bullet — a real nested `claude -p` role session (scratch
  repo `/tmp/otr-2409-livefire`) produced its first commit as
  `git commit -m "..." -m "..."` (two `-m` flags) with zero `is_error`
  tool_results, avoiding the exact heredoc-shaped-first-attempt failure
  that 3 of the 5 sampled real sessions hit.
canonical: `grep -n "by_gate" -A2
  02aba0a9:docs/issue-2409/reports/implementation.md` (run live this
  session) — result: the per-session gate breakdown lines (2314, 2331,
  2348 each list `heredoc=` counts >0) — 3/5 sessions hit the heredoc
  shape — run live this session, read directly.
rationale: a genuine single live demonstration exists, names the
  specific refusal shape avoided, and traces it to real before-data from
  the same 5-issue sample.
---
requirement: NR3-mustnot — the up-front contract must not weaken or
  bypass any existing gate's actual refusal logic; it may only inform
  earlier, never suppress a refusal that should still fire
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 3
  `must not:` clause
verdict: Present
evidence: no gate script is modified by this delivery.
canonical: `git status --short on-the-record/hooks/` (run live this
  session, against the worktree) — result: empty — re-confirmed live
  this session (see "What was done" above).
canonical: `git diff origin/main...origin/issue-2409/implementation
  --numstat -- spawn.py directive_assembly.py` (run live this session)
  — result: `2 0 spawn.py`, `72 6 directive_assembly.py` — net-additive
  within existing `_*_PROSE` constant bodies plus one new constant; no
  existing constant or gate reference removed.
rationale: independently confirmed this session that no gate's
  behavior changed — `hook-contract.md` only states existing rules
  earlier, per its own docstring and the diff shape.
---
requirement: NR4a — the mechanism and rationale for reducing redundant
  same-file re-reads within a session are stated in the record
  (prose/directive change; live measurement of an actual reduction is
  explicitly not required by this narrowed scope)
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 4
verdict: Present
evidence: `02aba0a9:directive_assembly.py:153-176`, `_TURN_BUDGET_PROSE`
  — gained a third numbered item (spawn.py/own-record re-read guidance).
canonical: `sed -n '153,176p' directive_assembly.py` (run this session,
  against the worktree) — result: the third numbered item cites the
  issue's own re-read counts (spawn.py=105, own-record=96, both quoted
  verbatim in the prose text) and explains why (the content already
  rides `--append-system-prompt`, so re-opening the file re-derives what
  is already in context) — run live this session, read directly.
rationale: this bullet's own text explicitly waives live-measurement —
  the mechanism-plus-rationale-in-prose bar is what's checkable, and it
  is met.
---
requirement: NR4-mustnot — not applicable, per the issue's own
  annotation ("prose/directive-only change, no runtime mechanism added
  by this bullet")
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 4
  `must not:` clause
verdict: Present
evidence: n/a by the clause's own text; confirmed no runtime mechanism
  (script, gate, code path) was added for this bullet — only the prose
  constant cited under NR4a.
rationale: the issue's own `must not:` line states this sub-clause has
  nothing to check; independently confirmed nothing beyond prose exists
  for it.
---
requirement: NR5 — the record states honestly, in one place, that this
  is a partial/small-scale result and NOT a corpus-measured 5x claim
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 5
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here), "Honest 5x-target statement" paragraph (single
  dedicated paragraph): "This delivery does not claim to have reached it
  or measured a corpus-scale number that could confirm or refute it. ...
  This is a partial, honestly-bounded win on the classes this repo can
  act on — not a corpus-measured 5x result."
canonical: `grep -n "Honest 5x-target statement" -A6
  02aba0a9:docs/issue-2409/reports/implementation.md` (run live this
  session) — result: the paragraph quoted above, plus its own numbers
  (22/35 = 62.9%, 104/496 = 21.0%) computed inline in the same
  paragraph — run live this session, read directly.
rationale: the statement exists, is honest and specific with numbers
  computed inline (not bare), and is confined to one place rather than
  scattered/implied — satisfying the "in one place" clause.
---
requirement: NR5-mustnot — not applicable, per the issue's own
  annotation ("disclosure statement only, no mechanism added by this
  bullet")
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 5
  `must not:` clause
verdict: Present
evidence: n/a by the clause's own text; the "Honest 5x-target statement"
  paragraph cited under NR5 adds no runtime mechanism.
rationale: same reasoning as NR4-mustnot.
---
requirement: NR6a — no verification, record, or observer step is
  removed to achieve any of the above
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 6
verdict: Present
evidence: independently checked this session.
canonical: `git diff origin/main...origin/issue-2409/implementation
  --stat -- 'roles/specs/*.json' 'pipeline.py' '*consult*'` (run live
  this session) — result: empty except one issue-scoped `consult-log/`
  entry — run live this session.
canonical: `git status --short on-the-record/hooks/` (run live this
  session) — result: empty — no gate script touched, re-confirmed live
  this session.
rationale: independently confirmed no role-spec, pipeline, or
  consult-trace mechanism path is touched, and both touched Python files
  show net-additive diffs (see NR3-mustnot).
---
requirement: NR6b — the delivering session's record states explicitly
  what it did NOT touch
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 6
  (documentation sub-clause)
verdict: Present
evidence: `02aba0a9:docs/issue-2409/reports/implementation.md`
  (untracked here), "What was NOT touched" section — names the
  untouched flow (issue->spawn->PR, both observer roles,
  verify-at-landing, consult-trace), untouched code
  (`pretooluse_dispatcher.py`, `hooks.json`, all 20 gate scripts), and
  untouched constants (`_COMPLETION_PROSE`, `_LANDING_BATCHING_PROSE`,
  etc.).
canonical: `git status --short on-the-record/hooks/` (run live this
  session, against the worktree) — result: empty — confirming the
  record's own claim.
rationale: the section exists, is specific, and its central citation was
  independently reproduced this session.
---
requirement: NR6-mustnot — must not remove, weaken, or skip any existing
  verification/observer/record step
spec_ref: issue #2409 `## Acceptance` (amended 2026-08-26) check 6
  `must not:` clause
verdict: Present
evidence: same citations as NR6a/NR6b, both re-run live this session
  (see immediately above).
rationale: identical check to NR6a — the `must not:` clause and the
  `check:` clause of item 6 share one evidentiary basis by the issue's
  own text.

## Open findings

- **Requirement-set breakdown (amended scope), CHANGES round.**
  Sub-clause set: NR1a, NR1b, NR2a, NR2b, NR2c, NR2-mustnot, NR3a, NR3b,
  NR3-mustnot, NR4a, NR4-mustnot, NR5, NR5-mustnot, NR6a, NR6b,
  NR6-mustnot.
  derived: count of `---`-delimited requirement blocks in this record's
  "Requirement verdicts" section above = 16, of which exactly one
  (NR1b) carries `verdict: Incorrect` and the remaining fifteen carry
  `verdict: Present` — counted directly from the section just written,
  this session.
  derived: 1/16 = 6.25% (Non-Present set {NR1b}) and 15/16 = 93.75%
  (Present set) are plain arithmetic on the two counts (1 and 16) in the
  `derived:` line immediately above — no independent recount needed.
  Non-Present set: {NR1b} — one item, same proportion as the prior
  round (`8121072e`), but the verdict on that one item changed from
  Absent to Incorrect this round (see "CHANGES-round re-review" above
  and NR1b's updated block) — Present set: the remaining fifteen items,
  carried forward unchanged from `8121072e` per verdict-
  assignment rule 4 (their evidence is untouched by the
  `64028704`..`1b09aca4` diff, re-confirmed live this session).
  Fix-attempt outcome: commit `980d6db9` on
  `origin/issue-2409/implementation` committed a real, byte-for-byte
  reproducible artifact intended to close NR1b, but the artifact is a
  `batch_summary()`-shaped session/corpus rollup, not the
  `per_turn_breakdown()`-shaped per-turn table the amended check 1's
  literal text asks for ("a per-turn breakdown for a role session (what
  each turn's tool call was for)") — the script itself already
  implements both shapes as separate functions, and the committed
  artifact used the wrong one. Resolution path (unchanged in substance
  from the prior round, restated precisely): commit one example `--md`
  single-session output (the `per_turn_breakdown()`-backed table, not
  a `--batch` rollup) alongside `implementation.md`, or paste one
  inline in the record, in a further follow-up to PR #2416 — still a
  small, mechanical gap (the capability already exists and is tested;
  only the correct published-instance shape is missing), not a design
  failure.
- **Prior round's "Approval-gate Bash-hook denial over-blocks on
  substring match" finding** (carried forward from the phase-1 survey,
  `1bfc914d`) is unrelated to this round's requirement set and not
  re-verified here — out of scope for this re-review, unchanged since
  the prior round.
- **Prior round's "board-gate citation mention-count is imprecise"
  finding** (`1bfc914d`) concerned old requirement R8's evidence
  precision; the underlying citation is unchanged in `02aba0a9` and this
  round's NR3a evidence does not depend on the exact mention count, so
  it is not re-litigated here.

## Next steps

None — `loop_state: reported` (terminal state for this role per
`roles/specs/conformance-review.spec.json`). NR1b above is handed back
via this record, not fixed by this role (out of scope, per this role's
own proposal and the finding-record skill's "never fix or patch what it
finds") — this CHANGES round raised NR1b's verdict from Absent to
Incorrect but did not itself commit a corrected per-turn artifact,
consistent with that same scope boundary.

## skill-verdict

derived: `git diff 64028704 origin/issue-2409/implementation --stat`
(run live this session; also cited under "CHANGES-round re-review"
above) — result: only `implementation.md` and the new artifact file
changed — basis for the "carried forward unchanged" skill-verdict claim
below.

Original round (`8121072e`) invocations:

skill-verdict: conformance-review-requirement-extraction — applied: invoked; used to split issue #2409's amended check-1 bullet into two independent sub-clauses (NR1a regenerate-command-documented vs NR1b artifact-instance-published) per rule 1, and to split checks 2 and 3's `check:`/`must not:` text into NR2a/b/c/mustnot and NR3a/b/mustnot per the same rule, dimension-tagging each per rule 6 (scope-boundary for the `must not:` items, functional for the `check:` items).
skill-verdict: conformance-review-verification-method-selection — applied: invoked; assigned Inspection to structural checks (constant/function existence, file diffs, git status), Demonstration to the two live-fire mechanism reruns (related_files.py, the nested hook-contract session cited in implementation.md), and Test by reusing the existing 79-passed suite per rule 4 rather than re-deriving a parallel manual check.
skill-verdict: defect-verification-independence-from-upstream-verdicts — not-applicable: this session's own role is the original conformance-review pass producing this round's own verdicts, not a downstream defect-verification attempt against another role's closed_checks entry; the skill's own trigger names that downstream scenario, which this session's pipeline position does not match.

This CHANGES round's own invocations (re-reviewing commit `980d6db9`'s
NR1b fix attempt against tip `1b09aca4`):

skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 2 to raise NR1b from Absent to Incorrect (a real artifact was actively produced and the record's own prose claims it "addresses ... NR1b," but it is the wrong one of the script's own two output shapes — present-but-wrong, not omission), named the specific failing clause via `spec_vs_built` per rule 5, and re-checked the evidence live this session (grep for `per_turn`, key enumeration, `| turn | tool` search, byte-for-byte regeneration diff) per rule 6 before finalizing; carried forward the other 15 sub-clauses' unchanged verdicts from `8121072e` per rule 4, basis cited in the `derived:` line above.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; NR1b's updated evidence cites the new commit shas (`980d6db9`, `1b09aca4`) plus this session's own live command outputs rather than a bare path, and names the amended (2026-08-26) Acceptance version explicitly per rule 5, consistent with the original round's citation convention.
skill-verdict: conformance-review-finding-record — applied: invoked; NR1b's block was rewritten in place with the full field set (requirement/spec_ref/verdict/evidence/spec_vs_built/rationale, `spec_vs_built` added per rule 3 since the verdict is now Incorrect) rather than merely relabeling the verdict.
other mounted skills: not triggered this round (conformance-review-requirement-extraction — no new sub-clause split was needed, the existing 16-item set from the original round still exhaustively covers the amended Acceptance text; conformance-review-verification-method-selection — the verification method for NR1b stays Inspection/Demonstration, unchanged from the original round; conformance-review-sampling-derivation — full enumeration of the 16 sub-clauses remained feasible; conformance-review-severity-classification — this round's scope stayed fidelity-checking, not risk-weighting).
