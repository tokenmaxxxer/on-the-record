---
issue: 2593
role: architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408
author: architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408
loop_state: landed
upstream:
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: same-commit
  - path: docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
    sha: same-commit
  - path: docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md
    sha: same-commit
---

# issue-2593 — architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408 record

## What was done

canonical: this record's factual claims are grounded in direct `Read`
of `gates/spawn_on_pr.py`, `gates/merge_gate.py`, `gates/skip_eligibility.py`,
`board.py`, `docs/decisions/2026-08-25-retire-role-axis-staging.md`,
`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`,
`docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`, and
`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md`,
plus `gh issue view 2593 --json body,comments` — all executed/read directly
this session unless a claim is explicitly marked otherwise. derived: `grep -rn 'PR_TRIGGERED_RECORD_KINDS' --include=*.py .` → 13 hits (this session, before-state). derived: `grep -rnE '"(implementation|coding)"' --include=*.py gates/ *.py` → 3 hits (this session). derived: `python3 spawn.py` bare invocation, executed this session — printed the live board plus a `역할:` catalog (both quoted below).

This is a design deliverable, not a patch — per the issue's own instruction,
no code changes land in this session. What follows is the whole-structure
design plus a proposed 3-issue sequence, each step stating what breaks if it
lands alone. Both mounted skills were invoked and applied (skill-verdict
lines under "Why").

### This is not a fresh diagnosis — it is a deferred fork

canonical: `docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`, read in full this session.

`docs/decisions/2026-08-25-retire-role-axis-staging.md` (issue #2241,
status: active) already decomposed "role" into four independent concepts
(lease / author-identity / record-kind / skill) and staged the rollout
across seven stages. Stage 5's own proposal explicitly built
`PR_TRIGGERED_RECORD_KINDS = ("execution-observation", "conformance-review")`
as the record-kind-keyed replacement for the old role-keyed observer pair,
and explicitly deferred the exact question #2593 raises. Quoted verbatim
from that proposal's `## Out of scope`:

> Changing which two kinds are required, or widening/narrowing the observer
> pair — that's a separate policy question from this issue's role→record-kind
> rewrite.

and from its `## Rationale`:

> the survey found this narrowing itself, of 10 candidate roles to these 2
> mechanically presence-checkable ones, is unrelated to the role→record-kind
> swap and stays as-is.

#2593 is that separate policy question, filed after live evidence (#2593's
own comment thread, 2026-08-27) showed the deferred shape still functions
as an identity-validated closed set at the point that gates a merge — the
failure mode issue #2241's own frozen decision `single-skill-axis` forbids
reintroducing. This design does not reopen or contradict stage 5's
`kind:`/`author:` machinery (self-verification exclusion, `<subject>/<kind>`
branch-suffix signal for pre-landing PRs) — that machinery is reused
unchanged. It replaces only the one piece stage 5 named as deferred: how
`gates/` decides which `kind:` values satisfy the obligation.

### Current-state findings

canonical: `gates/spawn_on_pr.py` lines 39, 70-153, 339-355; `gates/merge_gate.py` lines 116-160, 310-368; `gates/skip_eligibility.py` lines 128-175; `board.py` lines 795-819 — all read directly this session via the `Read`/`Bash sed -n` tools against this repo's current worktree commit. derived: `grep -rnE '"(implementation|coding)"' --include=*.py gates/ *.py` → exactly 3 hits (`gates/skip_eligibility.py:140`, `gates/spawn_on_pr.py:110` docstring-only, `gates/spawn_on_pr.py:125` live).

