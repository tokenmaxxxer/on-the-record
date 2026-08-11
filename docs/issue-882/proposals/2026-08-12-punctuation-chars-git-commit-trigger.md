---
status: approved
files:
  - on-the-record/hooks/spec-index-preflight.sh
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/role-axis-completeness-guard.sh
  - on-the-record/hooks/test_spec_index_preflight.py
  - on-the-record/hooks/test_gate_registration_guard.py
  - on-the-record/hooks/test_role_axis_completeness_guard.py
  - docs/issue-882/reports/implementation/survey.md
  - docs/issue-882/reports/implementation/resolution.md
  - docs/issue-882/proposals/2026-08-12-punctuation-chars-git-commit-trigger.md
---

Note (this session): `docs/issue-882/reports/implementation.md` — the
phase-2 record path — is mechanically blocked by
`on-the-record/hooks/approval-gate.sh` (`CLAUDE_ROLE=implementation`,
branch `issue-882/implementation`, no `APPROVE issue-882/implementation`
comment on the issue yet). `approval-gate.sh`'s own scope is exactly the
role's record file plus `src/`/`test(s)/` PATH-SEGMENT matches (checked
this session: `on-the-record/hooks/test_*.py` has no `src/`, `test/`, or
`tests/` path segment, so it is not gated either) — so this session's
actual fix is committed in the same PR; the write-up that would
otherwise live in `implementation.md` lives at
`docs/issue-882/reports/implementation/resolution.md` instead, a
phase-1-legal path, matching the precedent issue #866's PR (`7d97bd6`)
and issue #876's PR set for this exact situation. This PR's body carries
a plain `#882` reference, no `Closes`.

# Proposal — issue #882, implementation

## Request

