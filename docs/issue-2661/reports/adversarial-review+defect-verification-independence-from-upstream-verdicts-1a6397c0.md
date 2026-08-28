---
issue: 2661
role: adversarial-review+defect-verification-independence-from-upstream-verdicts-1a6397c0
author: adversarial-review+defect-verification-independence-from-upstream-verdicts-1a6397c0
skills: adversarial-review (skill-repository(297e350)), defect-verification-independence-from-upstream-verdicts (skill-repository(297e350))
verifies_subject: true  # independent verification of PR #2680's (author silent-failure-audit+secure-coding-input-validation-injection-defense-07028068) deliverable for this same issue
loop_state: verified
upstream:
  - path: on-the-record/hooks/deliverable-guard.sh (PR #2680, branch issue-2661/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068)
    sha: 871b30eac88fedfb874556a2efe90a6f941e516b
  - path: docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md (untracked on this branch — exists only on PR #2680's branch; cited via git show)
    sha: 871b30eac88fedfb874556a2efe90a6f941e516b
---

# issue-2661 — adversarial-review+defect-verification-independence-from-upstream-verdicts-1a6397c0 record

## What was done

Independently re-verified PR #2680's five load-bearing claims from raw commands, in a fresh clone never touched by the delivering session. derived: `rm -rf /tmp/verify-2680 && git clone https://github.com/tokenmaxxxer/on-the-record.git /tmp/verify-2680 && git fetch origin pull/2680/head:pr-2680 && git checkout pr-2680` plus a second, separate clean clone of unmodified `origin/main` at `/tmp/verify-2680-main` for the pre-existing-failure comparison. The delivering session's own record (`docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md`, untracked on this branch, read via `git show pr-2680:docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md` in `/tmp/verify-2680`) was read only after each verdict below was independently formed, per the `defect-verification-independence-from-upstream-verdicts` skill.

**Claim 1 — the negative ("no real write path in this codebase or on this system's plugin install actually needs the exemption").** Verdict: Present, but the delivering session's own investigation covered a narrower population than the one that actually determines the claim's truth.

Their investigation (per their own record) checked whether on-the-record's own code creates a project-relative `scratch/`/`tmp/` directory, and whether a literal `plugin-cache` path exists on disk. It never checked whether the OS temp root `/tmp` itself — whose top-level segment is literally `"tmp"` — is ever the location of a real board-repo write reachable through Write/Edit/NotebookEdit. It demonstrably is:

canonical: `find / -path "*/docs/specs/approvers.md" 2>/dev/null | wc -l` — result: 240 (this session, run against the live filesystem)
```
$ find / -path "*/docs/specs/approvers.md" 2>/dev/null | grep -c '^/tmp/'
136
```
136 of those board-repo checkouts (each carrying `docs/specs/approvers.md`, the board-repo activation signal) sit under `/tmp/*` — e.g. `/tmp/pr2340-verify`, `/tmp/otr-main-check`, `/tmp/corescan`, `/tmp/fix2528` — real clones made by exactly the kind of verification work this task itself performs. I re-derived the negative against this broader population and it still holds, but only because an orchestrator personally Write/Edit-ing a deliverable-shaped file inside such a clone is itself the self-scribing behavior `deliverable-guard.sh` exists to block — confirmed independently in claim 5 below (`tests/run-orchestrate-tests.sh`'s own `mktemp -d`-rooted fixtures were silently mis-passing as ALLOW on unmodified `main` for this exact reason). Also checked a second real board repo on this system:

checked: `find /home/jwjung/arcade-dodger -iname approvers.md` — result: `/home/jwjung/arcade-dodger/docs/specs/approvers.md` (a board repo)
checked: `grep -rln "tmp/\|scratch/\|plugin-cache" --include="*.py" --include="*.md" --include="*.sh" --include="*.js" --include="*.ts" /home/jwjung/arcade-dodger` — result: no output, zero hits
checked: `find / -maxdepth 8 -type d -iname "*plugin-cache*" 2>/dev/null` — result: only `/home/jwjung/src/easy-korea/material-ui/packages/netlify-plugin-cache-docs`, an unrelated npm package name in a different project, never a plugin-checkout path.

Verdict stands: claim survives on the full population I could construct, but was established on a sample (project code review), not the population (every Write/Edit/NotebookEdit-reachable path, including the large `/tmp`-rooted board-repo population found above) — it happened to still be true, not because the investigation covered it.

**Claim 2 — live blast radius.** Verdict: Absent (no denial risk), confirmed empirically against the two sessions the task named.

canonical: session-log mtimes (this session, `ls -la --time-style=full-iso`) — `on-the-record-issue-2661-silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.session.*` last write 2026-08-28 15:28:49 KST (= 06:28:49 UTC), `on-the-record-issue-2679-silent-failure-audit+api-design-error-design-3353dd59.session.*` last write 2026-08-28 15:30:38 KST — both active around the PR's commit timestamps (06:27:30Z / 06:28:44Z, from `gh pr view 2680 --json commits`).

Both are spawned role sessions (workspace-naming convention `<repo>-issue-<n>-<role>` under `MUSTER_WORKSPACE_ROOT`, identical to this session's own). checked: `printenv | grep TOKENMAXXXER_SPAWNED` (this session) — result: `TOKENMAXXXER_SPAWNED=1`. `deliverable-guard.sh`'s first check after payload parsing is `if spawned: sys.exit(0)`, before any EXEMPT_SUFFIXES/segment logic runs — so this PR's change is structurally inert for any spawned session. Verified live against each session's real workspace path:

derived: `printf '%s' "$PAYLOAD" | env -u CLAUDE_ROLE TOKENMAXXXER_SPAWNED=1 bash on-the-record/hooks/deliverable-guard.sh` where PAYLOAD targets `<workspace>/src/module_notes.py` for each of the two sessions' real `/home/jwjung/.tokenmaxxxer/work/...` paths — result: rc=0 ALLOW for both.

Also: neither workspace path contains a `tmp`/`scratch`/`.git`/`plugin-cache` segment to begin with (`/home/jwjung/.tokenmaxxxer/work/<repo>-<issue>-<role>/...`), so this PR's change would have been irrelevant to them even absent the spawned exemption.

**Claim 3 — git-root-walk steerability inherited by EXEMPT_SUFFIXES's new anchoring.** Verdict: Present, reproduced live; the PR does disclose it, but overstates its test coverage.

derived: created `real-repo/` with a genuine `.git` (`git init`), planted a fake `.git` directory at `real-repo/attacker/sub/.git`, sent a Write payload for `real-repo/attacker/sub/docs/specs/approvers.md` (`cwd=real-repo/attacker/sub`) through the shipped hook:
```
--- with fake .git planted at attacker/sub (steered root) ---
rc=0
--- without fake .git (root resolves to real-repo/.git) ---
orchestrate: ... deliverable path in a board repo ...
rc=2
```
This confirms `EXEMPT_SUFFIXES`'s new `root_relative_n`-based exact-match inherits the identical `_git_root_from`/`os.path.isdir(probe/".git")`-trusting steerability already accepted for `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` (the sibling priorities-shard exemption's own known residual, tracked separately) — the bypass is moved onto a mechanism, not closed.

canonical: `git show pr-2680:docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md` (Open findings section) — the PR's own linked record states this explicitly: *"The ... git-root-walk gap ... now also applies to the EXEMPT_SUFFIXES check ... This is an extension of an already-known, already-accepted residual ... no new test added for it here since [the sibling exemption]'s existing expectedFailure cases already cover the walk itself."* That last clause is inaccurate — checked: `grep -n "expectedFailure\|def test_" test/test_deliverable_guard_priorities_shard.py` — result: all three `expectedFailure` cases (`test_bypass_via_planted_git_directory_should_be_denied`, `test_bypass_via_planted_git_symlink_should_be_denied`, `test_bypass_inside_linked_worktree_should_be_denied`) target `.../priorities/hack.md` payloads (`PRODUCT_CAPTURE_PRIORITIES_DIR_RE`) specifically, not `EXEMPT_SUFFIXES` — no test in the suite exercises the planted-`.git`-against-`EXEMPT_SUFFIXES` attack I just reproduced live above.

**Claim 4 — the `.git`-segment reasoning.** Verdict: Present, attempted to falsify, found no counter-example.

checked: `grep -rn "\.git/hooks\|\.git/info\|\.git/config" --include="*.py" --include="*.sh" --include="*.md" .` — result: real writes to `.git/info/exclude` exist, in `spawn.py`'s `issue_workspace()` (per `pipeline.py:925` and `docs/reports/2026-08-07-hunt-issue-289-phase2.md`) — but these are the spawner process's own `open(...).write(...)` calls executing as a subprocess (invoked via Bash), never a Claude Write/Edit/NotebookEdit tool call, so they never reach `deliverable-guard.sh` (it only gates those four `tool_name` values per its own PreToolUse header). This is consistent with, not a counter-example to, the PR's claim. checked: `find . -iname "*.ipynb"` — result: no notebook files in the repo, so no NotebookEdit call site to check either. No genuine counter-example found.

**Claim 5 — test-result claims.** `test_deliverable_guard_priorities_shard.py`: Present, reproduced exactly. `tests/run-orchestrate-tests.sh`'s "pre-existing failures ... confirmed to fail identically against the unmodified HEAD hook" claim: Absent (false as literally stated), reproduced from a clean `origin/main` clone.

derived: `python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q` on the PR branch (`/tmp/verify-2680`) — result:
```
.....x..x.....x....                                                      [100%]
16 passed, 3 xfailed in 0.95s
```
Matches the PR's claim exactly.

derived: `bash tests/run-orchestrate-tests.sh` on the PR branch, naive re-run (session env inherited) — result: `7 passed, 6 failed`, every `guard` case flipped to ALLOW. Root cause: the script's own `env -u CLAUDE_ROLE` unsets only `CLAUDE_ROLE`, not `TOKENMAXXXER_SPAWNED` — running it inside a spawned session's inherited env (both the delivering session and this session start with `TOKENMAXXXER_SPAWNED=1`) silently short-circuits every `guard` case to ALLOW via the same `if spawned: sys.exit(0)` from claim 2. derived: `env -u TOKENMAXXXER_SPAWNED -u CLAUDE_ROLE bash tests/run-orchestrate-tests.sh` on the PR branch — result:
```
== 11 passed, 2 failed ==
```
with the 2 failures named `directive-silent-for-roles` and `guard-nonboard-repo` — matching the PR's claim once the environment is corrected this way.

Re-derived the "unmodified HEAD hook" comparison from a genuinely clean `origin/main` clone (`/tmp/verify-2680-main`, `git clone` fresh — not `git show HEAD:file` swapped into the PR worktree), using the PR's own updated test script (only diff vs. main: `guard-outside-trees`→`guard-scratch-not-exempt`, per `git diff main...pr-2680 -- tests/run-orchestrate-tests.sh`): derived: `env -u TOKENMAXXXER_SPAWNED -u CLAUDE_ROLE bash tests/run-orchestrate-tests.sh` (PR's test script copied onto a clean checkout of unmodified `origin/main`'s hook) — result:
```
FAIL   directive-silent-for-roles         want=0 got=58
FAIL   guard-docs-in-board                want=deny got=allow
FAIL   guard-src-in-board                 want=deny got=allow
FAIL   guard-tests-in-board               want=deny got=allow
ok     guard-nonboard-repo                allow
FAIL   guard-scratch-not-exempt           want=deny got=allow
== 8 passed, 5 failed ==
```
`guard-nonboard-repo` **passes** (ALLOW) on the unmodified hook — it does not fail identically before and after, contradicting the PR's specific claim about that test. Isolated directly: derived: constructed a non-`approvers.md` git repo at `/tmp/nonboard-test` and sent the equivalent payload through the old hook (`/tmp/old-hook.sh`, `git show main:on-the-record/hooks/deliverable-guard.sh`) — result: rc=0 ALLOW; through the new (PR) hook — result: rc=2 DENY. But replaying the identical payload against the *old* hook from a non-`/tmp` location (`/home/jwjung/verify-nonboard-notmp`, outside any `/tmp`-segment interference) — result: rc=2 DENY, same as the new hook. This proves the "any git repo, not just a board repo, gets denied" behavior is genuinely pre-existing and unrelated to this PR (the hook's own header comment says the target repo no longer needs to already carry `docs/specs/approvers.md` itself, a change from an earlier issue predating #2661) — `guard-nonboard-repo`'s ALLOW verdict on `main`'s actual test harness was never evidence of real board-repo scoping; it was an artifact of the harness's `mktemp -d` fixture sitting under `/tmp` and tripping the very segment bug this PR removes. The three additional failures (`guard-docs-in-board`/`-src-in-board`/`-tests-in-board`) are, for the same root cause, tests that were silently mis-passing as ALLOW on `main` and are correctly fixed by this PR as a side effect — but the PR's test-plan checklist does not mention them, and mischaracterizes `guard-nonboard-repo` as a matching "confirmed to fail identically" pre-existing failure when the actual harness run shows it does not.

## Why

Ran each check from raw commands against a subject-untouched fresh clone per `defect-verification-independence-from-upstream-verdicts` (re-derive rather than cite; include at least one falsification attempt per claim — e.g. claim 4's `.git/info/exclude` search, claim 3's live planted-`.git` reproduction). Applied `adversarial-review`'s stance of treating the PR's self-report as a claim to attack, not a fact: for claims 1 and 5 I re-executed rather than re-read, and for claim 5 specifically did not stop once the first number matched (`16 passed, 3 xfailed` did) — continuing to the second test suite's claim is what surfaced the `run-orchestrate-tests.sh` discrepancy, and re-deriving the "unmodified HEAD hook" baseline from a genuinely clean clone (rather than trusting `git show HEAD:file` swapped into the PR's own worktree, which cannot detect the test-harness-level `/tmp`-fixture confound) is what showed the specific `guard-nonboard-repo` mischaracterization.

## What did not work

None — every planned attack (population re-derivation, live blast-radius test, planted-`.git` reproduction, `.git`-target falsification search, and a from-clean-`main` test re-run) executed successfully and produced a verdict on the first attempt.

## Upstream basis

`on-the-record/hooks/deliverable-guard.sh` and `tests/run-orchestrate-tests.sh` at PR #2680 head (commit `871b30eac88fedfb874556a2efe90a6f941e516b`, fetched via `git fetch origin pull/2680/head:pr-2680` into a fresh clone never touched by the delivering session), diffed against `origin/main` at `2e446215f2dbb367b20c8a4ae5542e26f4e4d0c2` (a second, separately-cloned checkout, `/tmp/verify-2680-main`). The delivering session's own record (`docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md`, untracked on this branch — read via `git show pr-2680:...` in `/tmp/verify-2680`) was read only after each independent verdict above was formed, to check for agreement/disagreement, not to shape which checks were run. `test/test_deliverable_guard_priorities_shard.py` at PR head was read to check whether its `expectedFailure` cases actually cover the EXEMPT_SUFFIXES-specific attack (claim 3) — they do not.

## Open findings

canonical: this section restates verdicts already established, with commands and raw output, in the "What was done" section above (claim 3's planted-`.git` reproduction and the `git show pr-2680:docs/issue-2661/reports/silent-failure-audit+secure-coding-input-validation-injection-defense-07028068.md` quote; claim 5's `env -u TOKENMAXXXER_SPAWNED -u CLAUDE_ROLE bash tests/run-orchestrate-tests.sh` runs against both the PR branch and a clean `origin/main` clone) — no new claims are introduced here, only their resolution paths.

- Claim 3 open item: EXEMPT_SUFFIXES's new anchoring inherits the git-root-walk steerability already accepted for the sibling priorities-shard exemption — real, live-reproduced above, and already disclosed in the PR's own linked record as an accepted residual. That record's claim that the walk's existing `expectedFailure` tests "already cover" this specific check does not hold: derived: `grep -n "expectedFailure\|def test_" test/test_deliverable_guard_priorities_shard.py` (quoted in full in "What was done") shows all three target `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` payloads, none target EXEMPT_SUFFIXES. Resolution path: same as that sibling exemption's own deferred resolution (no path-shaped formulation closes this while the hook decides from session-reported strings and session-mutable filesystem state before the write) — out of scope to fix here; recommend the PR add one `expectedFailure` case mirroring the existing three but targeting EXEMPT_SUFFIXES, so the gap is pinned down as a regression rather than only described in prose.
- Claim 5 open item: `guard-nonboard-repo` mischaracterized as a pre-existing failure. derived: the clean-`origin/main` run quoted above in "What was done" (`env -u TOKENMAXXXER_SPAWNED -u CLAUDE_ROLE bash tests/run-orchestrate-tests.sh` against `/tmp/verify-2680-main` with the PR's test script) shows `ok guard-nonboard-repo allow` — it passes on the unmodified hook, so the PR's "confirmed to fail identically" claim does not hold as literally stated. The deeper design fact it gestures at (any git repo, not just a board repo, gets denied) is separately confirmed genuinely pre-existing and unrelated to this PR, via the non-`/tmp` old-hook repro at `/home/jwjung/verify-nonboard-notmp` quoted above (rc=2 DENY on the old hook too, once the `/tmp`-fixture confound is removed). Resolution path: none needed for issue #2661 itself — the underlying behavior predates this PR and this PR doesn't change it — but the PR's stated test evidence for that specific claim should be corrected.
- Claim 5 secondary open item: three `run-orchestrate-tests.sh` cases (`guard-docs-in-board`/`-src-in-board`/`-tests-in-board`) were, per the same clean-`origin/main` run quoted above, silently mis-passing as ALLOW on unmodified `main` (the `/tmp`-rooted `mktemp -d` fixture confound) and are correctly fixed by this PR as a side effect — but this is not mentioned anywhere in the PR body or record. Not a defect — a disclosure gap; no action needed beyond noting it here.

## Next steps

None — loop_state: verified.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used to treat PR #2680's self-report (background-agent-plus-spot-checks investigation, test-plan checklist) as a claim to attack rather than a settled fact, and to deliberately search for the most plausible falsifying counter-example for claims 1 and 4 (the `/tmp`-rooted board-repo population; `.git/info/exclude` as a candidate legitimate `.git`-segment write) before accepting either negative.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived every claim above from raw commands (see the `derived:`/`canonical:` tags throughout "What was done") in a fresh clone never touched by the delivering session, read the delivering session's own record only after forming each independent verdict, and kept checking past the first passing number in claim 5 instead of treating the whole test-evidence section as settled once it matched — that continued check is what surfaced the `run-orchestrate-tests.sh` discrepancy.