- `gates/spawn_on_pr.py:39`: `PR_TRIGGERED_RECORD_KINDS = ("execution-observation", "conformance-review")`.
- Four live call sites read this tuple for identity comparison:
  - `applicable_record_kinds()` (`gates/spawn_on_pr.py:70-104`) — `matched = kind_field if kind_field in kinds else (name if name in kinds else None)` — decides which of the tuple's two kinds are still missing for a subject.
  - `subject_deliverable_branch()` (`gates/spawn_on_pr.py:130-153`) — `b[len(prefix):] not in PR_TRIGGERED_RECORD_KINDS` — excludes the two kinds' branches to isolate the deliverable branch.
  - `_exempt_own_record_kind()` (`gates/merge_gate.py:116-158`) — `if own_kind in spawn_on_pr.PR_TRIGGERED_RECORD_KINDS: return [k for k in missing if k not in spawn_on_pr.PR_TRIGGERED_RECORD_KINDS]` — breaks the sibling-observer mutual-blocking cycle (issue #2380/#2233). This is a direct cross-module attribute reference: `merge_gate.py` reads `spawn_on_pr.PR_TRIGGERED_RECORD_KINDS` at runtime, not a copy. Deleting the constant from `spawn_on_pr.py` without updating `merge_gate.py` in the same change breaks the merge gate's import at load time — this is why stage A below must touch both files atomically.
  - `subject_deliverable_record()` (`gates/spawn_on_pr.py:107-127`) — `kind_field == "implementation" or (kind_field is None and name == "implementation")` — one of the two live grep hits cited above.
- `gates/merge_gate.py:316-318`: `missing = required_verification_missing(...); if missing: reasons.append(f"필요한 검증 기록이 없다: {missing}")`, and `main()` (`:362-368`) prints `거절: PR #{pr} ({subject})` plus each reason, exit code 1 — the refusal mechanism acceptance bullet two asks to be demonstrated against, named by file:function.
- `gates/skip_eligibility.py:140,172`: both hardcoded `"implementation"` fallbacks are unreachable in production — `classify_for_subject()`'s sole production caller (`spawn_on_pr.py:352`, inside `_filter_execution_observation()`) always passes `ref=branch` explicitly, and `branch` (from `subject_deliverable_branch()`) is guaranteed non-`None` before that call (`spawn_on_pr.py:301-304` short-circuits otherwise). `skip_eligibility.py`'s own docstring at that line already documents this. Dead code, safe to delete.
- `gates/spawn_on_pr.py:339-355` (`_filter_execution_observation`): its docstring states this classifies eligibility on change size, reversibility, and claim vocabulary, specifically for whether a change needs an `execution-observation`-flavored check — not a generic, kind-agnostic exemption. See Open findings.
- `board.py:795-819`: bracket rendering (`[{r}]`) draws `r` from filename stem / roster lease-slug, never from `PR_TRIGGERED_RECORD_KINDS` or any `kind:` frontmatter value; `grep -n "PR_TRIGGERED\|spawn_on_pr" board.py` → 0 hits this session — board.py and the gates/ mechanism are fully disjoint today. `python3 spawn.py` (bare invocation) executed this session printed, among ~570 subjects, `subject: issue-100` / `  [coding] loop_state: landed` and `subject: issue-1000` / `  [implementation] loop_state: landed   verdict: supports` — matching the bug report's claim verbatim.
- The same bare invocation also prints, at the end, a block headed `역할:` ("Roles:") listing 43 named entries with descriptions and `board_condition` heuristics (`implementation`, `conformance-review`, `execution-observation`, `architecture`, ... — full list captured this session). This is the pointer consult.md already sends sessions to ("`spawn.py` 가 아는 역할 이름 — 인자 없이 `spawn.py` 를 부르면 목록이 뜬다", `on-the-record/commands/consult.md:30`, read this session) — a legitimate, curated skill catalog, not dead vocabulary. Its defect for #2593 is that the heading/description use the word "역할"/"role."
- Consumer-text survey: cross-checked directly this session against `on-the-record/hooks/directive.sh` (`grep -n -i 'role' on-the-record/hooks/directive.sh`, lines 315/321 confirmed live) and `spawn.py` (`sed -n` around lines 1755-1770, 1815-1825, 2202 confirmed live). Two background research passes additionally surveyed the six directive `.md` and three command `.md` files; those approximate counts (order-of-magnitude in the hundreds, a large fraction generic-narrative "역할") are relayed from that research — derived: not independently reproduced line-by-line this session; canonical: task-notification for background agent a0b122f699505e122, received this session, full text relayed in-transcript — treat as approximate, not a precise derived count. The issue's own corrected comment (`gh issue view 2593`, read this session, comment timestamped 2026-08-27T04:13:45Z) rules narrative use in scope too: "the word must not appear anywhere a consumer session can see it... no exception for refusals, no exception for historical description, no per-site judgment call."

## Why

canonical: this section's design claims are grounded in the direct reads cited under "What was done" → "Current-state findings," plus a fresh direct read of `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md` this session for the `kind:` vocabulary's own stated closed-ness.

### The mechanism replacement (the core design decision)

canonical: `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md` and `docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`, both read in full this session (same citations as above, restated here because this subsection is its own heading boundary).

The decisive test from #2548 ("does anything still validate identity
against a closed set," not "did the name change") applied honestly to
`kind:` produces a real fork, not a clean single answer. Both options were
considered; Option 2 is recommended, but the fork must be resolved
explicitly before stage A's build starts — it cannot be left ambiguous,
because `spawn_on_pr.py` and `merge_gate.py` must be rewritten consistently
with one choice.

**Option 1 — vocabulary-property lookup (rejected as primary, kept as
fallback).** `docs/specs/record-kind-vocabulary.md`'s closed vocabulary
(per stage 1's proposal text: "formalizes the `kind:` field... into a
spec'd, closed vocabulary e.g. `survey`, `scout-brief`, `adr`,
`execution-observation`, `conformance-review`, ...") gains a boolean
property per entry (e.g. `independent_verification: true`, set on exactly
today's two kinds — behavior parity). `gates/` computes
`required_verification_kinds()` from that one canonical spec file instead
of a duplicated tuple. Preserves every current nuance, including the
execution-observation-specific skip-eligibility carve-out, at the cost of
still being a closed set that gates a merge — just relocated. Structurally
close to the shape the #2139 consult already rejected (importing the tuple
into `board.py` as a single source of truth) — canonicalizing the closed
set rather than removing it as the deciding mechanism.

**Option 2 — self-declared boolean + count threshold (recommended).** Add
one new, self-declared frontmatter field — e.g. `verifies_subject: true` —
that any record, regardless of `kind:` value or which skill produced it,
sets to declare "this record is an independent check of the subject's
deliverable." Same self-declaration pattern stage 1 already uses for
`author:`. `required_verification_missing()` then counts records under the
subject's board with `verifies_subject: true` and `author:` different from
the subject's deliverable author (exact reuse of stage 5's existing
self-verification guard) and refuses the merge unless that count meets
`REQUIRED_INDEPENDENT_VERIFICATIONS` (a plain integer, `2`, matching
today's count — a business rule about how many, not which names). This is
the one design with no enumeration left anywhere in `gates/`.

**Rejected alternative considered and discarded early**: kind-presence
alone (any `kind:` value, no new field) as the verification signal.
Rejected because `kind:` also covers unrelated document genres (`survey`,
`scout-brief`, `adr`, ...) per stage 1's own vocabulary spec — a design doc
authored by a different session under the same subject would incorrectly
satisfy the requirement. A dedicated, purpose-built, self-declared field
avoids this false positive.

**The behavior-change cost of Option 2, stated plainly**: today,
skip-eligibility removes specifically `"execution-observation"` from
`missing` for low-risk (population-S) subjects — such a subject still
needs `conformance-review`. Under Option 2, the equivalent becomes reducing
`REQUIRED_INDEPENDENT_VERIFICATIONS` from 2 to 1 for those subjects
(skip-eligibility's existing classification is reused unchanged as the
trigger; only its effect changes from "excuse this one named kind" to
"need one fewer independent check, any kind"). This is a real policy
nuance change and must be surfaced to whoever approves stage A, not
silently absorbed.

### Board.py (Step B) — why not the two already-rejected shapes

canonical: `gh issue view 2593` body, read this session, quoting the #2139 consult's two ruled-out shapes; `board.py:795-819`, read this session (restated citation, new heading boundary).

The #2139 consult ruled out (a) dropping the bracketed token entirely and
(b) relabelling the line while still printing the old role strings. This
design does neither: it keeps printing `[X]` exactly as today (same
information, same filename-stem/lease-slug source, zero data-flow change),
and adds an inline, per-line provenance marker directly in the format
string itself — e.g. `[record: X]` instead of bare `[X]` — so a reader
cannot mistake "this bracket names a historical report file" for "this is
a `--skills` value" without needing a separate caveat elsewhere on the
page. Exact wording is left to stage B's own proposal; the shape
constraint (inline, every line, non-optional) is fixed here.

### Consumer-text purge (Step C) — sizing correction

canonical: `gh issue view 2593` comments, read this session, comment timestamped 2026-08-27T04:13:45Z (the corrected-scope ruling quoted under "Current-state findings," restated here for this heading boundary).

The issue's own surface list undercounts this surface's true size. The
corrected operator ruling extends scope to every consumer-visible
occurrence of the word "role"/"역할," not just literal retired-name
examples — this reaches the narrative hits in `run.md` and the
bare-invocation `역할:` catalog header. This is a large, low-judgment,
purely-textual sweep with zero runtime coupling to stages A or B — a
legitimate reason to give it its own issue per the module-boundary skill's
bounded-context rule (this text lives in a different "ubiquitous language"
domain — documentation prose — from the gates/ enforcement code) rather
than a reason to fold it into stage A.

### Skill verdicts

canonical: Skill-tool output for `architecture-module-boundary-definition` (loaded directly in-session) and Agent-relayed Skill-tool output for `architecture-decomposition-strategy` (delegated to a subagent this session, full output relayed verbatim in-transcript) — both received this session, both cited by rule number below.

skill-verdict: architecture-module-boundary-definition — applied: invoked; used rule 5 (bounded contexts, not schemas, as the seam) and rule 4 (every cross-component interaction through an explicit interface, no direct reach-through) to justify keeping stage A/B/C as three separate issues and to justify Option 2's self-declared-field design over Option 1's cross-module canonical-constant reach-through.
skill-verdict: architecture-decomposition-strategy — applied: invoked (via a delegated subagent call, output relayed verbatim); used the operational-evidence rule (do not split without collected evidence) inverted for issue-sequencing: stage A is evidenced-coupled (direct cross-module attribute reference, confirmed by reading the code, see Current-state findings) so it stays one unit; stages B and C are evidenced-decoupled (confirmed zero import/data coupling via direct grep/read, same citation) so splitting them is justified by evidence, not convenience.

## What did not work

canonical: task-notification for background agent `a0b122f699505e122`, received this session, arriving after a liveness probe sent via SendMessage went unanswered across several ScheduleWakeup cycles.

None in the sense of a written-then-reverted change — this session
delivered a design document only; no code was written. One coordination
note: a background research worker (survey of directive/command markdown
text) ran past the other two workers' duration and did not respond to the
liveness probe within a reasonable window; rather than wait further, that
surface was gathered directly via `Read`/`grep` in this session instead.
The worker's task-notification arrived shortly after with an independent
report, used to cross-check (not replace) the direct findings already in
this record.

## Upstream basis

canonical: all four paths below were opened directly via the `Read` tool this session, at this session's own commit (no separate sha to pin — see frontmatter `same-commit`).

- `docs/decisions/2026-08-25-retire-role-axis-staging.md` — the frozen decision this design extends, not contradicts.
- `docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md` — the proposal whose "Out of scope" clause this issue's own policy question falls into.
- `docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` — the terminal deletion stage this design's stage A must land before, and whose consumers (`roles/`, `spawn_roles.json`) stage C's bare-invocation catalog rewording should not duplicate or conflict with.
- `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md` — source of the `kind:` field's own stated closed-vocabulary design, cited under "Why."

canonical: task-notifications for background agents a246f3f64fb902e3f, a759e00c11bc9445e, a0b122f699505e122, all received this session — the three research passes named below.

Three background research passes (board.py rendering; gates/ closed-tuple
consumers; directive/command text + printed role strings) were dispatched
via the freelunch protocol and used as a first pass; every claim from them
that became load-bearing in this record was independently cross-checked
against a direct `Read`/`grep` this session (see the `canonical:`/`derived:`
tags throughout — none of this record's load-bearing claims rest on the
subagent output alone).

## Open findings

canonical: `python3 spawn.py` bare invocation output (the `역할:` catalog block), captured this session; `gh issue view 2593` body and Non-goals section, read this session.

1. **Skip-eligibility's kind-specificity (Option 2's real cost)** — not
   resolved here. `_filter_execution_observation`'s three-axis
   classification is inherently about the execution-observation lens
   specifically; Option 2 converts its effect from "excuse this named
   kind" to "need one fewer independent check, any kind" (see Why, above).
   This needs an explicit yes/no from whoever approves stage A's proposal
   — not a default this design session can set unilaterally. Resolution
   path: state both readings in stage A's own proposal `## Constraints`
   and let the approval decide, or escalate via `consult` to a role with
   standing over verification policy before drafting stage A.
2. **`spawn.py`'s `role_data()` / `spawn_roles.json`** — confirmed live
   this session (`python3 spawn.py` bare invocation) to print a `역할:`
   catalog including `implementation` as a listed entry. Not traced this
   session: whether `spawn_roles.json` is generated from `roles/*.json`
   (the terminal deletion stage of the #2241 program, per
   `docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`, deletes
   `roles/*.json` — if `spawn_roles.json` is derived from it, that stage
   already handles this catalog's eventual removal; if independent/
   hand-maintained, stage C's rewording needs to touch it directly). Needs
   a short investigation at the start of stage C's build.
3. **Whether the `roles/` directory name itself is in scope anywhere** —
   confirmed out of scope for #2593 (its own surface list and Non-goals
   section, read via `gh issue view 2593` this session, do not name the
   directory; renaming a directory with many consumers is a materially
   larger migration, already the terminal deletion stage's territory per
   finding 2 above). Flagged so stage C's assignee does not accidentally
   expand scope to it.

## Next steps

canonical: coupling/decoupling claims below restate the direct-Read findings already cited under "What was done" → "Current-state findings" (same commit, same session) — repeated here as the basis for sequencing, not as new unverified claims.

Proposed 3-issue sequence. Stage A must land as one atomic unit (confirmed
cross-module coupling via direct attribute reference, see above); stages B
and C are independent of A and of each other (confirmed zero coupling — no
shared import, no shared data path) and may land in any order, including
before A or concurrently with it.

### Issue A — decouple the observer-pair requirement from `PR_TRIGGERED_RECORD_KINDS` (stage "5b" of the #2241 program)

canonical: `gates/spawn_on_pr.py`/`gates/merge_gate.py` lines cited under "What was done" → "Current-state findings," same session, same commit (restated here for this heading boundary).

**What lands**: `gates/spawn_on_pr.py` + `gates/merge_gate.py` rewritten
per Option 2 above (pending the skip-eligibility fork's resolution, Open
finding 1); `gates/skip_eligibility.py`'s two confirmed-dead fallback
strings deleted; `PR_TRIGGERED_RECORD_KINDS` deleted entirely.

**What breaks if this lands alone (before B/C)**: nothing external —
`board.py` is confirmed disjoint (see "Current-state findings" above) and
keeps rendering brackets exactly as today, still ambiguous but not newly
broken. Consumer-facing text is unaffected. This step alone satisfies
acceptance bullets one, two, and (modulo `skip_eligibility.py`'s two
now-deleted dead strings) the bulk of bullet four — the load-bearing
bullet (a demonstrated merge refusal, mechanism named) is fully
satisfiable by this step alone via the existing refusal path
(`gates/merge_gate.py:316-318,362-368`), with its message text changed
from naming two literal kinds to reporting the count/threshold.

**Depends on**: nothing outside this repo's current state; does not
depend on B or C.

### Issue B — board.py bracket-label provenance marker

canonical: `board.py:795-819`, read this session (restated citation for this heading boundary).

**What lands**: the inline per-line marker described in Why, above (exact
wording decided in B's own proposal); zero change to the underlying
`lease_slugs`/`_skill_axis_report_names` data flow.

**What breaks if this lands alone (any order relative to A/C)**: nothing —
confirmed zero coupling to gates/ (`grep -n "PR_TRIGGERED\|spawn_on_pr" board.py` → 0 hits, cited above) or to the consumer-text surfaces. Landing
B without C satisfies acceptance bullet three's first half but not its
second half (pointing sessions to real skill names) unless C's rewording
of the `역할:` catalog header/pointer text has also landed — the two
halves of that bullet are split across B and C by design.

**Depends on**: nothing.

### Issue C — consumer-visible "role"/"역할" vocabulary purge

canonical: `on-the-record/hooks/directive.sh` and `spawn.py` lines cited under "What was done" → "Current-state findings," read directly this session; task-notification for background agent a0b122f699505e122 for the markdown-file survey, received this session (restated for this heading boundary).

**What lands**: zero-occurrence sweep across `spawn.py` (bare-invocation
`역할:` header/framing, all `--help`/usage-error strings naming `role` or
`role-or-skill`, per Open finding 2's investigation),
`on-the-record/hooks/directive.sh` (2 confirmed-live sites), the six
directive `.md` files, and three command `.md` files (per-file weight not
independently re-measured this session — see the research-pass citation
above for `run.md`'s share). Given the approximate overall size, recommend
splitting further into C1 (`spawn.py` + `directive.sh` — smaller, highest
severity, always-on/live-tool surfaces) and C2 (the nine markdown files —
larger diff, lower severity, mechanical reword) if the assignee finds one
PR unwieldy; not mandated here.

**What breaks if this lands alone (any order relative to A/B)**: nothing —
purely textual, `--skills` has been the sole live spawn syntax since
#2572, independent of #2593. Landing C without A means the reworded text
remains accurate either way; landing C without B leaves the board's
bracket ambiguity unaddressed.

**Depends on**: nothing; should coordinate timing (not blocking) with the
#2241 program's terminal deletion stage per Open findings 2 and 3, to
avoid duplicated or conflicting edits to `spawn_roles.json`/`roles/`
consumers.

### Acceptance-bullet-to-issue mapping

canonical: `gh issue view 2593` body, `## Acceptance` section, read this session; grep results cited under "Current-state findings" above (restated for this heading boundary).

- Bullet one (`PR_TRIGGERED_RECORD_KINDS` → zero occurrences): Issue A.
- Bullet two (merge refusal for missing independent verification,
  mechanism named, demonstrated live): Issue A.
- Bullet three (board bracket unambiguous / real skill names pointed to):
  Issues B (first half) + C (second half, `역할:` catalog reword).
- Bullet four (`"(implementation|coding)"` grep in `gates/`/`*.py` →
  comments/docs only): Issue A deletes the two live hits;
  `gates/spawn_on_pr.py:110`'s docstring-quote hit may remain as a named
  documentation citation per the bullet's own empty-state text.
- `must not:` (the ~2274 existing records; independent-check obligation
  not weakened/made advisory): honored by all three — none of A/B/C touch
  `docs/issue-*/reports/` record content, and A's count-based requirement
  is a hard blocking check (exit code 1 on failure), never advisory.
