---
issue: 2600
role: adversarial-review+technical-writing-structure-comprehension-3f30f496
author: adversarial-review+technical-writing-structure-comprehension-3f30f496
skills: adversarial-review (skill-repository(297e350)), technical-writing-structure-comprehension (skill-repository(297e350))
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: issue-2600/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab (PR #2673, unmerged, not in repo on this branch)
    sha: ee7c8c92b0bcb1fde198dec041ef27003843a59c
---

# issue-2600 — adversarial-review+technical-writing-structure-comprehension-3f30f496 record

## What was done

Independently verified PR #2673 (`issue-2600/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab`,
head `ee7c8c92`), the second slice of #2600 (comment/docstring kind).
Re-cloned both repos fresh instead of trusting the PR body or its own
record: `/tmp/verify-2673/otr` at the PR head, `/tmp/verify-2673/core` at
`origin/main`. Reproduced each of the four carrying claims plus the
reconciliation and vocabulary side-claims from raw commands.

skill-verdict: adversarial-review — applied: invoked; this whole record
follows the two-party blind-evaluation protocol — a structurally
independent session re-derived every command from a fresh clone, took
the subject's PR body and record as context only, and treated the
933-vs-934 discrepancy and the consult.py hunk as findings surfaced by
looking rather than assumed innocent.
skill-verdict: technical-writing-structure-comprehension — applied: invoked; used to keep this record's sentences near the 15-20 word
target and to group the four-claim-plus-two-extras findings under
per-claim subheadings instead of one flat wall of prose.

### Claim 1 — shell diff restricted to non-comment lines is empty: **PRESENT**

Read every hunk in every changed `.sh` file by hand (all 22 files, all
hunks), then cross-checked each changed line's position against that
file's heredoc ranges.

derived: `cd /tmp/verify-2673/otr && git diff d3ef7b8d2c50f37d91837327116495c3c9cf9282 HEAD -- '*.sh'`
— every changed line in all 22 files is a top-level `#` comment, except
one.

The one exception is `on-the-record/hooks/pr-base-guard.sh`, where the
changed comment sits inside a `<<'PY'` heredoc:

```
42	IFS='' read -r -d '' GUARD <<'PY' || true
43	import json, os, re, subprocess, sys
...
96	# --- subject issue number from the current branch (spawned workspace scope) ---
...
161	PY
162	
163	CG_PAYLOAD="$payload" python3 -c "$GUARD"
```

The heredoc delimiter is quoted (`<<'PY'`), so bash performs no expansion
and `read -d ''` captures the body verbatim into `$GUARD`; the shell
never re-interprets that text as shell syntax. `$GUARD` is then handed to
`python3 -c "$GUARD"` as a Python source string, where `#` at line 96 is
a genuine Python comment — inert either way. This is exactly the
heredoc-embedded-text risk the review brief warned about, and it
resolves in the PR's favor rather than against it.

derived: `for f in <22 changed .sh files>; do bash -n "$f" && echo PASS $f || echo FAIL $f; done`
```
PASS on-the-record/hooks/approach-cap-warning.sh
PASS on-the-record/hooks/approval-gate.sh
PASS on-the-record/hooks/decision-queue-stopgate.sh
PASS on-the-record/hooks/delegated-judgment-gate.sh
PASS on-the-record/hooks/delegation-post-gate.sh
PASS on-the-record/hooks/deliverable-guard.sh
PASS on-the-record/hooks/deviation-log-guard.sh
PASS on-the-record/hooks/directive.sh
PASS on-the-record/hooks/gh-write-allow-gate.sh
PASS on-the-record/hooks/git-push-guard.sh
PASS on-the-record/hooks/heredoc-command-refusal-gate.sh
PASS on-the-record/hooks/merge-allow-gate.sh
PASS on-the-record/hooks/pr-base-guard.sh
PASS on-the-record/hooks/product-capture-stopgate.sh
PASS on-the-record/hooks/record-claim-guard.sh
PASS on-the-record/hooks/record-claim-shape-directive.sh
PASS on-the-record/hooks/report-framing-check.sh
PASS on-the-record/hooks/retry-loop-bound.sh
PASS on-the-record/hooks/role-deviation-directive.sh
PASS on-the-record/hooks/spawn-allow-gate.sh
PASS on-the-record/hooks/stop-poll-rearm.sh
PASS on-the-record/hooks/upstream-defect-scope-guard.sh
```
All 22 pass.