Issue #882: the `shlex.split`-based `git commit` trigger check
(`spec-index-preflight.sh` #866/PR #875, ported unchanged to
`gate-registration-guard.sh`/`role-axis-completeness-guard.sh` in #876)
fuses an unspaced opening parenthesis onto `git` — `(git commit -m x)`
tokenizes to `["(git", "commit", ...]`, so `"git" in tokens` is `False`
and the trigger silently never fires, even though the wrapped command is
an ordinary, real subshell commit. The pre-#866 `\bgit\s+commit\b` regex
caught this shape; the #866 fix traded it away to close the more common
`git -c k=v commit` bypass. This is the second time in this trigger
check's history that closing one hole opened another. Fix all three
hooks at once (this issue's own explicit target list), evaluate the
issue's own five-input table plus the `punctuation_chars=True` design
`merge-allow-gate.sh`/`spawn-allow-gate.sh` (issue #824/#834) already
landed, and re-confirm whether the #876 shared-helper rejection still
holds.

## Constraints

- Judge the fix empirically against the issue's own five inputs before
  choosing (issue's decision point 1) — not by inspection alone.
- All three hooks must end up checked identically — this issue exists
  because a prior fix landed non-uniformly across the three.
- Every hook's own regression test file is the only place new test cases
  land; `test_spec_index_preflight.py`'s pure-Python mirror
  (`is_git_commit_invocation`) must be edited in the same shape as its
  hook, or the two silently diverge again.
- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` must show no
  new failures versus `origin/main`, compared via isolated worktrees (a
  direct in-place run is not a valid comparison method — same
  constraint issues #866/#876 recorded, this repo's own
  `t_rulebook_version_is_recorded` fails against a dirty working tree).
- `on-the-record/hooks/pr-preflight.sh` is out of the write set — a
  concurrent session is editing it.

## Rationale

Chose `shlex.shlex(cmd, posix=True, punctuation_chars=True)` with
`whitespace_split = True` (the tokenizer construction
`merge-allow-gate.sh`/`spawn-allow-gate.sh` already use, minus their
hook-specific `OPERATOR_CHARS`/strict-shape allowlist logic, which
belongs to a narrower permission-granting job neither this issue's three
hooks have). Verified this session (`docs/issue-882/reports/implementation/survey.md`,
"## Candidate fix") against all five of the issue's inputs: `punctuation_chars=True`
splits `(git commit -m x)` into `['(', 'git', 'commit', '-m', 'x', ')']`
— `git` and `commit` land as standalone tokens again — while still
correctly matching `git -c ... commit` (multiple global options,
#866/#876's fix) and still correctly rejecting `git commit-tree`
(#866's bycatch improvement). All five inputs land on the correct
judgment (`True, True, True, True, False`) with one tokenizer change,
closing the paren gap without reopening either prior gap — the survey's
own "repeat-hole" table names this explicitly as the thing being
checked for, not assumed.

Considered regex-stripping a leading `(`/trailing `)` from the command
string before calling the existing `shlex.split`, instead of switching
tokenizer constructions. Rejected: narrower than the tokenizer swap — it
only handles a bare parenthesis-wrapped command, not other
punctuation-fused shapes a shell also treats as a subshell/group
boundary (e.g. `{git commit -m x;}`, a brace-grouped command list), and
it invents a new, untested transformation instead of reusing the
`punctuation_chars=True` construction issue #824/#834 already landed and
tested for exactly this class of problem (issue's own decision point 1
directs reading that design first, "실제로 돌려보고 정하라"). The
tokenizer swap generalizes to any punctuation character shlex already
tracks (`()<>|&;`), not just one hand-picked case.

Re-affirmed, not re-derived, the #876 shared-helper rejection (issue's
decision point 3): `hooks.json` still invokes every hook by absolute
`${CLAUDE_PLUGIN_ROOT}/hooks/<script>.sh` path with no guaranteed
consumer-repo checkout (re-checked this session, unchanged); this issue
doesn't touch `gates/role_spec_shape.py`'s import-with-fallback situation
or add a fourth hook to the family; the fail-open-on-missing-dependency
risk a shared helper would reintroduce is unchanged in kind. Full
evidence trail: `docs/issue-882/reports/implementation/survey.md`, "The
shared-helper question".

## Accumulation

This change does not grow the duplication COUNT (still three hook
files, same as after #876) — it changes what is duplicated: a five-line
`shlex.shlex(...)`/`whitespace_split`/`list(...)` tokenizer construction
replaces the one-line `shlex.split(cmd)` call, in the same three places.
Judged deliberately in `## Rationale` above and
`docs/issue-882/reports/implementation/survey.md` ("The shared-helper
question"), not defaulted into.

This is the second consecutive fix to this exact snippet (#866 -> #876
port -> this issue's tokenizer swap). If a third design change to the
trigger-check LOGIC itself (not just a new call site) is needed again,
it still has to land by hand in three files — an accepted, explicit cost
of staying fail-open-safe against a hook family with no guaranteed
shared-module checkout, not an unnoticed one (same reasoning #876's own
`## Accumulation` recorded, re-applied here because the constraint that
grounds it — `hooks.json`'s `${CLAUDE_PLUGIN_ROOT}` invocation path — is
unchanged). A fourth hook joining this family, or the snippet outgrowing
what one hook-header comment can explain, remains the signal to revisit
this decision (e.g. a generated/templated hook body checked in per-hook),
not a reason to extract a shared import now.

## What will be done

1. In all three hooks (`spec-index-preflight.sh`,
   `gate-registration-guard.sh`, `role-axis-completeness-guard.sh`),
   replace the `tokens = shlex.split(cmd)` / `except ValueError:
   sys.exit(0)` / `if "git" not in tokens or "commit" not in tokens:
   sys.exit(0)` block with the `shlex.shlex(cmd, posix=True,
   punctuation_chars=True)` + `whitespace_split = True` construction,
   keeping the same fail-open `except ValueError: sys.exit(0)` wrapper
   and the same `"git" not in tokens or "commit" not in tokens` check.
   `shlex` is already imported in all three files — no import-line
   change. Update each file's header comment to cite issue #882 and the
   punctuation-fused bypass this closes, alongside the existing #866/#876
   citations (not replacing them — the `git -c ...` history stays
   documented).
2. In `test_spec_index_preflight.py`, update the pure-Python
   `is_git_commit_invocation` mirror to the same tokenizer construction,
   and add one `(git commit -m x)`-shaped regression case (and a
   `cd /tmp && git commit -m x`-shaped case if not already covered)
   asserting `True`, alongside the five existing cases (all re-run
   unchanged to confirm no re-regression).
3. In `test_gate_registration_guard.py` and
   `test_role_axis_completeness_guard.py`, add one real end-to-end
   regression case each: a staged violation (unregistered gate module /
   zero-owner axis, matching each file's existing fixture convention)
   committed via a paren-wrapped `(git commit -m msg)` invocation,
   asserting `returncode == 2` — the shape that silently passed before
   this fix.
4. Run each hook's own test file, then `on-the-record/hooks/` as a
   whole, then `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
   in two isolated `git worktree` checkouts (this branch's tip,
   `origin/main`) and diff the failure sets.
5. Dispatch one before-landing `warrant:warrant-hunter` (stance rotation
   per `.warrant-hunt.count`), wait for and consume its result in this
   same turn (contract v3 s22 — headless single-shot).
6. Write `docs/issue-882/reports/implementation/resolution.md` with the
   five-input x three-hook judgment table (issue's decision point 2), the
   repeat-hole visibility note, the shared-helper re-affirmation, the
   hunt, and the verification transcripts.

## Out of scope

- Redesigning the trigger-detection approach beyond the tokenizer
  construction itself (e.g. a from-scratch shell-metacharacter-splitting
  regex) — the issue directs evaluating the already-landed
  `punctuation_chars=True` design first, and it fully closes the known
  gap without a new design.
- `on-the-record/hooks/pr-preflight.sh` — a concurrent session's write
  set; explicitly excluded by this issue's own instructions.
- The `git -c <key>=<value> commit` bypass — already closed (#866/#876),
  unaffected by this change (re-verified as one of the five inputs, not
  reopened).
- The commit-time-only design limitation (a GitHub server-side
  squash-merge commit is structurally invisible to a `PreToolUse` hook)
  — already recorded by #866, not reopened by this issue.
- A shared helper module across the three hooks — judged and rejected
  again, see `## Rationale`.
- Other punctuation-fused shapes beyond what `punctuation_chars=True`'s
  default character set (`()<>|&;`) already covers (e.g. a shape
  requiring a custom `punctuation_chars` string) — not reported by this
  issue, not evaluated here.

## How you'll know it worked

- All three hooks deny a `(git commit -m x)`-shaped invocation carrying a
  staged violation their existing plain-`git commit` case already
  denies, with matching stderr content.
- The issue's own five-input table, re-run against the chosen fix and
  recorded per hook, shows the correct judgment on every cell — no input
  that was correctly detected before this change becomes falsely
  undetected after it (the repeat-hole check this issue exists to make
  visible).
- `python3 -m pytest on-the-record/hooks/ -q` passes in full, including
  the new cases.
- The branch-vs-`origin/main` worktree comparison of
  `gates/ tests/ on-the-record/hooks/` shows the branch's failure set is
  empty (or strictly smaller than, never a superset of) `origin/main`'s
  failure set, with no failure introduced by this change.
