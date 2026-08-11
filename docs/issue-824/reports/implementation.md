---
code_under_review:
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/test_merge_allow_gate.py
  - docs/specs/generated-paths.md
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #824

## Summary of work

Implemented the approved phase-1 design in
`docs/issue-824/proposals/strict-merge-allow-validation.md`, approved via
the issue-level comment `APPROVE issue-824/implementation` (single-account
mode, `jjongkwann`, listed in `docs/specs/approvers.md`).

canonical: `on-the-record/hooks/merge-allow-gate.sh` (this build's own
edit, read directly) — the loose `re.search(r"\bgh\s+pr\s+merge\b", cmd)`
substring check is now a strict command-shape check that runs before any
identity/READY check: the command is rejected outright (falls through to
the existing plain `exit 0`) if a backtick, `$(`, or a literal newline
appears anywhere in it; otherwise it is tokenized with
`shlex.shlex(cmd, posix=True, punctuation_chars=True)`
(`whitespace_split = True`; a `ValueError` for unbalanced quoting falls
through the same way); the token list must be exactly
`["gh","pr","merge",...args]` or
`["cd",DIR,"&&","gh","pr","merge",...args]` with no other token composed
entirely of shell operator characters (`();<>|&` plus `;`) anywhere else
in the list. Only after both checks pass does the existing (unchanged)
`cd`/URL/`-R`/`--repo`/plain-number regex extraction and
`gates/landing_readiness.py` READY check run.

canonical: `docs/specs/generated-paths.md` (this build's own edit, read
directly) — a `merge-allow-gate.sh` row was added; see `## Rationale for
deviations` below for its classification.

canonical: `on-the-record/hooks/test_merge_allow_gate.py` (this build's
own edit, read directly) — new regression cases were added:
`t_chain_appended_with_double_ampersand_is_not_allowed` (append
direction, `&&`), `t_chain_prepended_with_semicolon_is_not_allowed`
(prepend direction, `;`), `t_chain_appended_with_semicolon_is_not_allowed`
(semicolon variant), `t_chain_appended_with_pipe_is_not_allowed` (pipe
variant), `t_backslash_escaped_quote_payload_is_not_allowed` (the hunt's
`\';evil;'X'` payload), and `t_cd_prefixed_ready_pr_still_gets_allow`
(a green case — the `cd DIR &&` shape still reaches `allow` when READY).
Every pre-existing test function in the file was kept unmodified.

derived: `python3 -m pytest on-the-record/hooks/test_merge_allow_gate.py -q`
```
..............                                                           [100%]
14 passed in 0.71s
```

## Why

canonical: `on-the-record/hooks/merge-allow-gate.sh` before this build
(git history, read via `git show 3d54b72:on-the-record/hooks/merge-allow-gate.sh`)
and `docs/issue-824/reports/implementation/survey.md`'s item 1 — the
shipped hook (issue-810, PR #816) grants `permissionDecision: "allow"`,
which skips the harness's human confirmation prompt, for the entire
`tool_input.command` string whenever `gh pr merge` appears anywhere in
it, so a chained command (either direction, any chain operator) gets the
whole string auto-approved with no human ever seeing the appended or
prepended part.

canonical: the survey's item 2 (`docs/issue-824/reports/implementation/survey.md`)
— the hook also landed with no row in `docs/specs/generated-paths.md`,
failing `gates/test_generated_paths.py`.

## Upstream

Based on: `docs/issue-824/proposals/strict-merge-allow-validation.md`
(phase-1 proposal, itself built on
`docs/issue-824/reports/implementation/survey.md` and revised after
`docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md`'s
after-proposal hunt finding).

## Rationale for deviations

canonical: `docs/issue-824/proposals/strict-merge-allow-validation.md`'s
`## What will be done` section (read directly) — it specified the
`docs/specs/generated-paths.md` row as `n/a | reads/validates only, no
write call`, reasoning by analogy to `spawn-allow-gate.sh`'s row (same
shape claim: no `write_text`/`open(...,"w")`/`.mkdir(`/`shutil.copy`/
`move` call in the file).

canonical: `on-the-record/hooks/merge-allow-gate.sh`'s
`_checkout_resolve()` function (read directly, unchanged by this build —
it predates issue #824) — it runs `mkdir -p "$(dirname "$own")"` and
`git clone -q https://github.com/tokenmaxxxer/on-the-record.git "$own"`,
the same shared-checkout-clone pattern `docs/specs/generated-paths.md`
already records as `out-of-tree` for `impact-guard.sh`,
`decision-queue-stopgate.sh`, `self-update.sh`, and `directive.sh`.

canonical: `gates/test_generated_paths.py`'s `_WRITE_CALL_RE` (read
directly) matches `mkdir -p`/`git clone`, so it classifies
`merge-allow-gate.sh` as a writer, not a `n/a` no-writer — see `## What
did not work` for the live failure this produced. The row was corrected
to `out-of-tree`, its verdict text mirroring the four sibling rows above
(same shared-checkout-clone pattern, never inside the target repo's
worktree).