No changed line falls inside a double-quoted string, a `case` pattern,
or any other shell-executed context. Claim 1 holds.

### Claim 2 — tokenmaxxxer-core "zero in-scope edits", verified by an identical 934->934 count: **ABSENT**

The count itself does not reproduce. Re-derived it independently, twice:

derived: `cd /tmp/verify-2673/core && git rev-parse HEAD && grep -rIo --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l` (run twice)
```
764aebc19c7e01fedd0078805c75740ac777b9a6
933
933
```

That SHA is the exact commit PR #2673's own record cites as core's
`code_under_review` sha. The true count there is 933, not 934.

canonical: PR #2673's own record, read via
`git -C /tmp/verify-2673/otr show ee7c8c92:docs/issue-2600/reports/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab.md`
(unmerged PR branch, not in repo on this branch), lines 95-101:
```
**Acceptance-regex count, tokenmaxxxer-core.**
before (origin/main, fresh checkout): 934
after  (post-audit, same checkout):   934
```
"This differs from PR #2668's own core-repo acceptance-regex baseline of
933 by exactly 1 — a one-line drift explained by unrelated landings on
`main` between that map's derivation and this session."

That explanation cannot be true. Both "measurements" — PR #2668's 933 and
PR #2673's claimed 934 — are pinned to the *same immutable commit hash*
(764aebc19c7e01fedd0078805c75740ac777b9a6, the sha in PR #2673's own
frontmatter). A fixed commit's tree cannot receive "landings" after the
fact; re-running the identical command against the identical sha is
deterministic and gives 933 every time (shown above), matching PR
#2668's baseline exactly, not PR #2673's claimed 934. The 934 figure is a
measurement or transcription error in PR #2673's own report, not a real
drift — the premise for the offered explanation does not exist.

Independent of the count, sampled core's occurrences directly, since
"zero edits" is also a claim about what wasn't touched:

derived: `cd /tmp/verify-2673/core && grep -rIn --exclude-dir=.git --exclude-dir=docs -iE '\brole\b|역할' . | wc -l` → 849 (933 occurrences spread across 849 matching lines, some lines carry more than one hit).

Sampled 30 lines spread across that output (every 28th line via `awk 'NR%28==0'`) plus a targeted comment-only
sub-search (derived: `grep -rn --include='*.py' --include='*.sh' -iE '#.*\brole\b' /tmp/verify-2673/core | grep -v CLAUDE_ROLE | wc -l` → 267).
The large majority of the 30 fit the claimed categories (live
`CLAUDE_ROLE` docs, historical narration, heredoc-embedded text, or the
six named load-bearing files). One flagged candidate from the sample,
`core/hooks/approval-gate.sh:297-306`, does NOT hold up as a miss on
direct re-read — it is correctly-framed history:

canonical: `sed -n '297,306p' /tmp/verify-2673/core/core/hooks/approval-gate.sh`
```
# issue-343 removed the issue-295 observer-role exemption that used to
# live here. issue-295 carved out a closed-issue exemption for exactly
# two named roles (execution-observation, conformance-review), verifying
# an implementation role's own landed work after their shared issue
# auto-closed via that role's PR merge, implemented as OBSERVER_ROLES =
# ("execution-observation", "conformance-review") membership-tested at
# runtime (`role in OBSERVER_ROLES`) plus a hard-coded second identity,
```

"removed... that used to live here" is unambiguous past tense; correctly
left alone. No genuine in-scope miss survived direct re-reading in this
sample. The claim's *negative-result* framing is largely defensible on
the sample; its *stated verification number* (934->934) is not — it is
wrong on its own terms, at its own cited sha. Because the carrying
sentence bundles "zero in-scope edits" with "verified by an identical
934->934... count, not asserted," and the verification half is false,
the claim as stated is marked Absent.

### Claim 3 — history-vs-current triage: **PRESENT, with one scope-boundary finding**

Sampled 15 rewrite hunks across 14 files (board.py, checkpoint.py,
consult.py, directive_assembly.py, gates/finding_shape.py,
gates/findings_due.py, gates/gh_cache.py, gates/merge_gate.py,
gates/quality_bar.py, gates/record_lint.py, gates/repo_scope.py,
gates/skip_gate.py, ledger/decisions.py, harness/driver.py) plus surviving (unedited) `role`/역할 comment occurrences across both
touched and untouched files (derived: `grep -rniE '#.*\brole\b|#.*역할|"""[^"]*\brole\b|"""[^"]*역할' --include='*.py' --include='*.sh' /tmp/verify-2673/otr | grep -v '/docs/' | grep -v '/\.git/' | wc -l` → 693).

