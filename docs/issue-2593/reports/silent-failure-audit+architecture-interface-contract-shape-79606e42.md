---
issue: 2593
role: silent-failure-audit+architecture-interface-contract-shape-79606e42
author: silent-failure-audit+architecture-interface-contract-shape-79606e42
skills: silent-failure-audit (skill-repository(297e350)), architecture-interface-contract-shape (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: gates/spawn_on_pr.py
    sha: 73daf57b64b77bc4d5479294cbca01cb48225b79
  - path: board.py
    sha: 73daf57b64b77bc4d5479294cbca01cb48225b79
type: audit-and-fix
breaking: false
verdict: 3 of 4 acceptance bullets already Present (landed by #2609/#2615/#2623 before this session); bullet 3 (board rendering) was Absent and is fixed here; a second, previously-unreported live defect in bullet 4's own mechanism is also fixed here
loop_state: landed
upstream:
  - path: docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md
    sha: same-commit
  - path: docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-ded46e17.md
    sha: same-commit
  - path: docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-b3934eed.md
    sha: same-commit
---

# issue-2593 — silent-failure-audit+architecture-interface-contract-shape-79606e42 record

## What was done

canonical: this record's factual claims are grounded in direct `Read`/`Bash`/`grep`/interactive-Python execution against this repo's own worktree this session (base commit `de8b7ffe`; code committed this session at `73daf57b`), `gh issue view 2593 --comments`, `gh pr view 2605/2609/2615/2623` -- all executed live this session unless marked otherwise.

The issue's own body warns that an earlier "removal" on this exact issue was later found by audit to be a rename (issue #2626/#2627), and that #2600/#2601/#2609/#2615/#2623/#2628/#2610/#2651 landed since the issue was filed and must not be assumed to satisfy any bullet. Each of the four acceptance bullets was re-derived from scratch this session. Three came back genuinely satisfied by prior work; one was Absent and is fixed here; fixing the fourth also surfaced a second, previously undetected live defect in the mechanism #2609 built, fixed in the same commit (`73daf57b`).

### Bullet 1 — no closed set decides spawn/merge (`PR_TRIGGERED_RECORD_KINDS`)

derived: `grep -rn 'PR_TRIGGERED_RECORD_KINDS' --include=*.py .` — 0 hits, this session, before any edit.

Verdict: **Present.** Landed by PR #2615 (issue #2609), which replaced the closed two-name tuple with `spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS = 2` (a count) plus `verifies_subject: true` self-declaration. No edit needed for this bullet.

### Bullet 2 — the load-bearing bullet: merge still refuses for missing independent verification, mechanism named, demonstrated live

Verdict: **Present**, demonstrated live against this issue's own subject board, which at execution time held 2 records (this design doc plus this record's own skeleton), neither self-declaring `verifies_subject: true`:

derived: `python3 gates/merge_gate.py 999999 issue-2593 --repo .` (this session, live, exit code 1):
```
거절: PR #999999 (issue-2593)
  - check-runner 코멘트를 찾을 수 없다
  - required_verification_missing(): 독립 검증 기록이 부족하다 -- 0/2개 확인됨 (2개 더 필요)
```

Mechanism named: `gates/merge_gate.py::evaluate()` (`gates/merge_gate.py:310-382`) calls `gates/merge_gate.py::required_verification_missing()` (`gates/merge_gate.py:178-213`), which calls `gates/spawn_on_pr.py::verifying_record_count()` (`gates/spawn_on_pr.py:67-89`) against `spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS = 2` (`gates/spawn_on_pr.py:43`), a plain integer threshold. `main()` (`gates/merge_gate.py:315-341`) prints `거절: PR #{pr} ({subject})` and each reason, exit code 1, exactly reproduced above. canonical: `gates/merge_gate.py` and `gates/spawn_on_pr.py`, read directly this session at the line ranges cited. Landed by PR #2615/#2623 (issue #2609); no edit needed for the refusal mechanism itself.

### Bullet 3 — a consumer cannot mistake a historical record's filename for a spawnable name, and can find real skill vocabulary from what the system shows it

Verdict: **Absent before this session's fix, Present after.** PR #2605's own design doc explicitly scoped this as a separate "Issue B" (board.py bracket-label provenance marker) that no follow-up issue was ever filed to build — #2609/#2615/#2623 only built "Issue A" (the merge-gate mechanism, bullets 1/2/4). canonical: `docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md`, "Next steps" → "Issue B", read this session.

Reproduced live, before this session's `board.py` edit, byte-identical to the issue body's own quoted incident:

derived: `python3 spawn.py 2>&1 | grep -A1 "^subject: issue-1005$\|^subject: issue-103$"` (this session, before the fix):
```
subject: issue-1005
  [implementation] loop_state: landed   verdict: pass
--
subject: issue-103
  [coding] loop_state: landed
```

Fixed in `board.py:808,819` (commit `73daf57b`; `gates/spawn_on_pr.py` untouched for this bullet): every bracket line now reads `[record: <name>]`. Re-run after the fix:

derived: same command, this session, after the `board.py` edit:
```
subject: issue-1005
  [record: implementation] loop_state: landed   verdict: pass
--
subject: issue-103
  [record: coding] loop_state: landed
```

Second half (where a session finds real skill names): already Present, not touched this session. canonical: `python3 spawn.py --help` output (`--skills` flag help text, names the four resolution sources: skill-repository checkout, installed plugins' `skills/`, `~/.claude/skills`, target repo `.claude/skills`) and `on-the-record/commands/consult.md:31-33` ("큐레이션된 목록은 없다: 실제 이름은 skill-repository 체크아웃의 디렉터리 목록이다" plus the literal `ls` command), both read directly this session. A curated name list is deliberately not reintroduced into `board.py` itself — the #2139 consult (quoted in the issue body) already ruled that shape out once.

### Bullet 4 — no live code path branches on a hard-coded historical role name

derived: `grep -rnE '"(implementation|coding)"' --include=*.py gates/ *.py` (this session, before the fix):
```
gates/skip_eligibility.py:85:# deleted here, not just their two dead `"implementation"` fallback
gates/gates.py:695:    ("implementation")에서만 실제로 발동했다(나머지 43개는 버킷 dict라
gates/spawn_on_pr.py:180:    `subject_board.get("implementation", {})` lookup silently returns an
gates/spawn_on_pr.py:195:        if kind_field == "implementation" or (kind_field is None and name == "implementation"):
```

`gates/spawn_on_pr.py:195` was live code, not a comment — `subject_deliverable_record()`'s hard-coded `kind_field == "implementation" or (kind_field is None and name == "implementation")` branch, present since before this issue was filed (the issue body's own Ask section names this exact function at its then-line-number 125). Verdict at this point: **Absent** — one live hit, not the bullet's own empty-state ("remaining hits are comments or documentation citations only").

Fixed in `gates/spawn_on_pr.py::subject_deliverable_record()` (commit `73daf57b`; see "Why" for the design). Re-run after the fix:

derived: same grep, this session, after the `gates/spawn_on_pr.py` edit:
```
gates/skip_eligibility.py:85:# deleted here, not just their two dead `"implementation"` fallback
gates/gates.py:695:    ("implementation")에서만 실제로 발동했다(나머지 43개는 버킷 dict라
gates/spawn_on_pr.py:180:    match `kind_field == "implementation" or (kind_field is None and name
gates/spawn_on_pr.py:181:    == "implementation")`, a hard-coded historical role name the #2593
gates/spawn_on_pr.py:184:    matched the equally-historical `"coding"` deliverable name, so a
```

All remaining hits are inside comments/docstrings (one is this function's own new docstring, citing the removed code for history), matching the bullet's own empty-state clause. Verdict: **Present** after the fix.

### The second defect bullet 4's fix surfaced: a live self-verification-guard gap, not previously reported

canonical: interactive Python this session against this repo's real `spawn.board(Path('.'))` (`import spawn_on_pr, spawn; b = spawn.board(Path('.'))`), before the fix.

derived: counting `spawn_on_pr.subject_deliverable_record(sb)` results over every `(subj, sb)` in `b.items()`, this session:
```
matched (legacy "implementation" name-match resolves a deliverable): 550 / 633 subjects
unmatched (returns (None, {})): 83 / 633 subjects
```
Of the 83 unmatched (derived: same script, partitioning on whether any record in `sb` has `kind == "coding"` or filename `"coding"`): 21 are pre-#2560 subjects whose deliverable used the equally-historical `"coding"` name/kind (never matched by this function in any version) and 62 use the modern skill-slug naming convention (issue #2560/#2610) — every subject whose deliverable landed after the role→skill rename.

`gates/merge_gate.py::required_verification_missing()` (`:205-206`) reads `subject_deliverable_record()`'s result to get `subject_author`, which `verifying_record_count()` (`gates/spawn_on_pr.py:86`) uses to exclude records authored by the deliverable's own author from the independent-verification count — the self-verification guard. `subject_deliverable_record()`'s own docstring (pre-fix, quoted under "Bullet 4" above) documents that `subject_author=None` "skips the guard" — pre-existing, accepted, intentional fail-open behavior for the "no deliverable landed yet" case. The defect: for all 83 unmatched subjects, `subject_author` was silently `None` even when a deliverable HAD landed for 62 of them, so the self-verification guard never fired for any of those 62 — a session could self-author two `verifies_subject: true` records under its own subject and satisfy `REQUIRED_INDEPENDENT_VERIFICATIONS` without independent verification ever occurring. This directly touches the acceptance section's `must not:` clause ("Do not remove the pre-merge independent-check obligation, or weaken it to advisory") for the subset the old hard-coded match could never reach.

derived: `python3 -m pytest test/test_subject_deliverable_record_name_free.py -q` (this session, after the fix, against code committed at `73daf57b`) — 4 passed, including `test_self_authored_verifying_records_are_excluded_for_modern_slug`, which reproduces this exact scenario end-to-end (a modern-slug deliverable, two self-authored `verifies_subject: true` records) and asserts the post-fix `deficit == 2` (still required, correctly excluding both self-authored records) rather than the pre-fix `0` (silently satisfied) this session confirmed inline before writing the fix.

Of the 550 subjects the pre-fix hard-coded match resolved, 7 currently-`OPEN` issues rely on it for self-verification-guard precision today. derived: `gh issue list --repo tokenmaxxxer/on-the-record --state open --limit 300 --json number`, cross-referenced against the 550 matched subjects, this session — result: `1725, 2079, 2092, 2152, 2153, 2159, 2193`.

## Why

canonical: this section's design reasoning is grounded in the direct reads/execution cited under "What was done," plus `gates/spawn_on_pr.py::subject_deliverable_branch()` (`:200-224`), read directly this session for its already-established name-free pattern.

### `subject_deliverable_record()`'s fix follows an already-accepted precedent in the same file

canonical: `gates/spawn_on_pr.py::subject_deliverable_branch()` (`:200-224`) and `gates/spawn_on_pr.py::subject_deliverable_record()` (`:177-217` post-fix), both read directly this session at commit `73daf57b`.

`subject_deliverable_branch()` (issue #2575, unchanged by this session) already resolves the subject's deliverable *branch* without matching any name: it takes the single branch under the subject's PR-index prefix that does not match `_VERIFICATION_SLOT_RE` (a structural pattern — "does this slug look like a generic verification slot," issue #2628 — not a role-name enumeration), and refuses to guess (`None`) when zero or more than one candidate exists. `subject_deliverable_record()`'s old hard-coded `"implementation"` match was the one place in this file not yet brought forward to this pattern when #2609 rewrote everything else around it.

The fix applies the identical shape to records instead of branches: the deliverable is the single record NOT self-declaring `verifies_subject: true` (issue #2609's own field); zero or more than one candidate → `(None, {})`, the same conservative contract this function already returned for "not found." No `kind:` value, filename, or skill name participates — consistent with the "does anything still validate identity against a closed set" test from #2548 the issue's Ask section applies to the surrounding code.

**Operator ruling applied** (per this session's spawning instructions, restating the 2026-08-27 ruling already live in `gates/spawn_on_pr.py:50-51`'s own comment on the AUTO_SPAWN_ROLES removal, read directly this session): a capability that cannot be provided without matching a hard-coded identity name is dropped outright, not relocated or reshaped. What stops working, plainly: for subjects whose `reports/` directory holds more than one non-verifying record with no `verifies_subject` marker to disambiguate them — chiefly older, closed subjects predating #2609 — `verifying_record_count()`'s self-verification guard degrades to its already-documented `subject_author=None` fail-open behavior (skip the same-author exclusion, still require the same count of 2) instead of firing precisely. The base independent-verification-COUNT obligation (bullet 2, the load-bearing one) is unaffected either way — only the same-author exclusion loses precision, and only for the measured 7 currently-open subjects that relied on the removed literal match (see "What was done"). The alternative (keeping the hard-coded `"implementation"`/`"coding"` match as a fallback behind the new structural check) was considered and rejected: bullet 4's own empty-state clause requires zero live non-comment hits, and the issue's Ask section explicitly rejects "reachability is not the standard being applied" as an excuse to keep a hard-coded name around (quoted verbatim regarding `skip_eligibility.py`'s dead fallbacks, applied here to a live one).

### `board.py`'s fix follows the shape the design (#2605) already specified, not a new invention

canonical: `docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md`, "Why" → "Board.py (Step B)", read this session.

That design doc explicitly proposed "an inline, per-line provenance marker directly in the format string itself — e.g. `[record: X]` instead of bare `[X]`" and ruled out the two shapes the #2139 consult already rejected (dropping the bracket entirely; relabelling while still printing bare role strings). This session's fix is exactly that proposal, applied verbatim to both bracket sites in `board.py:808,819` — zero change to the underlying `lease_slugs`/`_skill_axis_report_names` data flow, confirmed by re-running the full `python3 spawn.py` board dump after the edit (derived: full-output diff against the pre-edit capture, this session — only bracket text changed).

### Skill verdicts

canonical: Skill-tool output for `silent-failure-audit` and `architecture-interface-contract-shape`, both loaded directly in-session this session, applied to the diff described above.

skill-verdict: silent-failure-audit — applied: invoked; audited `subject_deliverable_record()`'s `(None, {})` return path end to end — traced from the catch point (ambiguous/no-match) through both call sites (`gates/merge_gate.py:205-206`, `gates/spawn_on_pr.py:362-364,791-793`) to the downstream consequence (self-verification guard silently skipped, quantified under "What was done" above). Found this consequence pre-existing and already documented for the "nothing landed yet" case, but reachable far more often after the fix widens the structural check's ambiguity trigger (any subject with 2+ non-verifying records, not just the old function's blind spot). Classified as Silently Absorbed in the sense that no reason string or log line currently surfaces "self-verification guard skipped for this subject" to an operator reading a merge evaluation's output — recorded as Open Finding 1 below rather than fixed in this session, since building that surfacing is separate-issue-sized work outside this issue's Ask/Scope.
skill-verdict: architecture-interface-contract-shape — applied: invoked; used rule 12 (hide the likely-to-change decision behind a stable interface) to keep `subject_deliverable_record()`'s public contract — `(slug: str | None, frontmatter: dict)`, `None` meaning "not found or ambiguous" — byte-identical while replacing its internal resolution strategy, so neither of its two call sites needed any change (confirmed: this commit's diff touches zero lines outside `gates/spawn_on_pr.py`/`board.py`/`test/`, derived: `git show 73daf57b --stat`); used rule 8 (Open Host Service / Published Language) to treat `board.py`'s printed bracket line as the de facto contract a consumer orchestrator reads, and to make that contract's own semantics explicit (`record:`) rather than leaving them to be inferred ad hoc, which is what produced the reported mistyping incident in the first place.

## What did not work

None.

## Upstream basis

canonical: all three paths below were opened directly via the `Read`/`gh pr view` tools this session.

- `docs/issue-2593/reports/architecture-module-boundary-definition+architecture-decomposition-strategy-386ff408.md` — the design PR #2605 this session builds on; source of the `board.py` bracket-marker shape and the 3-issue (A/B/C) sequencing this session found only "Issue A" (bullets 1/2/4) had been built from.
- `docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-ded46e17.md` — Issue A's initial build (PR #2615): the count-based `REQUIRED_INDEPENDENT_VERIFICATIONS`/`verifies_subject` mechanism this session verified live and left unchanged.
- `docs/issue-2609/reports/architecture-interface-contract-shape+silent-failure-audit-b3934eed.md` — Issue A's follow-up (PR #2623): scaffolds `verifies_subject: false` into every record via `write_record_skeleton()`, which this session's new tests (`test/test_subject_deliverable_record_name_free.py`, `test/test_board_bracket_provenance.py`, both committed this session at `73daf57b`) exercise directly rather than hand-building frontmatter dicts.

## Open findings

canonical: this session's own execution, cited inline per finding.

1. **Self-verification-guard-skipped is not surfaced to an operator.** `verifying_record_count()`'s `subject_author=None` fail-open path (pre-existing, and now reachable more often — see "What was done") produces no visible reason string in `gates/merge_gate.py::evaluate()`'s output when it fires — a merge can be `allowed: True` on the strength of 2 `verifies_subject: true` records without anyone being told the same-author exclusion wasn't checked. Resolution path: a follow-up issue scoped to `gates/merge_gate.py::evaluate()`'s reason-list construction, adding a non-blocking informational reason when `subject_deliverable_record()` returns ambiguous (more than one non-verifying candidate) rather than "nothing landed yet" (zero candidates) — the two cases are currently indistinguishable to callers and would need `subject_deliverable_record()`'s contract to expose the distinction, itself a small interface change per rule 12 that should get its own proposal rather than ride in on this issue's write set.
2. **7 currently-open subjects lose self-verification-guard precision** (issues 1725, 2079, 2092, 2152, 2153, 2159, 2193 — measured this session, see "What was done") because their deliverable record still carries the legacy `"implementation"`/`"coding"` name/kind and this session's fix no longer matches on it. None of these subjects' own historical records are touched (the `must not:` clause is honored — this is a change in a live gate function, not a rewrite of any `docs/issue-*/reports/` file). If any of these 7 subjects still needs a new PR merged, its self-verification guard now runs in the same fail-open mode every modern-slug subject already ran in before this fix (net: more subjects now share one consistent, documented behavior, rather than a name-matched majority and an unmatched minority behaving differently). No action needed unless a future audit wants guard precision restored for this shrinking legacy-named subset specifically.
3. **The consumer-visible "role"/"역할" vocabulary purge (PR #2605's design doc "Issue C") remains unbuilt**, but confirmed out of scope for this issue's own acceptance bullets: issue #2600 ("blocked on #2593") already exists as that follow-up, scoped across both `on-the-record` and `tokenmaxxxer-core` outside `docs/`. canonical: `gh issue view 2600`, read this session. This session's bullet-3 fix (the `board.py` provenance marker) satisfies bullet 3's first half; the second half (where a session finds real skill names) was independently confirmed already Present via `spawn.py --skills --help` and `consult.md` (see "Bullet 3" above), so issue #2600 remains the correct home for the broader word sweep and this session does not duplicate it.

## Next steps

None — `loop_state: landed`. Issue #2600 (vocabulary sweep) and the Open Findings above are follow-up work items for future issues, not remaining work on this one.
