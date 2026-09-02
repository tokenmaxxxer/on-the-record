---
issue: 3129
role: implementation-blueprint+silent-failure-audit+test-derivation-18d0fea5
author: implementation-blueprint+silent-failure-audit+test-derivation-18d0fea5
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: amendment_channel.py, hook_input.py, test_amendment_channel.py -- untracked in this record's own -18d0fea5 tree (this branch is main-based, PR #3137 unmerged); all three live on PR #3137's -a641f019 branch only, cited below by that branch's own commit sha
loop_state: landed
type: fix
breaking: false
verdict: pass — acceptance: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 62 passed; acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: ok; acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok; acceptance: `python3 -m pytest tests/ -q` — result: 316 passed, 0 failed
upstream:
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-0be2218f.md
    sha: c045d4a4f069a2967a82a64a08807849f50c9c0f
  - path: on-the-record/hooks/amendment_channel.py
    sha: f20da852720f59e32c6e8698df51e1c229e33ec4
---

# issue-3129 — implementation-blueprint+silent-failure-audit+test-derivation-18d0fea5 record

## What was done

Repair round 3 on PR #3137 (branch `issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`), fixing the four command-shape defects PR #3163 found in round 2's writer-side repo-targeting parser. Code landed directly on PR #3137's own branch (commit `f20da852720f59e32c6e8698df51e1c229e33ec4`, pushed to `origin`), not merged, per the spawning prompt's explicit instruction; this record documents that fix from this session's own identity/branch, matching the pattern the round-1 (`cab0bc41`) and round-2 (`242afa40`) repair records already established for this issue — a session's `docs/issue-3129/` write is gated to its own `CLAUDE_SKILL`-declared branch (`board-gate.sh` R3, canonical: the refusal text this session hit when it tried the identical edit from the `-a641f019` branch: "writing docs/issue-3129/ requires branch issue-3129/...-18d0fea5 (current: issue-3129/...-a641f019)"), which for this session is `-18d0fea5`, not the PR's own `-a641f019`. The three files this round changed -- `amendment_channel.py`, `hook_input.py`, `test_amendment_channel.py` -- are untracked/absent in this record's own working tree for exactly that reason (this branch is `origin/main`-based and PR #3137 is not yet merged); they exist only on the `-a641f019` branch, cited above by that branch's own commit sha rather than quoted as paths resolvable from here.

Reproduced all four defects against `bf28bf93` (round 2's tip, the commit immediately before this session's fix) before changing anything, from the `-a641f019` checkout:
- derived: a scratch script driving the writer-side `run_hook()` entrypoint at `bf28bf93` with the four PR #3163 command shapes — result:
  ```
  heredoc -> study_marker: False  wrong(session-cwd)_marker: True
  semicolon -> study_marker: False  wrong(session-cwd)_marker: True
  subshell -> study_marker: False  wrong(session-cwd)_marker: True
  -R before subcommand -> study_marker: False  wrong(session-cwd)_marker: False
  ```
  The first three silently keyed the marker to the orchestrator's raw session cwd (wrong repo, zero stderr); the fourth wrote no marker at all (total miss, zero stderr).

Root cause, in the writer module's shared cd-resolution helper (round 2's dependency chain: the writer's `target_repo_for_command()` called the shared input-parsing module's `resolved_cwd()`) at `bf28bf93`:
- The shared module's leading-cd regex only matched a `cd <path>` followed by `&&` at the absolute start of the command string — a `;`-separated or `(`-wrapped leading `cd` simply didn't match, so it reported "no cd present" (the legitimate case) instead of correctly resolving the actual `cd` target.
- Any heredoc (`<<` anywhere in the string) made the whole command opaque unconditionally, even when the heredoc body is just data (an issue-body string) that doesn't affect where the `cd` prefix points.
- The shared resolver's own documented contract is "the cd target, else a caller-supplied default" for EVERY unresolved case, opaque-command included — so the writer fed both the legitimate "no cd" case and the illegitimate "unresolvable command" case through the identical default-to-session-cwd fallback, and the repo-slug lookup then resolved a real, wrong repo instead of reporting "unknown."
- Separately, the writer's own `gh issue edit` detection regex required `issue edit` immediately after `gh` with only whitespace between, so `gh -R owner/repo issue edit 42` never matched at all — a total miss with no marker, no notice, and no stderr, independent of the cd-parsing bug above.

