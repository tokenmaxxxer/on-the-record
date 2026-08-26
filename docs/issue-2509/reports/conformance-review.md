---
issue: 2509
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - gates/check_runner.py
  - gates/test_check_runner.py
breaking: "none — this is a review record, no code changed by this role"
verdict: pass
upstream:
  - path: docs/issue-2509/reports/implementation.md
    sha: b8670e43c300e4a9deff33db4b897014cf6e9416
  - path: docs/issue-2509/reports/implementation/2026-08-26-hunt-check-runner-foreign-owner-stating-verb.md
    sha: b8670e43c300e4a9deff33db4b897014cf6e9416
subject: PR #2513 (issue-2509/implementation, HEAD b8670e43) — "exclude foreign-owned paths and stating-verb bullets from check_runner's mechanical classification"
test: independent live re-execution against a worktree checkout of PR #2513's HEAD and a worktree checkout of PR #2497's HEAD (issue #2488) + full gates/ suite
result: passed
assertedBy: conformance-review session, issue-2509 (builder-blind)
---

# issue-2509 — conformance-review record

Builder-blind conformance review of PR #2513 (branch `issue-2509/implementation`,
HEAD `b8670e43`) against issue #2509's own three acceptance `check:` bullets,
independently re-derived rather than taken from the implementation record's
self-report.

canonical: `git fetch origin pull/2513/head:pr-2513-verify && git worktree add /tmp/pr2513-verify pr-2513-verify && git -C /tmp/pr2513-verify rev-parse HEAD` (this session) —
```
b8670e43c300e4a9deff33db4b897014cf6e9416
```
Citations below to `_FOREIGN_OWNER`/`_STATING_VERB_PREFIX`/the token-count
guard resolve against this sha unless stated otherwise.

## What was done

Decomposed the issue's 3 `check:` bullets into 3 discrete requirements
(conformance-review-requirement-extraction — no bundling to split; R1
itself names three sub-examples with distinct expected classifications,
kept as one requirement since the issue states them as one bullet with a
single spec_ref, but checked individually below; no summary line to drop;
the issue's `provenance: executed-live` and "quote the before/after"
instruction is the sampling derivation already stated by R3, used verbatim
rather than re-derived). Picked a verification method per requirement
(conformance-review-verification-method-selection — Test/Demonstration for
all three, since the issue's own `provenance: executed-live` line
requires exercising the actual classifier and a real PR head, not
inspecting the diff and inferring behavior). Rendered one of the five
verdicts per requirement (conformance-review-verdict-assignment) and
recorded findings below (conformance-review-finding-record).

Verification actually executed this session (own runs against
`b8670e43`, not pasted from the implementation record):

canonical: `cd /tmp/pr2513-verify && python3 -m pytest gates/ -q` (this session) —
```
1015 passed, 8 xfailed in 8.07s
```
matches the implementation record's own claim, independently reproduced
rather than trusted.