## What did not work

canonical: live pytest run, this session, fence immediately below — the
`docs/specs/generated-paths.md` row was first added exactly as the
proposal specified it (`n/a | reads/validates only, no write call`).

```
$ python3 -m pytest gates/test_generated_paths.py -q
....F                                                                    [100%]
FAILED gates/test_generated_paths.py - AssertionError: merge-allow-gate.sh 의
기록된 분류 'n/a' 가 out-of-tree/issue-scoped 어느 쪽도 아니다.
```

The row's classification was replaced with `out-of-tree` (see `##
Rationale for deviations` above).

derived: `python3 -m pytest gates/test_generated_paths.py -q`
```
....                                                                     [100%]
4 passed in 0.02s
```

## Hunt cadence

canonical: `docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md`'s
"after-proposal — stance 0" section (read directly) — the draft design's
`re.sub(r"'[^']*'", "", rest)` quote-stripping regex desyncs from bash's
real quote state on a backslash-escaped-quote payload.

closed_checks:
- after-proposal hunt, stance 0: the corrected
  `shlex.shlex(posix=True, punctuation_chars=True)` design is what
  `on-the-record/hooks/merge-allow-gate.sh` (this record's
  `code_under_review`) implements; the exact hunt payload is now the
  `t_backslash_escaped_quote_payload_is_not_allowed` regression test, in
  the passing test run cited under `## Summary of work` above.

canonical: `docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md`'s
"before-landing — stance 1" section (read directly) — a composition
mismatch between `merge-allow-gate.sh`'s new precise shlex tokenizer and
`on-the-record/hooks/impact-guard.sh`'s coarse
`re.findall(r"\bgh\s+pr\s+merge\b", cmd)` substring count, on the same
`tool_input.command`, left open by this build (see `## Open findings`
below).

## Open findings

canonical: `docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md`'s
"before-landing — stance 1" section (read directly, live-fire and
direct-extraction reproduction both included there) — `impact-guard.sh`'s
batch-count check treats a single, legitimate merge command as a
multi-invocation batch whenever the merge-target phrase also appears
elsewhere in the same command text (e.g. inside a `--subject "..."`
argument), and denies it outright, while `merge-allow-gate.sh`'s new
tokenizer, on the identical string, correctly recognizes the single-merge
shape. This is the same substring-match defect class item 1 of this
issue closes, in a different file and the opposite failure direction
(false deny, not false allow).

canonical: `docs/issue-824/proposals/strict-merge-allow-validation.md`'s
`## Out of scope` section (read directly) — `impact-guard.sh`'s
substring-based batch-count defect was already named there as a
follow-up-issue candidate, before the before-landing hunt ran.
`on-the-record/hooks/impact-guard.sh` is outside this issue's frozen
write set.

next steps: file a follow-up GitHub issue against
`on-the-record/hooks/impact-guard.sh`'s substring-based batch counting
(the same treatment `on-the-record/hooks/spawn-allow-gate.sh`'s
backslash-escaped-quote bypass already got in this issue's own proposal's
`## Out of scope` section, which the orchestrator is issuing separately
per this round's task instructions).

resolution path: a new issue, scoped to `impact-guard.sh` only, replacing
its `re.findall` substring count with a tokenization-based count (e.g.
the same `shlex.shlex(posix=True, punctuation_chars=True)` approach this
build used) so it counts real invocations, not textual echoes.

## Acceptance

check 1 — the issue's own acceptance item ("no auto-allow for a chained
command, either direction, pure form unaffected"): the passing test run
cited under `## Summary of work` above covers both chain directions, the
semicolon and pipe variants, the hunt's backslash-escaped-quote payload,
and the pure-form green cases (bare, `--squash` flag, `-R owner/repo`
flag, `cd DIR &&` prefix).

check 2 — `main` restored to green
(`python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` reports no
failures):

canonical: live pytest run, this session, fence immediately below, run
against this build's own uncommitted working tree (pre-commit) —

```
$ python3 -m pytest gates/ tests/ on-the-record/hooks/ -q
1 failed, 1203 passed, 2 skipped, 1 xfailed in 185.76s (0:03:05)
FAILED tests/test_gates.py::t_rulebook_version_is_recorded
```

canonical: `spawn.py`'s `rulebook_dir`/`rulebook_version` functions (read
directly) — the one failure is `spawn.rulebook_version()`'s own
dirty-tree check (`git status --porcelain` against this exact checkout)
tripping on this build's own staged-but-uncommitted files, the same
self-referential artifact `docs/issue-759/reports/implementation.md` and
`docs/issue-741/reports/implementation.md` already documented for the
same test — not caused by this build's actual code changes. A
post-commit re-run, expected to show zero failures once this change is
committed, is pasted in a follow-up commit to this record, the same
two-commit convention issue-759 used
(`git log --oneline -- docs/issue-759/reports/implementation.md` shows
commits `dd651ed` then `7091f12`).