Fix (Design A — parse the shell shape properly; see "Why" for why Design B was rejected), all on the `-a641f019` branch:
- The shared input-parsing module gained a heredoc-body-stripping helper: excises heredoc BODY text (the data between a `<<[-]DELIM` line and its terminator line), leaving the redirect operator/delimiter token itself in place, so a `--body-file - <<'EOF' ... EOF` body's literal text is never mistaken for shell syntax. Reports "undecidable" when a heredoc opens but the string never contains its terminator.
- It also gained an enclosing-group unwrapper: strips one layer of `( ... )` / `{ ... }` when it wraps the entire (trimmed) string, refusing to unwrap when the closing bracket is not the string's own last character (a sibling command after the group must not be silently discarded).
- Its cd-resolution function was rewritten to strip heredoc bodies first (reporting the string opaque only if that fails), then loop: unwrap any enclosing groups, match a leading `cd <path>` followed by `&&`/`||`/`;`/newline (not only `&&`), resolve `~` and relative-to-previous-step joins, and repeat — so `cd /a && cd b && gh ...` resolves to `/a/b`, and `(cd /a && gh ...)`/`cd /a; gh ...` both resolve to `/a` instead of falling through to "no cd."
- The writer's `target_repo_for_command()` no longer calls the shared module's convenience `resolved_cwd()` wrapper. It calls the tri-state cd-resolution function directly and branches explicitly: a resolved cd target → resolve that path's repo; an opaque/unresolvable command → return unresolvable (never the session cwd); no cd present → use the session cwd (legitimate — the command structurally has no `cd` prefix, this is not a guess). This is the change that actually closes the must-not: an unresolvable command can no longer reach the session-cwd repo lookup at all.
- The writer's `gh issue edit` detection regex was widened to tolerate any number of flags (`-R owner/repo`, `--repo=owner/repo`, ...) between `gh` and the `issue edit` subcommand.

Two new test classes added to the writer's own test suite, both driven through the real `run_hook` entrypoint (not the lower-level functions), per the spawning prompt's requirement:
- One test per PR #3163 shape (heredoc, semicolon, subshell, `-R` before the subcommand, `--repo=`, relative `cd` via a real `os.chdir` into the session cwd matching how the shipped shell wrapper actually runs, and `cd` embedded in a quoted body string that must NOT be treated as a real `cd`), plus one for an unterminated heredoc asserting no-marker-plus-stderr and never a cwd fallback.
- A second class re-runs the four broken shapes through the real, unmodified pre-repair scripts checked out via `git show bf28bf93:...` into a scratch directory, confirming each one still reproduces the pre-repair mis-keying/total-miss independent of this session's fix.
- derived: `python3 -m pytest tests/test_amendment_channel.py -q` (run from the `-a641f019` checkout, after `f20da852`) — result:
  ```
  ..............................................................           [100%]
  62 passed in 0.97s
  ```
- Confirmed cross-repo isolation, unresolvable-slug isolation, and fire-once/stop-after-absorption all still hold — derived: `python3 -m pytest tests/test_amendment_channel.py -q -k "cross_repo or unresolvable_slugs or FiresOncePerAmendment or AbsorbedAmendmentStopsAnnouncing"` — result: `11 passed`.

Full acceptance gate, same session, from the `-a641f019` checkout:
- acceptance: `python3 gates/probe_running_session_sees_amendment.py` — result: `ok`
- acceptance: `python3 gates/probe_amendment_notice_fires_once.py` — result: `ok`
- acceptance: `python3 -m pytest tests/ -q` — result:
  ```
  316 passed, 2 warnings in 10.28s
  ```
- derived: `python3 -m pytest test/ -q` — result:
  ```
  15 failed, 548 passed, 3 xfailed in 32.08s
  ```
  Same 15 pre-existing failures named in the spawning prompt as owned by #3091 (in `test_convention_equivalence.py`, `test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`, `test_spawn_skill_judge_haiku_timeout_overlap.py`, `test_spawn_artifact_skill_pairing.py` -- none touch the writer module, the shared input-parsing module, or the shipped hook wrapper).

silent-failure-audit pass (invoked via the Skill tool) against the new heredoc-stripping/group-unwrapping/cd-resolution code, canonical: this session's own diff of the shared input-parsing module (the "Fix" bullets above) read directly during the audit — found no new silently-absorbed path: every early return is a typed, reason-carrying opaque result the caller inspects, not a bare `None`/`pass`, and the writer's opaque-command branch is a `return None` the existing caller already turns into an observable stderr line — no new bare except/pass was introduced.

test-derivation pass (invoked via the Skill tool), canonical: this session's own equivalence-partition table over `target_repo_for_command()`'s decision — {explicit `--repo`/`-R` present, cd-resolution returns a target, returns no-cd, returns opaque} × {separator shape: `&&`, `;`, `||`, subshell, heredoc}, which is what produced the two-class test structure above (one class per "does this shape resolve correctly" partition, one class re-proving each defect partition against the pre-repair commit).

