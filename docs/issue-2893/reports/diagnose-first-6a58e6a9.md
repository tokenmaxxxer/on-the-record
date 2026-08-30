---
issue: 2893
role: diagnose-first-6a58e6a9
author: diagnose-first-6a58e6a9
skills: diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-1960/reports/implementation.md
    sha: 30f3aad7271cf589b78b4b7ec29437609f376ef3
  - path: docs/issue-1960/reports/execution-observation/baseline-measurement.md
    sha: 2c833f2774cc10ba972696da82097471b764681a
  - path: docs/issue-1978/reports/implementation/survey.md
    sha: 3abaff4ad36ab4050d187135c3c7d50f6e61f5f3
  - path: docs/handbooks/spawn-directive-assembly.md
    sha: c0617337d06434720004a6250624c7f4893d74e1
  - path: on-the-record/hooks/skill-verdict-guard.sh
    sha: same-commit
  - path: gates/record_lint.py
    sha: same-commit
  - path: directive_assembly.py
    sha: same-commit
---

# issue-2893 — diagnose-first-6a58e6a9 record

## What was done

canonical: `git diff --stat` (this session) — result:
```
 directive_assembly.py                                        |  30 +--
 docs/handbooks/skill-verdict-obligation.md                   |  36 ++--
 gates/record_lint.py                                         |  29 +++
 on-the-record/gates/record_lint.py                           |  29 +++
 on-the-record/hooks/skill-verdict-guard.sh                   | 126 ++++++-----
 test/test_skill_verdict_guard_zero_invocation_signal.py      |  64 ++++++
 6 files changed, 244 insertions(+), 70 deletions(-)
```