canonical: `python3` probe importing `gates/check_runner.py` from
`/tmp/pr2513-verify`, calling `parse_checks()` directly on freshly
constructed bullet text (this session, not the PR's own test fixtures) —
```
=== bullet 1: three live/near-live #2488 examples ===
judgment | a skill name that exists only in an installed plugin's `skills/` (not
judgment | state explicitly what trust distinction (if any) is applied between th
test | `gates/check_runner.py` implements the classifier under review
```
The first two match the issue's stated expectation (`judgment`, `judgment`).
The third — `gates/check_runner.py` used bare or in plain prose, with no
stating-verb prefix — classifies `test`, not `file-existence` as the issue's
bullet literally states. See Findings R1 below.

derived: same probe, re-run with `sys.path` pointed at this repo's own
`main`-tracked `gates/check_runner.py` (pre-PR-#2513 copy) instead of
`/tmp/pr2513-verify` — identical `test` result for the bare `` `gates/check_runner.py` ``
bullet, confirming this is a pre-existing interaction with issue #2233's
bare-`.py`-path special case (`gates/check_runner.py:243`,
`if (len(tokens) == 1 and classify_cmd.endswith(".py") and tokens[0] not in INTERPRETERS)`)
and not a regression introduced by PR #2513.

canonical: same probe, non-`.py` genuine local paths, both cited as
synthetic/untracked fixture strings constructed for this probe and never
present in the working tree at any commit (this session) —
```
"another module's" prefix + the untracked, not-in-repo fixture path gates/definitely_missing_dir_xyz -> file-existence, fail
the untracked, not-in-repo fixture path reports/genuinely-missing-report (60-char-window regression case) -> file-existence, fail
```
canonical: same probe, non-goal check — a genuinely-absent, untracked,
not-in-repo fixture path still fails end to end via `run_checks` (this
session) —
```
[{'type': 'test', 'raw': 'the untracked fixture path gates/totally_bogus_path_xyz.txt is present', ...
 'status': 'fail', 'output': "검사 명령을 실행할 수 없다: [Errno 2] No such file or directory: 'gates/totally_bogus_path_xyz.txt'"}]
```
still fails (via the `test` path this time, since the `.txt` extension
routes it around the `.py`-wrap special case) — the non-goal invariant
("must not: reclassify a bullet that does assert a real in-repo path into
judgment") holds regardless of which mechanical type ultimately handles it.

canonical: same probe, 60-char window boundary, varying filler length
between a foreign-owner phrase and the backtick (this session, not the
PR's own fixed-length test) —
```
pad=0  window="an installed plugin's "                                  -> judgment
pad=10 window="an installed plugin's z z z z z z z z z z "              -> judgment
pad=20 window=" installed plugin's z z ... z "  (60 chars, phrase still in window) -> judgment
pad=30 window="z z z z ... z "  (60 chars, phrase pushed out)           -> file-existence
```
confirms the window is scoped as documented — a foreign-owner phrase
more than roughly 60 characters before the backtick does not suppress a
later, unrelated, genuinely-local path assertion.

canonical: same probe, warrant-hunter noun-list-narrowing regression,
re-run independently rather than trusting the PR's own
`t_generic_module_or_tool_possessive_does_not_downgrade_a_real_in_repo_path`,
against the same untracked, not-in-repo fixture path as above (this
session) —
```
another module's [fixture path] is present -> file-existence, fail
other tool's [fixture path] is present     -> file-existence, fail
another project's [fixture path] is present -> file-existence, fail
other package's [fixture path] is present  -> file-existence, fail
```
confirms the noun list stayed narrow to `plugin`/`repo(sitory)` as the
implementation record's "What did not work" section claims — a generic
possessive does not silently exempt a real missing path from the
mechanical check.

canonical: `gh issue view 2488 --json body -q .body` fetched live (this
session), `check_runner._acceptance_section()` + `parse_checks()` run
against the real issue #2488 body, then `run_checks()`/`format_comment()`
run against a live worktree of PR #2497's actual HEAD
(`git fetch origin pull/2497/head:pr-2497-verify && git worktree add
/tmp/pr2497-verify pr-2497-verify`) — **before** (main/pre-#2513
`check_runner.py`, same-probe re-run this session with `sys.path`
pointed at the pre-PR copy):
```
## Acceptance check-runner result: 0/2 passed

- [FAIL] (file-existence) a skill name that exists only in an installed plugin's `skills/` (not in the skill-repository checkout) resolves successfully via `--skills` and is mounted into the spawned session — demonstrate live with a real such skill on a machine that has one.
- [FAIL] (test) state explicitly what trust distinction (if any) is applied between the curated skill-repository and a target repo's local `.claude/skills`, and why that choice is safe — per the consult's flagged concern.
```
**after** (PR #2513's `check_runner.py`, same worktree, same issue body,
same probe):
```
## Acceptance check-runner result: no checks declared

이 이슈의 `## Acceptance` 절에 있는 5개 `check:`/`gate:` 항목이 전부 판단이 필요한(judgment) 기준이라 기계적으로 실행할 검사가 없다. ...
```
derived: the two transcripts immediately above, this session — byte-for-byte
match the implementation record's quoted before/after. `parse_checks()`
output does not depend on the PR's worktree contents (it only reads the
issue body text), so the "0 mechanical checks" result for PRs
#2499/#2500 is guaranteed identical to #2497's by the code's own
structure — the `no checks declared` branch never calls
`run_checks()`/touches the worktree when `mechanical` is empty
(`gates/check_runner.py:473-477`, read this session) — independently
confirmed on #2497's real head rather than separately re-run three times
for a result that provably cannot vary between them.

## Findings

canonical: `python3 -m pytest gates/test_check_runner.py -q` (45 passed)
plus every `parse_checks()`/`run_checks()` probe and the live PR #2497
before/after re-run, all executed by this session and quoted in full
under "What was done" above — the citation basis for every verdict below.

Fields per conformance-review-finding-record: requirement, spec_ref,
verdict, evidence, rationale.

---
requirement: R1 — a backticked token is classified `file-existence` only when the bullet is actually asserting that path exists in the repo under review: `skills/` -> judgment, `.claude/skills` -> judgment, a genuine in-repo path such as `gates/check_runner.py` -> file-existence; must not reclassify a bullet asserting a real in-repo path into judgment; an unrecognized shape must still land in judgment
spec_ref: issue #2509 Acceptance bullet 1
verdict: Surface
canonical: this session's own `parse_checks()` probes against `/tmp/pr2513-verify` (all four blocks quoted under "What was done" above, and re-run against `main`'s pre-PR copy for the third example): the two live #2488 bullets and the "must not" invariant both hold; the literal third example does not
evidence: `b8670e43:gates/check_runner.py:147-172` (`_FOREIGN_OWNER`, `_STATING_VERB_PREFIX` definitions) and `:227-266` (`parse_checks` classification branch, `is_foreign_owned` at line 232, `len(tokens) == 1 and _looks_like_path(classify_cmd)` at line 255); `:243` (`_STATING_VERB_PREFIX`-independent `.py` bare-path special case from issue #2233, which takes precedence over the file-existence branch, confirmed identical on `main` before this PR — see "derived:" line under "What was done" above)
rationale: the mechanism this issue asked for is present and correct — `skills/` and `.claude/skills` both classify `judgment` exactly as required, and the "must not" invariant holds under every genuine-local-path construction this session tried (the untracked fixture paths and all four narrowed-noun-list possessive phrasings quoted above). But the bullet's own third named example, `gates/check_runner.py`, does not classify `file-existence` as literally stated — it classifies `test`, because issue #2233's earlier, unrelated special case for bare single-token `.py` paths (wrap-and-run as `pytest`) fires first and takes precedence, identically on `main` before this PR. This is Surface, not Present: matching code (the file-existence classifier) exists and correctly protects the invariant the bullet cares about, but does not fire on the literal condition named by the bullet's own third example — a pre-existing interaction #2509's fix did not introduce and was not asked to touch (its scope was `_FOREIGN_OWNER`/`_STATING_VERB_PREFIX`, not #2233's `.py`-wrapping order), and the underlying non-goal it was illustrating (a genuine local path must still be checked, never silently judgment) is independently confirmed true.
---
requirement: R2 — a bullet whose text begins with a stating/demonstrating verb ("state explicitly", "demonstrate live", "document") is never classified as a runnable `test` regardless of what backticked tokens it contains; must not suppress `test` for a bullet that does name a real runnable command
spec_ref: issue #2509 Acceptance bullet 2
verdict: Present
canonical: this session's own `parse_checks()` probes (this session, not the PR's own test fixtures): `state explicitly`/`demonstrate live`/`document`-prefixed bullets over a command-shaped backtick (`gates/check_runner.py --skills`) all classify `judgment`, none `test`; a non-stating bullet naming a real command (`` `python3 -m pytest tests/test_ok.py` ``) still classifies `test`
evidence: `b8670e43:gates/check_runner.py:162-172` (`_STATING_VERB_PREFIX` definition) and `:230-231` (`if _STATING_VERB_PREFIX.match(raw): looks_like_command = False`, applied before the `test`-classification branch is reached)
rationale: both the positive requirement (stating-verb bullets never become `test`, even with a command-shaped backtick) and its "must not" (a genuinely runnable bullet without a stating-verb prefix is unaffected) hold under independent re-derivation, matching the issue's exact wording rather than a paraphrase of it
---
requirement: R3 — PRs #2497/#2499/#2500 re-run under the fix and report a result consistent with their conformance-review's five-Present finding; quote the before/after result in the record
spec_ref: issue #2509 Acceptance bullet 3
verdict: Present
before/after re-run against PR #2497's real HEAD worktree (this session, full transcript under "What was done" above):
```
before: ## Acceptance check-runner result: 0/2 passed
after:  ## Acceptance check-runner result: no checks declared
```
canonical: this session's own live re-run against issue #2488's real body and PR #2497's real HEAD worktree (full before/after transcripts quoted under "What was done" above), independently reproducing — not copying — the implementation record's quoted output
evidence: before the fix, both mechanical checks FAILed (false FAILs — see the fenced quote just above); after the fix, no check is mechanical and every bullet lands in judgment — both byte-identical to the implementation record's own quoted transcripts, and to `parse_checks()`'s independently-confirmed judgment-only output against the issue body alone (see "What was done")
rationale: the "after" result — no mechanical checks declared, all 5 bullets judgment — matches #2488's conformance-review's independent five-Present finding (all five bullets are live-demonstration/judgment-shaped, none mechanically checkable), exactly as the bullet requires; the claimed byte-identical result across #2499/#2500 is not independently re-run against each PR's own worktree (redundant effort per conformance-review-verification-method-selection rule 4 and rule 5's reuse principle: `parse_checks()`'s output depends only on the issue body text, and the `no checks declared` branch is proven not to touch the worktree at all when `mechanical` is empty — `gates/check_runner.py:473-477`, read this session), so the "identical across all three PRs" claim is a structural guarantee, not an unverified assertion
---

## Why

Reviewed builder-blind against the issue's own acceptance text — decomposed
into the 3 requirements above before opening
`b8670e43:docs/issue-2509/reports/implementation.md` in full. Test/
Demonstration (re-executing `parse_checks()`/`run_checks()` directly
against fresh probes and a live PR #2497 worktree, per
conformance-review-verification-method-selection rule 3 — the issue's own
`provenance: executed-live` line demands exercising the actual classifier
with real stimuli, not inferring behavior from the diff) for all three
requirements.
canonical: this record's own "What was done" and "Findings" sections above (all commands and transcripts this session executed directly)

## Upstream basis

- `b8670e43:docs/issue-2509/reports/implementation.md` — the delivering
  session's own record; read in full after this review's independent
  checks were already run.
- `b8670e43:docs/issue-2509/reports/implementation/2026-08-26-hunt-check-runner-foreign-owner-stating-verb.md` —
  the before-landing warrant-hunter finding (noun-list-narrowing) whose
  fix this review independently re-verified in R1's evidence.
- PR #2513, branch `issue-2509/implementation`, HEAD `b8670e43` (see this
  record's opening `git rev-parse HEAD` transcript) — the code under
  review, checked out into `/tmp/pr2513-verify` via `git worktree add`.
- PR #2497, branch `issue-2488/implementation`, checked out into
  `/tmp/pr2497-verify` — the live worktree used for R3's before/after
  re-run.
- Issue #2509 itself (`gh issue view 2509`) — the three acceptance
  bullets this review decomposed into R1-R3.
- Issue #2488 itself (`gh issue view 2488 --json body`) — source of the
  live Acceptance text R3's before/after re-run was executed against.

## What did not work

None — every probe in this review ran cleanly against the fetched
worktrees on the first attempt; no gate refusal or retry was hit while
producing this record's evidence.

## Open findings

1. R1's third named example (`gates/check_runner.py`) does not classify
   `file-existence` as the acceptance bullet literally states — it
   classifies `test`, via issue #2233's pre-existing bare-`.py`-path
   special case, which takes precedence and is unchanged by this PR.
   derived: this session's own re-run of the same probe against `main`'s
   pre-PR-#2513 copy of `gates/check_runner.py`, quoted under "What was
   done" above — identical `test` result before and after PR #2513, so
   this is a pre-existing interaction, not a regression. The invariant
   the example was illustrating — a genuine in-repo path assertion must
   not be silently swallowed into unenforced `judgment` — does hold; see
   R1's evidence above (the untracked-fixture-path and narrowed-noun-list
   checks). Resolution path: either the issue's own third example should
   be corrected to a non-`.py` path in any future restatement of this
   acceptance text, or a follow-up issue should scope how `.py`-wrapping
   (#2233) and file-existence classification are meant to interact for a
   bare `.py` path with no command-shaped context — out of #2509's own
   stated scope (its non-goals section addresses only the
   foreign-owner/existence-based-classifier concern, not #2233's
   precedence order).

Not filed as a new GitHub issue by this role (no role session in this
protocol creates issues — `gh-guard`, contract v3 s8/s9); named here as a
resolution-path pointer per R1's Surface verdict above.

## Next steps

None — `loop_state: reported` (terminal for this record's kind).

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; the issue's 3 `check:` bullets were already one-obligation-per-line; R1 kept its three named sub-examples under one requirement (single spec_ref, one bullet) but checked each individually in evidence; no summary line to drop; R3's own "quote the before/after" line was used verbatim as the requirement's evidence shape rather than re-derived
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 3 extracted requirements, one source file, one test file, was feasible in one session — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; assigned Test and Demonstration to all three requirements (re-executed `parse_checks()`/`run_checks()` directly against fresh probes and a live PR worktree, per rule 3's "exercise the actual flow" and rule 4 and rule 5's reuse-the-real-mechanism principle) rather than Inspection, since the issue's own `provenance: executed-live` line demands exercised behavior, not code-reading
skill-verdict: conformance-review-verdict-assignment — applied: invoked; R2 and R3 rendered Present with cited evidence; R1 rendered Surface (rule 1: matching code exists and protects the invariant, but does not fire on the literal third example the requirement names), naming the specific unmet clause per rule 5; re-checked R1's `.py`-precedence claim once against `main` before finalizing (rule 6) rather than asserting it from a single read of the PR branch alone
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites file:line-range plus the reviewed commit sha (`b8670e43:` prefix, rule 1); backward-traced each requirement to its issue bullet before checking the implementation (rule 3, `spec_ref` on every entry); R3's "why identical across three PRs" claim is derived from a code-structure citation (`gates/check_runner.py:473-477`) rather than three redundant re-runs, documented as a deliberate reuse rather than an unverified assumption; no duplicate-evidence entries to collapse (rule 4 n/a); single spec version in play — issue #2509 and #2488 as currently open (rule 5 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 3 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); no Incorrect verdicts so `spec_vs_built` was not needed; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not extended into risk-weighting; the one Surface finding (R1) is recorded as a scope-boundary observation in Open findings, not risk-banded
