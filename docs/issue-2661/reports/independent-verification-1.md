---
issue: 2661
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh (PR #2680 branch issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068)
    sha: 871b30eac88fedfb874556a2efe90a6f941e516b
---

# issue-2661 — independent-verification-1 record

## What was done

Build-now bypass (contract v3 s19a): CORE_BUILD_NOW=1 was set in this
session's environment by the spawner — checked: `printenv | grep
CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. So this record delivers
directly, no phase-1 proposal round.

Independently audited PR #2680, which claims to close issue #2661 by
removing `deliverable-guard.sh`'s unconditional scratch/tmp/.git/plugin-cache
path-segment exemption and anchoring a second `EXEMPT_SUFFIXES`
suffix-matching bypass found along the way. Checked out the PR head in a
separate worktree (`git fetch origin pull/2680/head:pr-2680-verify &&
git worktree add /tmp/verify-2680-check pr-2680-verify`) and independently
re-ran both of the issue's acceptance checks and the PR's test-plan
claims against the real hook, from scratch, rather than trusting the
PR's pasted output.

**Acceptance check 1 (three named payloads must DENY) — confirmed:**

canonical: pre-fix hook (`git show 2e446215:on-the-record/hooks/deliverable-guard.sh`,
the PR's parent commit, main branch tip at session start) run live via a
synthetic `Write` PreToolUse payload (`{"tool_name":"Write","tool_input":{"file_path":"<path>"},"cwd":"<fresh
git-init repo>"}`, `env -u TOKENMAXXXER_SPAWNED`) — result for the three
payloads named in the issue (segments "src, tmp, module.py", "docs, tmp,
note.md", "tmp, docs, specs, approvers.md"): all three rc=0 ALLOW —
silently exempted, matching the issue's bug report.
canonical: post-fix hook (PR #2680 worktree at commit
871b30eac88fedfb874556a2efe90a6f941e516b, same harness) — the same three
payloads: rc=2 DENY, rc=2 DENY, rc=2 DENY. Acceptance check 1 confirmed
met.

**Acceptance check 2 (genuine issue-#787 cases still pass) — confirmed:**

canonical: post-fix hook, genuine exempted path segments "docs, specs,
approvers.md" — rc=0 ALLOW, unchanged.
derived: `grep -rn "plugin-cache" --include="*.py" --include="*.sh" .`
across the repo — no hit is a real path, only prose/comments; the actual
plugin-cache install layout is two separate segments ("plugins" then
"cache"), never joined into one "plugin-cache" segment — checked live:
`find ~/.claude/plugins -maxdepth 4 -iname "*plugin-cache*"` returned no
result, and `ls -d ~/.claude/plugins/marketplaces/tokenmaxxxer/.git`
confirmed a real `.git` directory exists there.
derived: `grep -rln "scratch/" docs/handbooks README.md CLAUDE.md` and
`grep -rn tmp spawn.py roster.py pipeline.py` both returned no hits for a
project-relative scratch/ or tmp/ convention. This independently
confirms acceptance check 2's fallback clause was correctly invoked: no
real write path needs the scratch/tmp/plugin-cache segments, so removing
them in full (rather than narrowing) was warranted, and `.git` is real
but never a legitimate Write/Edit target segment.
derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q`
on the PR #2680 worktree — result: 16 passed, 3 xfailed — matches the
PR's claimed count exactly.

**Open finding — one inaccuracy in the PR's own test-plan claim (does
not affect the code fix's correctness, see Open findings below for the
full citation):** the PR's record and PR body claim
`tests/run-orchestrate-tests.sh` has "2 pre-existing failures
(`directive-silent-for-roles`, `guard-nonboard-repo`) confirmed to fail
identically against the unmodified HEAD hook, unrelated to this
change." I reproduced this directly and found `guard-nonboard-repo`
does not fail against the unmodified HEAD hook — it passes there and
only starts failing after this PR's own fix. Full evidence is under
Open findings.

The underlying `deliverable-guard.sh` fix is correct and both of issue
#2661's acceptance checks pass under independent, from-scratch
reproduction.

## Why

Independent verification means re-deriving the PR's claims from the real
hook and real test suites rather than trusting its pasted output, per
`docs/handbooks/observer-verification.md`. canonical: re-running both
acceptance checks from a fresh worktree at the exact pre-fix
(2e446215) and post-fix (871b30eac88fedfb874556a2efe90a6f941e516b)
commits, rather than trusting the PR's own pasted output, is what
surfaced the `guard-nonboard-repo` discrepancy documented above and
under Open findings — that check would not have been caught by reading
the PR's record alone.

## What did not work

None.

## Upstream basis

canonical: PR #2680 (branch
issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068)
at commit 871b30eac88fedfb874556a2efe90a6f941e516b, fetched via `git
fetch origin pull/2680/head` and checked out in a worktree at
/tmp/verify-2680-check — `on-the-record/hooks/deliverable-guard.sh`,
`test/test_deliverable_guard_priorities_shard.py`, and
`tests/run-orchestrate-tests.sh` on that worktree, all read and
independently re-executed. Its own audit record at path
docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md
(untracked on this branch — it lands only on the PR #2680 branch cited
above) was read for its claims, which this record then independently
re-derived rather than took on faith.
canonical: pre-fix baseline commit 2e446215 (the PR's parent, and
`origin/main`'s tip at this session's start — `git log --oneline -1
origin/main` confirms).
derived: `git show 8b449d98 -- on-the-record/hooks/deliverable-guard.sh`
— read to independently confirm the original stated justification for
the exemption this PR removes ("scratch files, the muster checkout
itself") before assessing whether PR #2680's removal was warranted.

## Open findings

- PR #2680's record and PR body claim that `guard-nonboard-repo` in
  `tests/run-orchestrate-tests.sh` fails identically against the
  unmodified HEAD hook. canonical: isolated repro of the
  `guard-nonboard-repo` scenario (a docs/notes.md-shaped write, cwd a
  bare `git init`'d repo under a `mktemp -d` directory, no
  docs/specs/approvers.md present) run against the unmodified HEAD hook
  (2e446215) directly:
  ```
  $ printf '{"tool_name":"Write","tool_input":{"file_path":"%s","content":"x"},"cwd":"%s"}' "$td/docs/notes.md" "$td" \
    | env -u CLAUDE_ROLE -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/deliverable-guard.sh; echo "rc=$?"
  rc=0
  ```
  — ALLOW, matching the test's own expectation, i.e. it does NOT fail
  pre-fix. canonical: the identical payload against the PR #2680
  post-fix hook:
  ```
  $ ... | env -u CLAUDE_ROLE -u TOKENMAXXXER_SPAWNED bash /tmp/verify-2680-check/on-the-record/hooks/deliverable-guard.sh; echo "rc=$?"
  orchestrate: this is an orchestrator session and .../docs/notes.md is a deliverable path in a board repo. ...
  rc=2
  ```
  — DENY, a NEW failure introduced (unmasked) by this fix, not a
  pre-existing one. canonical: full-suite reproduction with
  `env -u TOKENMAXXXER_SPAWNED bash tests/run-orchestrate-tests.sh`
  against unmodified HEAD (2e446215) — result: 9 passed, 4 failed
  (`directive-silent-for-roles`, `guard-docs-in-board`,
  `guard-src-in-board`, `guard-tests-in-board`), with `guard-nonboard-repo`
  among the passes, not the failures. Against the PR #2680 worktree with
  the same invocation — result: 11 passed, 2 failed
  (`directive-silent-for-roles`, `guard-nonboard-repo`), matching the
  PR's claimed post-fix count exactly, but not its claim about
  pre-fix identity.
  Root cause: `tests/run-orchestrate-tests.sh`'s `guard()`/`guard_raw()`
  helpers build fixture repos under `mktemp -d`, i.e. under the system
  tempdir — so every synthetic file_path in that suite's payloads
  carries a literal "tmp" path segment (the tempdir's own name).
  Pre-fix, that accidentally triggered the very scratch/tmp/plugin-cache
  exemption issue #2661 reports as a bug, which is why several of this
  suite's `guard-*` cases passed or failed the way they did pre-fix —
  not because the hook correctly recognized a "non-board" repo, but
  because the whole fixture tree lived under the now-removed tmp
  exemption. `deliverable-guard.sh`'s own header comment already states
  its real, pre-existing (pre-#2661) board-activation rule is "any git
  repo reachable from cwd" — so `guard-nonboard-repo`'s "allow"
  expectation for a bare git repo was already stale before this issue;
  removing the tmp exemption correctly stops masking that staleness, it
  is not a real regression in the delivered fix. But the specific claim
  "confirmed to fail identically against the unmodified HEAD hook" is
  false for `guard-nonboard-repo` as written.
  derived: `directive-silent-for-roles` genuinely is identical before and
  after — `env -u TOKENMAXXXER_SPAWNED bash on-the-record/hooks/directive.sh
  | wc -l` gives 58 both pre- and post-fix, and `directive.sh` is
  untouched by this PR's diff — that half of the PR's claim holds.
  Verdict: this is a record-accuracy defect in PR #2680's own evidence,
  not a correctness defect in the delivered `deliverable-guard.sh` fix —
  both of issue #2661's acceptance checks pass under independent
  reproduction (see What was done). Resolution path: a follow-up
  correcting either the stale `guard-nonboard-repo` assertion (it should
  assert deny, matching the hook's real activation rule) or, at minimum,
  amending PR #2680's own record to state this failure is newly
  surfaced by the fix rather than pre-existing.
- `PRODUCT_CAPTURE_ISSUE_RE`'s unanchored `.search()` — the sibling gap
  PR #2680's own record already logs as an open finding, not touched by
  this fix — carried forward unchanged; out of scope for this
  verification pass.

## Next steps

None — loop_state: landed.

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; used to write this
record, the audit reasoning, and all repo-facing artifacts in English
while keeping the final chat summary to the user in Korean.