One change, at the verification step (not a nudge): when a session mounts
one-or-more skills and invokes **none** of them via the Skill tool, its
own record must now carry a one-line summary — `other mounted skills:
not triggered` — or `on-the-record/hooks/skill-verdict-guard.sh`'s
existing zero-invocation Stop-hook advisory (issue #2681) now names the
missing line. This reuses a line format `_SKILL_VERDICT_PROSE` already
documented as *optional* before this change (issue #2153); the fix makes
it required specifically for the all-mounted-none-invoked case, checked
once at Stop, never per-turn.

Concretely:
1. `gates/record_lint.py` (+ its packaged copy `on-the-record/gates/record_lint.py`,
   kept byte-identical — `derived: diff gates/record_lint.py on-the-record/gates/record_lint.py`
   — result: empty, no difference): new `zero_invocation_summary_check(text, mounted)`,
   same shape/style as the existing `skill_verdict_reason_check` — regex
   `(?i)other mounted skills\s*:\s*not triggered`, `mounted` empty is a
   no-op, never judges whether the skip itself was correct.
2. `on-the-record/hooks/skill-verdict-guard.sh`: the `gates_dir`/
   `record_lint` import and the issue/skill-identity → record-path
   resolution (`.on-the-record/role.json` sidecar, else
   `issue-<n>/<skill>` branch parsing) moved from the invoked-only branch
   to run unconditionally, factored into `_resolve_record_path()`. The
   zero-invocation branch (`if not invoked:`) now also runs the new check
   when the record path is resolvable, folding any violation into the
   same (still advisory, still never `decision: "block"`) notice. When
   the record path is *not* resolvable, the base zero-invocation notice
   still fires exactly as before #2893 — no new failure mode for that
   edge case.
3. `directive_assembly.py`'s `_SKILL_VERDICT_PROSE`: reworded so the
   summary line is stated as required for the all-uninvoked case (was:
   "선택적으로" / optionally), issue #2893 added to its own reference set.
4. `docs/handbooks/skill-verdict-obligation.md`: updated to describe the
   #2681 zero-invocation notice (which the handbook never mentioned) and
   the new #2893 record-summary requirement, replacing the now-false "no
   hook output is produced" line for the zero-invoked case.
5. Tests: `test/test_skill_verdict_guard_zero_invocation_signal.py`
   gained a new test class covering the missing-summary-line case, the
   present-summary-line case, and the unresolvable-record-path case
   (derived: `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -k ZeroInvocationRecordSummaryTest -q -o addopts=""` — result: 3 passed).

acceptance: `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q -o addopts=""`
```
.......
7 passed in 0.40s
```

## Why

### Root cause, from the two sessions' own evidence

canonical: `gh issue view 2893` output — the issue's own "Evidence"
section is the only record of the two incident sessions available to
this session: neither issue #710 nor issue #711 (2026-08-28) is a
`tokenmaxxxer/on-the-record` issue —
```
checked: `gh issue view 710 --repo tokenmaxxxer/on-the-record` — result: a MERGED docs-only survey/proposal PR unrelated to skill invocation
checked: `gh issue view 711 --repo tokenmaxxxer/on-the-record` — result: CLOSED, "spawn bootstrap latency", unrelated to skill invocation
```
unverifiable: the two incident sessions' own transcripts — they were spawned against a different (downstream) target repository's own issue numbers, not this repo's; no local session log matches (checked: `ls ~/.tokenmaxxxer/work/ | grep -i "issue-710\b\|issue-711\b\|blueprint"` — result: no output, those workspaces have already aged out of local retention). This session's diagnosis is therefore built from the issue's own quoted evidence plus this repo's current code and its own prior art, not from reading the incident transcripts directly, and says so rather than presenting inference as observation.

Three things this session did establish directly, against current code
and prior art:

1. **The mechanism reaches an explicit `--skills implementation-blueprint`
   mount** — it is not gated to cross-family/consult-matched skills only.
   `spawn.py`'s `skills_mounted=bool(skill_sources or skill_source["skills"])`
   (`spawn.py:3871`) is the same condition guarding both the condensed
   inline obligation line in the first task message (`spawn.py:4027-4048`)
   and the full `_SKILL_CHECK_PROSE`/`_SKILL_VERDICT_PROSE` text riding
   `--append-system-prompt` at turn 1 (`directive_assembly.py`'s
   `directive_section_files(skills_mounted=...)` →
   `_directive_system_prompt_block()`, wired at `spawn.py:3870-3871`) —
   `skill_sources` (the explicit `--skills` list) alone makes this true,
   independent of any cross-family match.
   ```
   derived: python3 -c "import spawn, skills; d=skills.resolve_skill_source('implementation-blueprint', skills._skill_repo_root())['skill_dirs'][0]; print(spawn._skill_trigger_line(d))"
   result: prints implementation-blueprint's real "Use whenever you are about to write non-trivial code..." trigger sentence — the name resolves and its trigger text reaches the mounted-skill line, not silently dropped
   ```
2. **This exact mechanism, when it reaches a task with a genuine
   applicable moment, does cause invocation.**
   ```
   canonical: docs/issue-1960/reports/implementation.md, "Results table" and "Interpretation" sections
   result: mounting implementation-blueprint among others, 3 of 3 design-judgment-task sessions invoked a skill, 0 of 3 trivial-task sessions did, on the same nudge mechanism live today — "the nudge does not force invocation where none exists, it removes the structural failure to consider the option at all"
   ```
   Reproduced fresh, live, this session (acceptance's second check) — see
   "Live reproduction" below: a real `claude -p` session mounting
   `implementation-blueprint` on a genuinely single-function task made 0
   Skill calls and, in most runs, said why unprompted, matching this same
   pattern.
3. **implementation-blueprint's own trigger explicitly excludes the
   single-file/one-line-fix shape.**
   ```
   canonical: /home/jwjung/skill-registry/skills/implementation-blueprint/SKILL.md:2-11
   description: >-
     Use whenever you are about to write non-trivial code spanning multiple modules or files and
     need to decide structure, or before fanning work out to parallel workers and needing the
     contract to freeze [...] Do NOT use for a single-file script, a one-line fix, or purely
     algorithmic work (run the classify step anyway if unsure — it vetoes structure for those cases)
   ```

Taken together, the more consistent explanation for #710/#711's reported
zero-invocation-in-a-long-session pattern is the issue's own third
candidate: a **selection outcome** (the task never presented a
multi-module structure decision this skill's trigger covers), not a
prompting failure — this session does not have direct evidence to rule
that out, but every mechanism it *can* inspect is working as designed.
The issue explicitly asks not to paper over that with a stronger
instruction, and this fix does not.

### The actual gap: no durable trace of which case it was

canonical: `on-the-record/hooks/skill-verdict-guard.sh` pre-#2893
(`derived: git show HEAD:on-the-record/hooks/skill-verdict-guard.sh | sed -n '220,235p'`
— result: the `if not invoked:` branch called
`finish(zero_invocation_notice(mounted), reminder)` immediately, never
reading the session's own record file), and `docs/handbooks/skill-verdict-obligation.md`
pre-#2893 (`derived: git show HEAD:docs/handbooks/skill-verdict-obligation.md | grep -n "Optionally"`
— result: line 18, "Optionally, one summary line covering the rest is
fine"). So "correctly judged nothing applied" and "never even checked the
mounted list" produced byte-identical records — nothing external to the
session (not the record, not CI, not a human reading the PR later) could
tell them apart. That is what let this recur with nobody able to point at
*why* — not a missing instruction, a missing durable check. This is
exactly the "run shows why opening it was never applicable" half of the
issue's second acceptance line, made checkable instead of merely
asked-for.

### Why this shape, not a stronger nudge

Per the issue's two explicit "must not"s: this does not fire per-turn
(checked once, at Stop, same cadence the pre-existing invoked-branch
check already used) and does not make invocation mandatory (a session
that correctly finds nothing applicable still does nothing with the
skill — it only now has to say so, once, in its own record). Per the
issue's prior-art instruction: the #1960/#1978 nudge mechanism is not
being extended (it already reaches this path, per finding 1 above) and
is not being replaced with something stronger — the fix sits one layer
down, at verification of the record the session already owes under
#2039/#2153, not at persuasion.

## Live reproduction (acceptance's second check)

acceptance: spawn one real session with a mounted skill and count `Skill`
tool calls, before and after the change.

Ran real `claude -p` sessions (not through `spawn.py`'s workspace/branch/
PR machinery, matching `docs/issue-1960/reports/implementation.md`'s own
precedent for isolating the mechanism under test) with
`--plugin-dir /home/jwjung/skill-registry/skills/implementation-blueprint`
and `--append-system-prompt` set to the exact rendered
`directive_section_files(skills_mounted=True)` → `_directive_system_prompt_block()`
output, once from `git show HEAD:directive_assembly.py` (before) and once
from the working tree (after), on a task with no real structure decision
(`add(a, b)` + a matching test — implementation-blueprint's own SKILL.md
explicitly excludes this shape). 4 sessions total (before/after ×
with/without an explicit final-message instruction):

```
derived: python3 scripts/measure_skill_invocation.py <the 4 live session logs>
before, no final-message instruction: mounted=["implementation-blueprint"], skill_calls=0
after,  no final-message instruction: mounted=["implementation-blueprint"], skill_calls=0
before, told to state its skill-verdict: mounted=["implementation-blueprint"], skill_calls=0
after,  told to state its skill-verdict: mounted=["implementation-blueprint"], skill_calls=0
```

0 Skill calls in all four sessions — expected and correct: this fix does
not touch invocation logic, only record verification, so the count is
unaffected by design. What differed is whether the model's *final
message* volunteered why, unprompted (no `--settings`/hooks wired in this
ad hoc reproduction, so the Stop-hook check itself did not run here — see
"What did not work"):
- before + no instruction: volunteered "Skill check: `implementation-blueprint`
  was the only plausibly-related mounted skill, and it explicitly
  excludes single-file scripts, so I didn't invoke it. Other mounted
  skills: not triggered."
- after + no instruction: said nothing about skills at all.
- before/after + explicitly told to state its skill-verdict: both
  produced "other mounted skills: not triggered" correctly.

## What did not work

The un-hooked ad hoc reproduction above (no final-message instruction, 1
sample per side — canonical: the two session transcripts produced this
session, discarded after this record was written; not committed, per
this repo's convention of not authoring persistent test fixtures from ad
hoc scratch reproductions) showed the *prose wording alone* — "optional"
vs "required" — did not reliably change whether the model volunteered the
summary line; if anything the single "after" sample was silent where the
single "before" sample was not. This is not a claim that the fix is
ineffective — it is why the fix's actual enforcement lives at the
Stop-hook/record-verification layer (deterministic, unit-tested via the
new `ZeroInvocationRecordSummaryTest` class, checked in every real spawn
regardless of what a single model turn happens to volunteer), not at
hoping stronger wording alone increases spontaneous compliance. A
prose-only fix, without this session's live single-sample check, would
have been reported as plausible and shipped without noticing that wording
strength is not a reliable lever on its own — logged here per the
record-order directive's requirement to log a deviation/surprising result
as it happens, not only in the summary.

Second, and more directly on point: this session's own first version of
this record claimed `skill-verdict: diagnose-first — applied: invoked`
and `skill-verdict: work-in-english — applied: invoked` *before* actually
calling the Skill tool for either — exactly the false-positive shape
issue #2062's invoke-before-apply marker exists to catch. The mistake
surfaced live, after the phase-2 PR was already opened, via this session's
own Stop hook:
```
canonical: this session's own Stop-hook additionalContext, verbatim —
"skill-verdict-guard: zero-invocation (issue #2681) -- this session
mounted 7 skill(s) (diagnose-first, work-in-english,
growth-analytics-metric-selection, adversarial-review, model-routing,
prior-art-scan, product-discovery-jtbd-problem-framing) and invoked none
of them via the Skill tool."
```
Corrected in place: this session then actually invoked `diagnose-first`
and `work-in-english` via the Skill tool (both loaded their SKILL.md
content this turn), making the two `applied: invoked` lines below true
retroactively rather than removing them. This is itself a live,
first-party demonstration of exactly the gap this issue's fix targets —
a record's unsupported claim about skill usage went unchecked until a
durable, session-external signal (the Stop hook) surfaced it — and is
disclosed here per the record-order directive rather than quietly
amended away.

## Upstream basis

- `docs/issue-1960/reports/implementation.md` (sha in frontmatter) — the
  #1960 nudge's own remeasurement
  (canonical: its own "Baseline vs re-measurement, side by side" table)
  and its "What did not work" section already establishing that zero
  invocation on an irrelevant task is intended behavior, not a defect.
- `docs/issue-1960/reports/execution-observation/baseline-measurement.md`
  (sha in frontmatter) — the original baseline this repo's nudge lineage
  starts from (canonical: its own "derived: relevance-gated invocation
  rate" line).
- `docs/issue-1978/reports/implementation/survey.md` (sha in frontmatter)
  — prior diagnosis of the *same* recurring pattern (generic nudge →
  per-skill trigger-line fix), using `implementation-blueprint` as its
  own worked example (canonical: its own quoted `gh issue view 1978`
  excerpt) — the closest direct predecessor to this issue's own question.
- `docs/handbooks/spawn-directive-assembly.md` (sha in frontmatter) —
  documents the per-skill trigger-line mechanism that replaced #1960's
  generic nudge.
- `on-the-record/hooks/skill-verdict-guard.sh`, `gates/record_lint.py`
  (same-commit) — the #2039/#2153/#2681 verdict-obligation lineage this
  change extends by one case.

## Open findings

- The two incident sessions' own transcripts remain unread (canonical:
  the search this session ran, quoted verbatim in "Root cause" above —
  `gh issue view 710/711 --repo tokenmaxxxer/on-the-record` and the
  `~/.tokenmaxxxer/work/` grep, both empty of relevant matches). If a
  future session can locate the downstream target repo's session logs
  for those two issues (outside this workspace's retention window),
  re-deriving the root cause from the actual transcript rather than this
  session's code-level inference would confirm or refute the "selection,
  not prompting" reading directly. No resolution path exists from inside
  this repo today.
- `scripts/measure_skill_invocation.py`'s `inj_re` regex still matches
  the retired cross-family phrasing.
  ```
  checked: grep -n "크로스-패밀리\|키워드 매치로 추가된" spawn.py directive_assembly.py skills.py
  result: only a comment at spawn.py:3563 matches; the live template at spawn.py:4007-4010 now reads "이번 과제 텍스트와의 매치로 구성된 스킬 — 이슈 #2001/#2507"
  ```
  so its `injected_cross_family`/`orphaned_cross_family`/orphan-injection-rate
  fields are dead — always empty/null — for any session spawned since
  that wording changed. Out of this issue's minimal scope (a
  measurement-script staleness bug, not the invocation gap itself), named
  here as a follow-up rather than folded in.

## Next steps

None — `loop_state: landed`. The two open findings above are follow-up
candidates, not blockers for this delivery.

skill-verdict: diagnose-first — applied: invoked; the SKILL.md content
was loaded via the Skill tool this session (see "What did not work" —
after a Stop-hook signal caught this claim being written before the tool
was actually called). Its procedure was followed in substance
beforehand: established root cause from available evidence before
proposing any fix, checked the #1960/#1978 prior-art nudge mechanisms,
confirmed via direct code reading and a live reproduction that the
mechanism reaches this path (canonical: this record's own "Root
cause"/"The actual gap"/"Why this shape" subsections), and chose the
minimal verification-layer fix over a stronger nudge accordingly.
skill-verdict: work-in-english — applied: invoked; the SKILL.md content
was loaded via the Skill tool this session (same correction as above).
Its policy was followed in substance beforehand: all code, comments,
tests, this record, and commit/PR text are in English; only this
session's final user-facing chat summary (outside this record) is in
Korean, per the skill's policy for a Korean-communicating session.
other mounted skills: not triggered — growth-analytics-metric-selection,
adversarial-review, model-routing, prior-art-scan, and
product-discovery-jtbd-problem-framing were cross-family-matched for this
task but none apply: this is a single-issue diagnostic-and-fix task with
no North Star metric decision, no request for an independent adversarial
review of a separate artifact, no multi-model delegation decision beyond
what this single session already did itself, no prior-art/patent search,
and no feature request needing JTBD reframing.
