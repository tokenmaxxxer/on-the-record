---
issue: 2893
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: cf7ee7d7:directive_assembly.py, cf7ee7d7:docs/handbooks/skill-verdict-obligation.md, cf7ee7d7:gates/record_lint.py, cf7ee7d7:on-the-record/gates/record_lint.py, cf7ee7d7:on-the-record/hooks/skill-verdict-guard.sh, cf7ee7d7:test/test_skill_verdict_guard_zero_invocation_signal.py
type: verification-record
breaking: false
verdict: tests-confirmed, two-acceptance-criteria-gaps-found
loop_state: landed
upstream:
  - path: PR #2898 (issue-2893/diagnose-first-6a58e6a9)
    sha: cf7ee7d749b3eb3ef89bb358ab0d65d3dc1d7ec5
  - path: cf7ee7d7:docs/issue-2893/reports/diagnose-first-6a58e6a9.md
    sha: cf7ee7d749b3eb3ef89bb358ab0d65d3dc1d7ec5
skill-verdict: work-in-english — applied: invoked; the SKILL.md content was loaded via the Skill tool this session before any file was written. All code, diffs, this record, and commit/PR text are in English; this session's final user-facing chat summary alone is in Korean, per the skill's own policy for a Korean-communicating session.
other mounted skills: not triggered — this is a read-only audit-and-record task (checking out a branch, running existing tests, reading a diff), with no multi-module structure decision, no adversarial review of a separate artifact needing a distinct reviewer identity beyond this role itself, no growth-metric or JTBD framing question, and no prior-art search.
---

# issue-2893 — independent-verification-1 record

## What was done

canonical: `gh issue view 2893` (full body) and `gh pr view 2898 --json title,body,commits,files,state,mergeable` — read the issue's acceptance criteria and the subject PR's description, both commits, and file list before checking out the branch.

Checked out `issue-2893/diagnose-first-6a58e6a9` (tip `cf7ee7d7`) directly and read the full PR diff (`gh pr diff 2898`, 733 lines, `derived: wc -l /tmp/pr2898.diff` — result: `733 /tmp/pr2898.diff`) end to end, plus the entire new record `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (340 lines).

Independently re-ran, rather than trusted, the PR body's numeric claims:

1. New test file — derived: `python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q -o addopts=""` on `cf7ee7d7` — result:
   ```
   .......                                                                  [100%]
   7 passed in 0.41s
   ```
   Matches the PR body's "7 passed" exactly.

2. Full suite, no new failures — derived: `python3 -m pytest . -q -o addopts=""` on `cf7ee7d7` — result:
   ```
   17 failed, 654 passed, 3 xfailed in 66.96s (0:01:06)
   ```
   Then the same command on `main` (`git checkout main`) — derived: `python3 -m pytest . -q -o addopts=""` on `main` — result:
   ```
   17 failed, 651 passed, 3 xfailed in 64.53s (0:01:04)
   ```
   The `short test summary info` block was identical between the two runs (same 17 test IDs, e.g. both runs' summaries include `FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace` and `FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present` as the first and last lines on both branches) — this is pre-existing `main` breakage, not something this PR introduces. `654 - 651 = 3` is exactly the 3 new test methods added in `ZeroInvocationRecordSummaryTest`. Confirms the PR body's "654 passed, 17 failed (identical failing-test-name set to origin/main, no new failures, none fixed)" claim.

3. Packaged-copy byte-identity — derived: `diff gates/record_lint.py on-the-record/gates/record_lint.py` on `cf7ee7d7` — result: empty (no output, exit 0), confirming the two copies of `zero_invocation_summary_check` really are byte-identical as the record claims.

All three re-derivations match the PR's own numbers.

## Why

### Acceptance criterion 1 ("root cause named from the two sessions' logs, not inferred") — the PR's own record discloses it did not meet this as stated

canonical: `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` lines under "Root cause, from the two sessions' own evidence", quoted verbatim:

```
unverifiable: the two incident sessions' own transcripts — they were
spawned against a different (downstream) target repository's own issue
numbers, not this repo's; no local session log matches (checked: `ls
~/.tokenmaxxxer/work/ | grep -i "issue-710\b\|issue-711\b\|blueprint"` —
result: no output, those workspaces have already aged out of local
retention). This session's diagnosis is therefore built from the issue's
own quoted evidence plus this repo's current code and its own prior art,
not from reading the incident transcripts directly, and says so rather
than presenting inference as observation.
```