implementation-blueprint pass: this is a same-module edit (two existing flat modules, no new files, no new cross-module boundary) — re-running the classifier was not warranted; skip recorded per the skill's own single-file/no-new-boundary veto precedent this issue's original implementation record already noted (canonical: that record's own "implementation-blueprint pass" section, read this session; that record is itself untracked in this branch's tree, main-based, PR #3137 unmerged -- read via `git show 587dfa89:docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-a641f019.md` from the `-a641f019` checkout).

## Why

Design choice — Design A (parse the shell shape properly) over Design B (derive the target from where `gh` actually executed, e.g. a shim/alias): Design B would require installing a wrapper into the orchestrator's `PATH` or a `gh` alias that persists across every Bash tool call for the life of the orchestrator session, and reading its own recorded state back out — a much larger blast radius (a persistent PATH/alias mutation across the whole session, not just this one hook) for a hook whose own docstring already promises "must never call `gh`" and "local git plumbing only." Design A stays inside the existing total-function, no-network contract the shared input-parsing module already established, and every shape PR #3163 named is provably resolvable by structural parsing alone (heredoc bodies are textually delimited; `;`/`||`/subshell are ordinary shell syntax) — none of them actually needed the stronger Design B guarantee. The one must-not the choice hinges on — "anything the tokenizer cannot resolve with certainty must produce NO marker plus a stderr line, never a cwd fallback" — is verified by the unterminated-heredoc regression test: an unterminated heredoc (genuinely undecidable where the body ends) reports opaque, and `target_repo_for_command()` turns that into "unresolvable," never the session-cwd repo lookup.

Design choice — `target_repo_for_command()` calls the tri-state cd-resolution function directly instead of the convenience `resolved_cwd()` wrapper: that wrapper's own docstring is "the cd target, else a caller-supplied default" and that contract is correct and unchanged for any future caller that genuinely wants a best-effort cwd guess — the defect was this specific caller's stricter "never a fallback to the session cwd" promise being silently violated by a shared helper's documented-but-too-permissive behavior. Fixing it at the call site (rather than narrowing the wrapper's own contract, which has no other caller in the hooks tree today — derived: a recursive grep for both function names across the hooks and gates directories on the `-a641f019` checkout matched only the writer module's own uses) keeps the generic utility's documented behavior intact for whoever reads its docstring next, while giving this module the stricter guarantee its own docstring already promised.

## Upstream basis

PR #3163's finding — canonical: `gh pr view 3163 --json body` output, quoted in the spawning prompt verbatim — the four command shapes it confirmed broken: heredoc, semicolon, subshell (all three silently mis-key to session cwd, zero stderr) and `-R` before the subcommand (total miss, zero marker, zero stderr, zero notice).

The writer module and the shared input-parsing module at commit `bf28bf93` (PR #3137's round-2 tip, short form as it appears in this issue's own commit history and PR #3163's own record) — read directly from the `-a641f019` working tree at session start, quoted above under "What was done."

## Open findings

None open. The `--repo=` form and "relative cd"/"cd inside a quoted string" shapes named in the spawning prompt's required-test list were already handled correctly before this session (round 2's explicit-repo-flag regex already accepted `=`, and the leading-cd regex never matched text embedded inside quotes) — added as regression tests in the new "handles real command shapes" class without a corresponding pre-repair-failure test, since they were never broken.

## What did not work

None — derived: `git log --oneline` on the `-a641f019` branch after this session's push shows one new commit (`f20da852`) on top of `bf28bf93`, not a revert or a superseding follow-up; the first implementation of the tokenizer (heredoc-stripping, group-unwrapping, chained-cd-walking) passed every required shape and the full suite on the first run with no rework needed.

## Next steps

None — canonical: this record's own `loop_state: landed` frontmatter field, set in this same commit. The code fix is pushed to PR #3137's branch (`f20da852720f59e32c6e8698df51e1c229e33ec4`) but that PR itself is not merged by this session, per the spawning prompt's explicit instruction ("push to the existing branch, do not merge"); a human merges PR #3137 separately.

## Skill verdicts

canonical: this session's own Skill-tool invocations of `silent-failure-audit` and `test-derivation` against the diff described in "What was done", plus the classify-skip decision for `implementation-blueprint` cross-referenced against this issue's original implementation record (read via `git show`, see "What was done").

skill-verdict: implementation-blueprint — not-applicable: same-module edit to two existing flat modules, no new file, no new cross-module boundary — nothing to (re)classify
skill-verdict: silent-failure-audit — applied: invoked; audited every new early-return path in the heredoc-stripping/group-unwrapping/cd-resolution/target-repo-resolution code, confirmed each unresolved case surfaces as a typed opaque result or an observable stderr line, no new silent absorption (see "What was done")
skill-verdict: test-derivation — applied: invoked; partitioned `target_repo_for_command()`'s decision by {explicit-repo-flag, resolved-cd, no-cd, opaque-command} × {separator/wrapper shape}, which produced the two paired test classes above (see "What was done")
other mounted skills: not triggered
