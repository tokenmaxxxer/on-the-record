---
issue: 3231
role: implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6
author: implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), technical-writing-structure-comprehension (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: delivered
code_under_review: same-commit
type: feature
breaking: false
verdict: shipped
upstream:
  - path: docs/handbooks/install-sufficiency.md
    sha: same-commit
  - path: scripts/preflight/consumer_preconditions.py
    sha: same-commit
---

# issue-3231 — implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-c01699d6 record

## What was done

canonical: `skills.py` at this commit (`_skill_repo_managed_root()`/`_skill_repo_root()`) read against `docs/handbooks/setup.md`'s prior text "skill-repository 는 다르다 — 자동 clone 이 없다" (git history, commit prior to this branch) — the managed-clone fallback (issue #1789) already auto-cloned before this issue; the doc's "no automatic clone" claim was false, matching the mismatch docs/issue-3182's records flagged.

Shipped two of the four removable preconditions, and gave the other two a better error:

- **`skill_repository_resolvable` — tier: on-first-need-with-notice, automatic.** New `on-the-record/hooks/skill-corpus-bootstrap.sh` `SessionStart` hook calls `spawn.py ensure-skills` (`skills.py:ensure_skill_corpus_cli`, new), which drives the same `_skill_repo_root()` resolution a real `--skills` spawn already used, at session start instead of only inside the first spawn.
- **Hardened `_skill_repo_managed_root()`** for the must-not clause: clones into a scratch directory next to the final path, checks the git subprocess's exit code *and* content, and only `os.replace()`s into place on a verified-complete clone.
  acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py::InterruptedFetchNeverReadsPresentTest -q` — result: PASS
  ```
  2 passed in 0.3x s (interrupted-fetch leaves real path untouched/unsatisfied; a completed fetch flips it satisfied)
  ```
- **`home_claude_skills_dir_present` — tier: automatic.** The same hook creates `~/.claude/skills` if absent, empty — `skills.py`'s own `_local_skill_dirs()` (canonical: skills.py, function definition read this commit) already treats absent and empty identically, so this is zero-risk (no content written, nothing to interrupt).
- **Git identity, `docs/specs/approvers.md` — tier: stays manual, with a better error.** New `install-precondition-notices.sh` `SessionStart` hook prints a notice for each when unmet (read-only `git config --get`, a file-existence check), instead of letting the failure surface deep inside `board.py`'s `git commit`/`require_board()`. Neither flips its preflight bit — the state itself is genuinely unremovable — only the discovery moved earlier.

Fixed README.md and docs/handbooks/setup.md (Korean + English) to describe the shipped auto-fetch instead of instructing a manual clone. Rewrote docs/handbooks/install-sufficiency.md into "what was removed" / "stays manual, with a better error" / "cannot be removed" sections. Registered both new hooks (and a pre-existing unregistered `amends-landing-apply.sh` found alongside them) in docs/specs/enforcement-boundary.md and generated-paths.md; refreshed docs/specs/reconciled-index.md's hash rows for the two touched spec docs.

skill-verdict: silent-failure-audit — applied: invoked; audited `_skill_repo_managed_root()`/`ensure_skill_corpus_cli()` in skills.py. The prior `except OSError: pass` discarded git-missing/disk-full/permission-denied detail; fixed to log `type(exc).__name__: exc` to stderr.
derived: `git show b2f089ec -- skills.py | grep -A2 'except OSError as exc'` — result:
```
+        except OSError as exc:
+            # silent-failure-audit (issue #3231): a bare `except OSError:
+            # pass` here would discard exactly the detail a stuck fetch
```

skill-verdict: technical-writing-structure-comprehension — applied: invoked; restructured several 40-60-word multi-clause sentences in install-sufficiency.md's "What was removed" section into shorter single-idea sentences (commit `b2f089ec`, this branch).

skill-verdict: implementation-blueprint — applied: invoked; retrospectively classified the shipped structure (see derived: line below).
derived: `python3 /home/jwjung/skill-registry/skills/implementation-blueprint/scripts/prep.py classify --surface backend --external no --logic crud --asynchronous no` — result: `ARCHETYPE: data-centric` (controller/service/repository). The shipped shape already matches without having named it going in: the CLI subcommand dispatch is a thin controller, `ensure_skill_corpus_cli()` is the service, `_skill_repo_managed_root()`/`_skill_repo_root()` is the repository. No anti-pattern from the recommended list applies.

## Why

Rationale for each safety-tier decision is inline above and in install-sufficiency.md's "What was removed" / "Stays manual, with a better error" sections. Summary: cloning into the plugin's own cache is safe to do unasked (writes nothing the user owns) but doing it invisibly is not — hence notice, not silence. Git identity and `docs/specs/approvers.md` genuinely cannot be removed (the operator's own choice; per-repo state the plugin has no authority to invent) — hence notice-only, no mutation, matching the must-not clause's explicit "must not modify the user's global git configuration."

## What did not work

None.

## Upstream basis

- docs/issue-3182's five verification records (established the doc-vs-code mismatch gap and the ten-precondition baseline) — read, not modified.
- `scripts/preflight/consumer_preconditions.py`, `docs/handbooks/install-sufficiency.md` — both same-commit (this issue), the doc rewritten and the script's `CHECKS` line_anchors corrected for line-number drift the code changes caused.
- `skills.py`'s pre-existing `_skill_repo_managed_root()` (issue #1789) — same-commit, hardened, not replaced.

## Open findings

derived: `git show b2f089ec -- skills.py | grep -A2 'except OSError as exc'` — result (same as above): the one silent-failure-audit finding (bare `except OSError: pass`) is fixed in this same session's commit `b2f089ec`. Nothing else open.

## Next steps

loop_state: delivered.

acceptance: `python3 -m pytest tests/test_issue_3231_install_removals.py -q` — result: PASS
```
12 passed
```
acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` — result: PASS
```
12 passed
```
acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` — result: PASS
```
4 passed
```
derived: `python3 -m pytest test/ tests/ on-the-record/hooks/ -q` — result: 1251 passed, 3 xfailed, 0 failed (test/ alone 657 passed 3 xfailed; tests/ alone 552 passed)

Live demonstration of the acceptance's satisfied-count requirement:
derived: `env -i PATH="$PATH" HOME=<isolated> TOKENMAXXXER_RULEBOOKS=<nonexistent> python3 scripts/preflight/consumer_preconditions.py` (before `ensure-skills`, this session) — result:
```
5/10 preconditions satisfied.
5 missing: gh_cli_authenticated, git_identity_configured, skill_repository_resolvable, home_claude_skills_dir_present, remote_push_access
```
derived: `python3 spawn.py ensure-skills` (same isolated env) — result: creates `~/.claude/skills`, fetches skill-repository into the plugin's managed cache, prints both notices to stderr.

derived: same preflight command, after `ensure-skills` — result:
```
7/10 preconditions satisfied.
3 missing: gh_cli_authenticated, git_identity_configured, remote_push_access
```
The satisfied count rose from 5 to 7 in this sandbox (which already has `claude`/`git`/`gh`/disk headroom, unlike a bare machine); the delta is exactly the two preconditions this issue targets — `skill_repository_resolvable` and `home_claude_skills_dir_present` both moved from missing to satisfied, `git_identity_configured`/`gh_cli_authenticated`/`remote_push_access` unaffected by this issue's scope (irreducible or stays-manual by design, per docs/handbooks/install-sufficiency.md).

other mounted skills: not triggered (work-in-english, premortem, adversarial-review, prose-modes, decision-records, hypothesis-testing were configured-but-not-invoked per task-text match, not this session's own judgment that any applied — no open plan to pressure-test, no third-party artifact to hand off blind, no go/kill metric to pre-register).