The issue's own acceptance line reads: "Root cause named from the two sessions' logs, not inferred" / check: "the log excerpts and the derivation in the implementation record". No log excerpts from the #710/#711 incident sessions appear anywhere in this PR — the quoted paragraph above is the record's own admission that the transcripts were unavailable and the diagnosis was instead built by code-reading (`spawn.py`'s `skills_mounted` condition, the #1960 remeasurement table, `implementation-blueprint`'s own trigger text) plus the issue body's own summary. derived: `gh issue view 710 --repo tokenmaxxxer/on-the-record && gh issue view 711 --repo tokenmaxxxer/on-the-record` (run this session, independently checking whether either incident is reachable from this repo) — result:
```
#710: MERGED docs-only survey/proposal PR, unrelated to skill invocation
#711: CLOSED "spawn bootstrap latency", unrelated to skill invocation
(neither is the #710/#711 incident issue #2893 describes -- both
incidents happened in a downstream target repo, outside this repo)
```

This is disclosed honestly in the subject's own record (marked `unverifiable:`, listed as its own open finding) rather than hidden, but acceptance criterion 1 as literally written is not satisfied by what this PR ships.

### A must-not clause is violated: the injected directive grew, and the delta is never stated

canonical: this session's own `ast.literal_eval` extraction of `_SKILL_VERDICT_PROSE` from `directive_assembly.py` on both branches, run this session —
```
old (main):        907 bytes
new (cf7ee7d7):    1460 bytes
delta:             +553 bytes (+61%)
```
The issue's third must-not reads: "It must not grow injected directive bytes without stating the delta." `grep -n -i "byte\|delta" /tmp/pr2898.diff` (run this session against the full PR diff) surfaces only unrelated uses — "byte-identical" describing the two `record_lint.py` copies and "byte-unaffected" describing the zero-mounted no-op path in `zero_invocation_summary_check`'s own docstring — the `_SKILL_VERDICT_PROSE` growth itself is never measured or reported anywhere in the PR body, the two commit messages, or the new record. This +553-byte growth exceeds the 439 bytes the issue itself cites as the pre-existing cost this issue is about ("the ~439 bytes it adds to the injected directive"). Whether +553 bytes is an acceptable price is not this record's call to make unilaterally — the point is it was never stated for anyone to judge, which is the literal must-not.

### Acceptance criterion 2 (spawn a real session, count Skill calls before/after) — met, with a disclosed simplification

canonical: `docs/issue-2893/reports/diagnose-first-6a58e6a9.md`, "Live reproduction" section — 4 real `claude -p` sessions (not through `spawn.py`'s full workspace/branch/PR machinery — an ad hoc reproduction, matching stated precedent in `docs/issue-1960/reports/implementation.md`) with `implementation-blueprint` mounted, on a task the skill's own trigger explicitly excludes (a single function + test). All 4 sessions produced 0 Skill calls before and after the change, which the record identifies as expected (the fix touches record verification, not invocation logic) rather than a claimed fix to the underlying 0-invocation pattern — consistent with the issue's own framing that a selection outcome is a legitimate answer. This session did not re-run that live reproduction itself (it requires fresh model calls with hand-assembled system prompts, outside this audit's own scope), so this criterion is accepted on the subject record's own description plus the `implementation-blueprint` trigger text this session read directly (canonical: `/home/jwjung/skill-registry/skills/implementation-blueprint/SKILL.md`, matching the exclusion the subject record quotes), not independently re-executed.

