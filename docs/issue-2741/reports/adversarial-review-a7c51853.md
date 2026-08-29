---
issue: 2741
role: adversarial-review-a7c51853
author: adversarial-review-a7c51853
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2743 (on-the-record) and its companion tokenmaxxxer-core#353
loop_state: landed
upstream:
  - path: on-the-record PR #2743 (branch issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a)
    sha: 5cc92dfd52b7652d37e2eec6116bc732ab3a06cd
  - path: tokenmaxxxer-core PR #353 (branch issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a)
    sha: f06267ef7395001da7d612cc9959e15bcaecbd2c
---

# issue-2741 — adversarial-review-a7c51853 record

## What was done

Build-now bypass (contract v3 s19a): checked: `printenv | grep CORE_BUILD_NOW` —
result: `CORE_BUILD_NOW=1`. Delivers directly, no proposal round.

Independently verified PR #2743 (`tokenmaxxxer/on-the-record`, OPEN, base
`main`, head `5cc92dfd`) and its cross-repo companion PR #353
(`tokenmaxxxer/tokenmaxxxer-core`, OPEN, base `main`, head `f06267e`) —
canonical: `gh pr view 2743 --repo tokenmaxxxer/on-the-record
--json headRefOid,state,baseRefName` and the equivalent for
`tokenmaxxxer/tokenmaxxxer-core#353`. Both claim to retire the `role`
persisted-state dict key (rename to `skill`, forward-only, no dual read,
no migration) at every runtime-state write/read site outside `docs/` in
both repos — the last slice of #2600. Every claim below was re-derived
independently against the two PR branches checked out at
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2741-refactoring-legacy-seam-selection+adversarial-review-24d0293a`
(on-the-record) and `/home/jwjung/.tokenmaxxxer/work/tokenmaxxxer-core-issue-2741-role-key`
(core) — separate checkouts from this session's own working tree, not by
re-reading the PRs' own transcripts.

**1. Enumeration of write/read sites — FALSIFIED, two real misses found.**

derived: `git grep -nE '["\x27]role["\x27]' <ref> -- '*.py' | grep -v '^<ref>:docs/'`
run against both `origin/main` and PR HEAD in on-the-record. The PR
correctly renamed the large majority of the `origin/main` population (17
`spawn.py` sites, `roster.py`, `board.py`, `lifecycle.py`, `events.py`,
`watchdog.py`, `consult.py`, `pipeline.py`, `relay.py`, `bench/run.py`,
the `gates/*.py` modules, test fixture files, and the
`.on-the-record/role.json` sidecar readers in `on-the-record/hooks/*.sh` —
per file counts as the PR itself describes them, canonical: `gh pr view
2743 --repo tokenmaxxxer/on-the-record --json body`) down to a residual
set that is genuinely inert: `gates/finding_shape.py` /
`gates/findings_due.py` (reading `docs/reports/findings/<role>/` frontmatter
— that frontmatter convention is `docs/` content, out of scope by the
issue's own non-goals, unrelated to the roster/ledger/sidecar dict-key
population), `harness/fixture-target/scenario.py` (LLM chat-message
`role`), `harness/run_smoke.py` / `on-the-record/monitors/test_poll_heartbeat.py`
(synthetic test fixtures, no real consumer reads their `role` field back —
confirmed by grepping for readers), `spawn.py:1894` (`ap.add_argument("role", ...)`
CLI positional), and `test/test_spawn_attempt_staleness.py:394,408` (the
string `"role"` is a *value* passed to `_write_attempt(attempt_id, issue,
skill, ...)`, not a key — canonical: `grep -n "def _write_attempt" -A 5
test/test_spawn_attempt_staleness.py` shows the function's own body writes
`"skill": skill`). All of these match one of the PR's three stated
exclusion categories or are `docs/`-frontmatter-adjacent and genuinely
inert.

But two real, unrenamed persisted-state write/read pairs survive outside
`docs/`, both live code paths, both missed by the PR's own enumeration:

- **PR-body `role:` trailer.** `relay.py:267` (`ensure_pushed()`, called
  from `spawn.py:4400`) still builds
  `f"...role: {skill}"` as an explicit-carrier trailer written into the
  body of every PR it opens (issue #1814 convention) — canonical:
  `git diff origin/main HEAD -- relay.py` (in the on-the-record PR
  checkout), which shows two *other* dict-key sites in the same file
  (`relay.py:172`, `relay.py:257`) renamed to `"skill": skill` while line
  267's f-string literal was left untouched.
  `gates/flows.py:26-34` (`_ROLE_TRAILER_RE = re.compile(r"^role:\s*([a-z0-9-]+)\s*$")`,
  `_role_from_pr()`) still reads that exact trailer back — canonical:
  `git diff origin/main HEAD -- gates/flows.py`, which shows dict-key sites
  30+ lines below (inside `flows_payload()`) renamed to `"skill"` while
  `_role_from_pr()` itself has zero diff. The PR's own record cites this
  file: `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md` (untracked in this working tree — it lives on the PR #2743 branch) line 27
  (canonical: `git show origin/issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md`),
  lists both `relay.py` and `gates/flows.py` as renamed files — the miss is
  a blind spot in the search method (grepping for the quoted-key literal
  `"role"`/`'role'`, which does not match the `f"role: {skill}"` trailer
  literal or the `^role:` regex), not an unvisited file.
- **GitHub issue-label `role:{skill}`.** `gates/patrol_board.py:229,332,337`
  (writes the label on board-issue creation, reads it back via
  `gh issue list --label role:{skill}` at line 229) and
  `gates/patrol_promote.py:236,242` (same pattern for promoted-finding
  issues) still use the literal `role:` label prefix — canonical:
  `git diff origin/main HEAD -- gates/patrol_board.py` (0 lines) and the
  equivalent for `patrol_promote.py` (0 lines): neither file was touched.
  The same untracked record file above (line 41) shows the
  builder did inspect `patrol_promote.py` — `derived: grep -n
  "patrol_promote\|promotions" --include='*.py' -r . | grep -v /docs/` —
  but only checked the `promotions` list's dict shape
  (`{"fingerprint": ..., "issue": ...}`, line 302) and concluded "no
  role/skill key", missing the `--label f"role:{skill}"` argument in the
  same file 60+ lines away, and never checked the sibling file
  `patrol_board.py` at all.

Both are genuine persisted state (GitHub PR-body text and GitHub issue
labels respectively) written and read outside `docs/` in live code paths
— this directly falsifies acceptance bullet 1, "No `role` persisted key is
written anywhere outside `docs/` in either repo," as currently delivered.

**2. Live round-trip — CONFIRMED**, re-derived independently (not
re-running the PR's own transcript): called the real
`pipeline._write_skill_sidecar(td, 27410, "implementation")` in a temp
workspace, read back the written `.on-the-record/role.json`
(`{"skill": "implementation", "issue": 27410}`), then invoked the real
`core/hooks/board-gate.sh` from PR #353's branch as a subprocess against
that file on a matching `issue-27410/implementation` branch: `rc=0`
(allow), confirming the real writer and the real cross-repo reader agree
end to end.

**3. Failing-test sets vs. `origin/main`, as sets of names — CONFIRMED in
both repos.**
- on-the-record: `python3 -m pytest -q` on PR HEAD and on an `origin/main`
  worktree both produce 16 failed / 539 passed / 6 xfailed; `diff` of the
  two sorted `FAILED ...` name lists is empty (`derived`, both runs shown
  in full below).
- tokenmaxxxer-core: `bash core/hooks/tests/run-board-gate-tests.sh` (143
  passed / 2 failed: `feasibility-spikes`, `ops-postmortems`) and
  `python3 -m pytest -q test tests` (3 failed:
  `test_proposal_shape_gate_refuses_missing_sections`,
  `test_survey_order_gate_refuses_proposal_without_survey_or_skip`,
  `test_A5_trailer_gate_quote_split_commit_is_detected`) — identical
  failing names on PR #353 HEAD and on an `origin/main` worktree for both
  suites.

**4. Cross-repo fail-open claim — CONFIRMED, tested live in both merge-order
directions**, not just read from code. Built a probe
(`/tmp/probe_failopen.sh` — a session-scratch file, untracked, not a repo
path) that materializes each `board-gate.sh` version (`origin/main` =
pre-#353, `HEAD` = post-#353) via `git show <ref>:...` and runs it as a
real subprocess against a real sidecar file on a matching branch:
- Direction A (on-the-record merged first, core not yet): old `board-gate.sh`
  (still reads `.get("role")`) against a new-format sidecar
  (`{"issue": 3, "skill": "qa"}`) — `rc=0` (allow), no crash.
- Direction B (core merged first, on-the-record not yet): new
  `board-gate.sh` (reads `.get("skill")`) against an old-format sidecar
  (`{"issue": 3, "role": "qa"}`) — `rc=0` (allow), no crash.
- Both directions degrade precision exactly as claimed, demonstrated
  concretely: with matching key formats and a genuinely disagreeing
  sidecar (`branch=issue-3/qa`, `sidecar={"issue":3,"skill":"otherskill"}`),
  `board-gate.sh` hard-denies (`rc=2`, "sidecar role/issue ... disagrees
  with the branch-parsed role/issue"). With the same disagreeing content
  but a cross-format gap (old-format reader, new-format sidecar), the
  identical disagreement is silently missed — `rc=0` (allow), no deny, no
  stderr. This is the precision loss the PR describes, reproduced directly
  rather than taken on the PR's word.
- Additionally spot-checked one of on-the-record's own six sidecar readers
  (`on-the-record/hooks/approval-gate.sh:117-131`, canonical: `sed -n
  '108,131p' on-the-record/hooks/approval-gate.sh` on the PR checkout):
  same `except (OSError, ValueError): pass` fail-open pattern, and — per
  the builder's own hunt finding, cited at
  `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md` (untracked in this working tree — lives on the PR #2743 branch)
  (canonical: `git show
  origin/issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a:docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md`
  — a silent-fail-open regression the builder found and then fixed in a
  later commit on this same branch) — now emits an explicit stderr
  diagnostic naming issue #2741 when a pre-rename sidecar is encountered,
  rather than failing open silently. Confirmed present in the final HEAD
  read directly (not just the hunt record's before/after transcript).

**5. `docs/` untouched, no dual read — CONFIRMED.**
`git diff --stat origin/main..HEAD -- docs/` across all four issue-2741
commits shows only 2 new files added under `docs/issue-2741/` (this PR's
own proposal/record files) — zero modifications to any pre-existing
`docs/` file. `git grep` for `.get("role")`/dual-key fallback patterns
across both repos' `*.py`/`*.sh` outside `docs/` and `test/` returns
nothing; the on-the-record sidecar readers' branch-regex fallback is a
pre-existing (#1814/#1827), unrelated mechanism, not a role/skill dual
read. The `core/hooks/board-gate.sh` diff is a clean 3-line change
(`.get("role")`→`.get("skill")`, `_sidecar["role"]`→`_sidecar["skill"]`),
matching the PR's stated `+3/-3`.

## Why

The task named the enumeration claim as carrying the most risk (a missed
write site leaves the old key alive in new data) and asked for the
population to be re-derived independently rather than checked against the
PR's own list. Re-deriving it with `git grep` on both `origin/main` and PR
HEAD, then manually classifying every residual hit, is the only way to
catch a site the PR's own search method structurally can't see (a quoted
dict-key grep does not match an f-string trailer literal or a `role:`
label-prefix literal) — which is exactly what happened here.

## What did not work

None — every probe (live round-trip, fail-open direction tests, precision-
degradation test, both repos' failing-test-set diffs) succeeded on the
first construction; no dead ends to report.

## Upstream basis

- on-the-record PR #2743, branch
  `issue-2741/refactoring-legacy-seam-selection+adversarial-review-24d0293a`,
  head `5cc92dfd52b7652d37e2eec6116bc732ab3a06cd` (same-commit as `HEAD` of
  the separate on-the-record checkout used throughout this verification,
  untracked in this session's own working tree).
- tokenmaxxxer-core PR #353, same branch name, head
  `f06267ef7395001da7d612cc9959e15bcaecbd2c` (separate core checkout, also
  untracked in this session's own working tree).
- The builder's own record, untracked in this working tree (lives on the PR #2743 branch): `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a.md`
- Its hunt-finding companion, also untracked in this working tree: `docs/issue-2741/reports/refactoring-legacy-seam-selection+adversarial-review-24d0293a/2026-08-30-hunt-role-key-rename.md`
  (both sha `5cc92dfd`) — read for context but not trusted as evidence;
  every claim attributed to them above was independently re-derived with
  the `canonical:`/`derived:` commands cited inline.

## Open findings

canonical: this record's own "What was done" §1 derivations (`git diff
origin/main HEAD -- relay.py`, `git diff origin/main HEAD --
gates/flows.py`, `git diff origin/main HEAD -- gates/patrol_board.py`,
`git diff origin/main HEAD -- gates/patrol_promote.py`, all run in the
on-the-record PR checkout) — restated here as the finding list.

1. **role: PR-body trailer not renamed** (`relay.py:267`, `gates/flows.py:26-34`)
   — real persisted state outside `docs/`, still literally `role:`.
   Resolution path: a follow-up commit on PR #2743's branch (or a new
   commit if #2743 has already merged by the time this is read — check
   current state with `gh pr view 2743 --repo tokenmaxxxer/on-the-record
   --json state,mergedAt` before acting) renaming `relay.py:267`'s trailer
   text to `skill: {skill}` and `gates/flows.py`'s `_ROLE_TRAILER_RE` /
   `_role_from_pr()` to match, forward-only per the same operator ruling —
   this is squarely the same population the rest of the PR already
   handles, just missed by the search method.
2. **role:{skill} GitHub issue labels not renamed** (`gates/patrol_board.py:229,332,337`,
   `gates/patrol_promote.py:236,242`) — real persisted state (GitHub issue
   labels) outside `docs/`, still literally `role:`. Resolution path: same
   as above, renaming the label prefix and its one reader
   (`gh issue list --label role:{skill}`) in both files.
3. Both findings above mean acceptance bullet 1 ("No `role` persisted key
   is written anywhere outside `docs/` in either repo") is not satisfied by
   PR #2743 as currently written, verdict per this record's own §1 derivation
   above — the PR should not land as a final delivery of this issue until
   these two sites are addressed (or an operator explicitly rules them out
   of scope, which nothing in the issue text does — they are not CLI
   syntax, not LLM chat-message role, and not decorative test fixtures, the
   three stated exclusion categories).

skill-verdict: adversarial-review — applied: invoked; used its blind-artifact
posture as the operating stance for this whole verification (canonical:
this record's own "What was done" section, all five sub-claims re-derived
from the PR branches directly) — re-derived every claim (enumeration, live
round-trip, fail-open behavior, failing-test sets) from the actual PR
branches and a fresh probe script rather than trusting the PR's own
transcript, and it is what surfaced the two missed write sites the PR's own
search method couldn't see.
skill-verdict: work-in-english — applied: invoked; this record, the probe
script, and all intermediate progress notes were written in English per
policy.
other mounted skills: implementation-audit, merge-gates — not triggered;
canonical: this session's task prompt (`gh issue view 2741`) already
supplied the falsifiable acceptance criteria directly, so no separate
claim-extraction pass was needed, and no merge-gate design question arose
during this verification.

## Next steps

None outstanding for this record — `loop_state: landed`. This record and
its two open findings are delivered as this PR; whether to open a
follow-up fix (or amend #2743 directly) for the two missed write sites is
the operator's call, not this session's to make unilaterally.