14 of the 15 rewrite hunks convert current-behavior teaching text
(function/module docstrings, inline comments describing what the code
does today) into session/skill/domain/참가자 vocabulary without
falsifying any historical statement. One is worth citing as a good
example of the harder case — updating a description of a *changed*
mechanism, not just swapping a word:

canonical: `git -C /tmp/verify-2673/otr diff d3ef7b8d2c50f37d91837327116495c3c9cf9282 HEAD -- gates/quality_bar.py`
```
-to a role that owns a `quality_bar` (roles/specs/<role>.spec.json), the
+to a quality domain that owns a `quality_bar` (the fixed 7-domain set
+inlined in `quality-bar-gate.sh` since issue #2539/#2610 — no longer read
+from `roles/specs/<role>.spec.json`, which was deleted), the
```
This correctly documents both the current mechanism and the fact the old
file was deleted, rather than silently overwriting history.

For the "left unchanged" direction, checked two candidates that looked
like possible misses on first read and found both defensible, not
defects, on direct re-inspection:

- `core/hooks/approval-gate.sh:297-306` — see Claim 2 above; correctly
  historical.
- `directive_assembly.py:610` docstring, `"""Pre-write the role's own
  record skeleton at bootstrap..."""` — looked like a same-file
  inconsistency (a sibling comment nearby was rewritten role->session),
  but is not one.

canonical: `sed -n '607,633p' /tmp/verify-2673/otr/directive_assembly.py`
```
607	def write_record_skeleton(cwd: str, issue: int, role: str,
608	                           task_text: str = "",
609	                           skill_sources: list | None = None) -> Path | None:
610	    """Pre-write the role's own record skeleton at bootstrap; never
611	    overwrite an existing record (a respawn into the same workspace)."""
...
632	    # issue #2575: `role` is a free-form slug under slug identity (#2555)
633	    # and is never validated against a closed role set any more (#2555/
```
`write_record_skeleton`'s own parameter is still literally named `role`
(line 607). The docstring at 610 correctly names its own live parameter;
rewriting it to "session" would have made docstring and signature
disagree. Line 632's own comment explains why the parameter itself was
never renamed: it is a free-form slug now, not a closed-catalog name.

**Real finding**: one sampled hunk is not a history/current triage
decision at all — it is unrelated content added inside what the PR
frames as a pure wording-retirement diff, and that new content itself
leaves "role" unretired four times.

canonical: `git -C /tmp/verify-2673/otr diff d3ef7b8d2c50f37d91837327116495c3c9cf9282 HEAD -- consult.py`, and `sed -n '490,498p' /tmp/verify-2673/otr/consult.py`
```
-        # 만 role 을 실제로 검증한다, pipeline.py). role 검증은 여전히 일어난다 —
-        # 지워진 건 죽은 코드지 검증이 아니다.
+        # 만 role 을 실제로 검증한다, pipeline.py). role 검증 호출 자체는 여전히
+        # 일어난다 — 지워진 건 죽은 코드지 검증이 아니다. 다만 이슈 #2610부터
+        # 그 함수는 role 카탈로그 조회 없이 빈 베이스라인을 무조건 쓴다(role 을
+        # 검증하지 않는다).
```
The added text documents new information about issue #2610's effect on
`role_settings()` — a real content update, not a wording swap — and
introduces four more literal uses of "role" that the same hunk does
nothing to retire, contradicting the PR's own "no behavior change,
comment/docstring wording only" framing for that specific hunk. This
does not break Claim 1 (the lines are still comment-only) or invalidate
the triage rule in general, but it is a genuine process miss: this one
hunk should either have been split out of the wording-retirement diff,
or itself have used session/participant vocabulary.

### Claim 4 — README.md/README.ko.md/UNENFORCED-CLAUSES.md deferral, premised on live code still emitting `APPROVE issue-<n>/<role>`: **PRESENT**

Grepped both fresh clones directly for the live emission, not just the
prose description of it.

derived: `grep -rn 'APPROVE issue-' /tmp/verify-2673/otr --include='*.py' --include='*.sh'` and the core equivalent — both hit real code, not just docs:

```
on-the-record/hooks/approval-gate.sh:255:    needle = "APPROVE issue-%d/%s" % (issue, role)
on-the-record/hooks/pr-preflight.sh:161:needle = "APPROVE issue-%d/%s" % (issue, role)
gates/ci.py:252:    prefix = f"APPROVE issue-{issue}/"
gates/delegation_metrics.py:18:_HUMAN_APPROVE_RE = re.compile(r"^APPROVE issue-(\d+)/([\w-]+)$")
core/hooks/approval-gate.sh:369:challenge = "APPROVE issue-%s/%s" % (issue_num, role)
```

`core/directive/session-protocol.md:48` and
`core/contract/role-handoff-contract.md:783` (both load-bearing, both
excluded from this PR already) independently confirm the same
still-current convention in prose. The premise is directly verified, not
inferred: this is live gate code building and matching the exact literal
string today, in both repos, using a variable literally named `role`.
Deferring the three files (which the diff-stat confirms this PR did not
touch: derived: `git -C /tmp/verify-2673/otr diff main...HEAD --stat` — README.md, README.ko.md, on-the-record/UNENFORCED-CLAUSES.md do not appear) to the identifier/prompt-text slice is justified.

### Vocabulary claim — "no new vocabulary invented": **PRESENT, one file-local caveat**

Extracted every added line's substitute term (session/세션,
spawned session, skill/스킬, 참가자, domain/quality domain,
execution-observation, subject-scoped) from the full added/removed diff,
then grepped each against an `origin/main` snapshot predating this PR
(`git archive d3ef7b8d2c50f37d91837327116495c3c9cf9282`).

derived: `grep -rniF 'spawned session' /tmp/verify-2673/main-snapshot | wc -l` → 149; `grep -rniF '세션' /tmp/verify-2673/main-snapshot | wc -l` → 1042; `grep -rniF '스킬' /tmp/verify-2673/main-snapshot | wc -l` → 345; `grep -c 'execution-observation' /tmp/verify-2673/main-snapshot/gates/skip_eligibility.py` → 4 (already present in the very file the substitution landed in).

Every term is FOUND pre-existing repo-wide by the counts above, except
"domain": zero hits specifically inside `gates/quality_bar.py` before
this PR (derived: `grep -c 'domain' /tmp/verify-2673/main-snapshot/gates/quality_bar.py` → 0), though the same word is
already established in the sibling enforcement script
`on-the-record/hooks/quality-bar-gate.sh` that file implements
(canonical: `on-the-record/hooks/quality-bar-gate.sh:34`, `# classify which quality domains the PR's changed paths implicate`) and in
`docs/issue-2568/reports/implementation.md`. This is a file-local
first-use of an already-established repo term, not invented vocabulary.
Claim holds.

## Why

Trusted nothing from the PR body or the subject's own record as
evidence; re-derived every command from two fresh clones instead. The
review brief warned that a tokenize-based comment checker can be blind
to shell heredocs, and that an unchanged count "proves nothing was
edited; it does not prove nothing needed editing." Both warnings paid
off in this session: see Claim 1 (the heredoc case needed direct
verification) and Claim 2 (the count did not survive re-derivation).

## What did not work

None.

## Upstream basis

PR #2673's own record — see frontmatter `upstream:` above for path and
sha — was read as context only, not as evidence. Every claim in this
record was independently re-derived from `/tmp/verify-2673/otr` and
`/tmp/verify-2673/core`, fresh clones of
`https://github.com/tokenmaxxxer/on-the-record.git` (branch
`issue-2600/technical-writing-structure-comprehension+silent-failure-audit-2d35eeab`)
and `https://github.com/tokenmaxxxer/tokenmaxxxer-core.git`
(`origin/main`, 764aebc19c7e01fedd0078805c75740ac777b9a6).

## Open findings

1. **The 934->934 core acceptance-regex count in PR #2673's record is
   wrong; the true count at the cited sha is 933->933**, matching PR
   #2668's baseline exactly, with zero drift (see Claim 2 above for the
   re-derivation). Resolution path: PR #2673 (or a follow-up correction
   to its record) should fix the verdict/frontmatter line and the
   "Acceptance-regex count" section to read 933->933 and drop the
   "unrelated landings on main" explanation, which the fixed-sha
   evidence rules out.
2. **`consult.py:492-497` is unrelated content added inside a
   wording-only PR, and itself leaves "role" unretired four times** (see
   Claim 3 above). Resolution path: a follow-up commit either splits
   that content update out of #2600's wording-retirement scope, or
   rewrites it to use session/participant vocabulary consistent with the
   rest of the diff.

## Next steps

None — this record is terminal. Findings 1-2 above are for the subject
(PR #2673) or a follow-up slice to act on, not further work in this
record.
