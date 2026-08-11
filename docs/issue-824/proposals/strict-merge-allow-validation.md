---
status: proposed
files:
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/test_merge_allow_gate.py
  - docs/specs/generated-paths.md
  - docs/issue-824/reports/implementation.md
---

# Proposal — issue #824 step 1, implementation

## Request

Fix two defects in `on-the-record/hooks/merge-allow-gate.sh` (landed by
issue-810 PR #816): (1) it grants `permissionDecision: allow` for any
Bash command that merely *contains* `gh pr merge <n>` as a substring,
so `gh pr merge 42 && <anything>` gets the whole chained command
auto-approved and the harness's human-confirmation prompt skipped; (2)
it landed with no row in `docs/specs/generated-paths.md`, failing
`gates/test_generated_paths.py`.

## Constraints

- Do not touch `gates/landing_readiness.py`'s READY predicate — out of
  scope per the issue.
- Do not touch the plugin install-cache refresh mechanism — issue-741's
  territory, out of scope per the issue.
- Do not touch `on-the-record/hooks/impact-guard.sh` or
  `on-the-record/hooks/claim-scan-preflight.sh` — both have a related
  loose-match defect (confirmed live for the latter during this issue's
  survey), but neither is in this issue's frozen write set; each is a
  separate-issue candidate.
- Every existing `test_merge_allow_gate.py` case must keep passing
  unmodified in behavior, including the two that drive a merge command
  with a trailing flag (`--squash`) or a `-R owner/repo` flag — a fix
  that only accepts the bare `gh pr merge <n>` form would regress
  legitimate use.

## Rationale

Considered leaving the `allow` grant in place and only tightening the
regex used to find `gh pr merge` (e.g. requiring it at the start of the
string). Rejected: a regex anchored on position still cannot certify
that nothing *else* is chained onto the command — `gh pr merge 42 &&
evil` starts with the target string too. The check has to reason about
the whole command's shape, not just where the match begins.

Considered falling back to silence (drop the `allow` branch entirely,
`exit 0` always, relying on the harness's normal confirmation prompt) —
the alternative the issue explicitly asks to weigh against strict
validation. Rejected as the primary fix, on the strength of two
in-repo precedents surfaced during this issue's survey
(`docs/issue-824/reports/implementation/survey.md`): issue-476's
`claim-scan-preflight.sh` put `allow` on an inherently fuzzy branch
("does this text contain an unsubstantiated claim?") and that branch
cannot be tightened into a mechanical exact-match — silence is the only
safe answer there. `merge-allow-gate.sh`'s target shape ("is this
command *exactly* `gh pr merge <n>` and nothing else?") is, by
contrast, mechanically decidable, and this exact repo already has a
proven, warrant-hunted implementation of that decision for a sibling
hook: `on-the-record/hooks/spawn-allow-gate.sh` (issue-810 SCOPE
EXTENSION 2, `#823`) strips an optional `cd DIR &&` prefix and then
rejects the remainder if any shell chaining/substitution operator is
reachable outside single-quoted spans, before ever matching its target
shape. Reusing that same, already-hardened pattern here closes the
bypass without regressing issue-810's actual point — the orchestrator
still merges a READY PR with no manual prompt, it just cannot smuggle a
second command through the same grant.

## What will be done

- `on-the-record/hooks/merge-allow-gate.sh`: require a validated `cd
  DIR &&` prefix (DIR restricted to characters outside the forbidden
  metacharacter set, so the prefix itself cannot smuggle a chained
  command) followed by an exact `gh pr merge <args>` invocation — reject
  the whole command if any of `&&`, `;`, `|`, `` ` ``, `$(`, `<`, `>`, or
  a newline is reachable outside single-quoted spans anywhere in the
  remainder, then `shlex.split` the remainder and require its first
  three tokens to be exactly `gh`, `pr`, `merge` — before extracting the
  PR number the existing url/`-R`/`--repo`/plain-number logic already
  handles. Any command failing either check falls through to the
  existing plain `exit 0` (no allow, no deny) — unchanged fallback
  behavior, human prompt preserved.
- `on-the-record/hooks/test_merge_allow_gate.py`: add regression cases
  for both chain directions (`gh pr merge 42 && <cmd>` and `<cmd> ; gh
  pr merge 42`) asserting no `allow` decision, plus a semicolon and a
  pipe variant; keep the existing 8 cases passing to confirm the pure
  form (bare, with a trailing flag, with `-R owner/repo`, with a `cd
  DIR &&` prefix) is unaffected.
- `docs/specs/generated-paths.md`: add a `merge-allow-gate.sh` row,
  `n/a | reads/validates only, no write call`, matching the row already
  recorded for `spawn-allow-gate.sh` (same shape: no `write_text`/
  `open(..., "w")`/`.mkdir(`/`shutil.copy`/`move` call in the file).
- Run `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` and
  confirm the current single failure
  (`gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint`)
  is gone with no new failures.
- Write `docs/issue-824/reports/implementation.md`, this role's phase-2
  record, citing this proposal and the survey as upstream basis.

## Out of scope

- `gates/landing_readiness.py`'s READY predicate.
- The plugin install-cache refresh mechanism (issue-741).
- `on-the-record/hooks/impact-guard.sh` (the reverse-direction false
  positive the issue's own comment reports, and reproduced live again
  during this issue's proposal-validation step — a batch-count
  substring-match defect, same root shape as item 1 but a different
  file and a different failure direction).
- `on-the-record/hooks/claim-scan-preflight.sh`'s still-live
  `allow`-on-warn-branch defect (issue-476), confirmed still present
  during this issue's survey — flagged as a follow-up-issue candidate,
  not fixed here.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_merge_allow_gate.py -q`
passes, including new cases proving a `gh pr merge <n> && <anything>`
(and `;`/`|` variants, either chain direction) command gets no `allow`
decision while a pure `gh pr merge <n>` (bare, flagged, or `cd`-prefixed)
still does when READY. `python3 -m pytest gates/ tests/
on-the-record/hooks/ -q` reports 0 failures.