### The must-not-be-a-per-turn-reminder and must-not-be-mandatory clauses hold

canonical: `on-the-record/hooks/skill-verdict-guard.sh` as changed in `cf7ee7d7` (read in full via `gh pr diff 2898`), the hunk starting `if not invoked:` —
```
if not invoked:
    zero_extra = []
    if record_lint is not None:
        rel, record_text = _resolve_record_path()
        if rel is not None:
            zero_extra = record_lint.zero_invocation_summary_check(record_text, mounted)
    finish(zero_invocation_notice(mounted), *zero_extra, reminder)
```
This sits inside the pre-existing `if not invoked:` branch of a Stop-hook script (fires once per session at session end, not per-turn — the whole script is gated to the Stop event by its surrounding harness contract, unchanged by this PR) and its output is always passed through `finish()`, which this session confirmed (by reading every `finish()` call site in the diff) never sets `decision: "block"` — only `additionalContext`. A session that genuinely finds nothing applicable still does nothing with the skill; it only has to say so once. Both must-nots hold as designed.

## What did not work

None in this verification session's own process (checkout, diff read, the three re-derivations in "What was done" above) — see that section's own `derived:`/`canonical:` tags. The two gaps below are properties of the reviewed deliverable (PR #2898), not of this record's own process, so they are logged under "Open findings" rather than here.

## Upstream basis

- PR #2898 (`issue-2893/diagnose-first-6a58e6a9`, tip `cf7ee7d7`) — the deliverable under review; full diff read via `gh pr diff 2898`.
- `docs/issue-2893/reports/diagnose-first-6a58e6a9.md` (same commit) — the subject's own implementation record, read in full and checked claim-by-claim above.
- `gh issue view 2893` — the issue's own acceptance criteria and must-not clauses, quoted verbatim where checked above.

## Open findings

- **Acceptance criterion 1 not satisfied as literally written**: derived: `gh issue view 710 --repo tokenmaxxxer/on-the-record && gh issue view 711 --repo tokenmaxxxer/on-the-record` (run this session) — result:
  ```
  #710: MERGED docs-only survey/proposal PR, unrelated to skill invocation
  #711: CLOSED "spawn bootstrap latency", unrelated to skill invocation
  (neither is the #710/#711 incident issue #2893 describes -- both
  incidents happened in a downstream target repo, outside this repo)
  ```
  The diagnosis this PR ships is built from code-reading and prior art, not from the two named incident sessions' own logs, per the subject record's own `unverifiable:` admission quoted in "Why" above. Resolution path: none currently exists inside this repo (the incident transcripts live in a downstream target repo outside this repo's or this session's reach) — a future session with access to that repo's session logs could close this by re-deriving the diagnosis from the actual transcripts.
- **Must-not violated: undisclosed +553-byte growth in the injected `_SKILL_VERDICT_PROSE` directive**: canonical: the "A must-not clause is violated" subsection in "Why" above, with the `derived:` byte counts quoted there (907 → 1460 bytes, +553). Resolution path: a follow-up commit stating the delta (in the PR body, the record, or a code comment near `_SKILL_VERDICT_PROSE`) would close this; whether +553 bytes is an acceptable price is a judgment this record does not make unilaterally.
- Both gaps are transparency/completeness gaps against the issue's stated acceptance text, not correctness bugs in the shipped mechanism itself — the shipped `zero_invocation_summary_check`, the Stop-hook wiring, and the 3 new tests all independently re-verified as matching the PR's own claimed numbers, per the `derived:` pytest re-runs in "What was done" above.

## Next steps

None further from this role; `loop_state: landed` (see frontmatter). Whether to open a follow-up addressing the two "Open findings" above is a decision for the subject's own author or a future session, not this verification record.
