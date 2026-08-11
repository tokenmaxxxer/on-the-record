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
contrast, mechanically decidable — strict validation stays the primary
fix.

Considered (and drafted first, in this proposal's own earlier revision)
mirroring `on-the-record/hooks/spawn-allow-gate.sh`'s shipped check
verbatim: strip single-quoted spans via `re.sub(r"'[^']*'", "", rest)`,
then regex-search the remainder for a forbidden-operator set. **Rejected
after the after-proposal warrant hunt reproduced a live bypass against
this exact design**
(`docs/issue-824/reports/implementation/hunt-strict-merge-allow-validation.md`):
the regex pairs every literal `'` character left-to-right regardless of
context, so bash's standard backslash-escaped-quote-outside-quotes idiom
(`\'`) desyncs the regex's assumed quote state from bash's real one — a
payload like `42 \';evil;'X'` gets `stripped` to a string with no
forbidden operator visible, while real bash (verified live, this
session, with `evil` stubbed as a shell function) executes `evil` as a
fully separate command. This session further confirmed
(`docs/issue-824/reports/implementation/survey.md`'s sibling finding is
extended here) that `spawn-allow-gate.sh`'s own shipped copy of this
exact regex is equally fooled by the same payload shape — see Out of
scope below. Rejected in favor of the corrected design immediately
below, which tokenizes with an engine that actually tracks bash's quote/
escape state instead of hand-rolling a quote-pairing regex.

**Corrected design:** use `shlex.shlex(cmd, posix=True,
punctuation_chars=True)` (Python's own POSIX-mode shell tokenizer,
enabled to split on shell control-operator punctuation — `();<>|&`
including compound clusters like `&&`/`||`, confirmed by inspecting
`shlex.shlex(..., punctuation_chars=True).punctuation_chars` in this
session) instead of the regex-based quote-stripping. Re-tested against
the exact hunt payload: this tokenizer correctly reports the injected
`;` as its own live token (`['42', "'", ';', 'evil', ';', 'X']`) rather
than hiding it inside a misclassified quoted span, and correctly leaves
legitimate flag forms (`--squash`, `-R owner/repo`) as ordinary
whitespace-delimited tokens with no operator tokens present — verified
live, this session, for both cases. `shlex`'s `posix=True` mode is
documented to implement POSIX-shell backslash/quote handling, which is
exactly the state-tracking the naive regex lacked.

## What will be done

- `on-the-record/hooks/merge-allow-gate.sh`:
  - Reject the whole command outright (unreached, no allow) if a
    backtick, `$(`, or a literal newline appears anywhere in it — no
    legitimate `gh pr merge` invocation needs command/process
    substitution or a multi-line command, so this is a plain substring
    check, independent of quoting.
  - Tokenize the full command with `shlex.shlex(cmd, posix=True,
    punctuation_chars=True)` (`whitespace_split = True`); a
    `ValueError` (unbalanced quoting) is unreached, same as today's
    fail-open posture.
  - Walk the resulting token list for the one recognized shape: either
    `["gh", "pr", "merge", ...args]` directly, or `["cd", DIR, "&&",
    "gh", "pr", "merge", ...args]` — and reject if any *other* token in
    the list is composed entirely of `shlex`'s punctuation characters
    (`();<>|&`, e.g. `;`, `&&`, `|`, `<`) — i.e. the one `&&` from a
    recognized `cd DIR &&` prefix is the only punctuation-only token
    ever tolerated, and only in that exact position.
  - Only after both checks pass, extract the PR number from the
    (unstripped) remainder using the existing url/`-R`/`--repo`/
    plain-number regex logic, unchanged.
  - Any command failing a check falls through to the existing plain
    `exit 0` (no allow, no deny) — unchanged fallback behavior, human
    prompt preserved.
- `on-the-record/hooks/test_merge_allow_gate.py`: add regression cases
  for both chain directions (`gh pr merge 42 && <cmd>` and `<cmd> ; gh
  pr merge 42`), a semicolon and a pipe variant, and the hunt's
  backslash-escaped-quote payload (`gh pr merge 42 \';evil;'X'`) —
  asserting no `allow` decision for all of them; keep the existing 8
  cases passing to confirm the pure form (bare, with a trailing flag,
  with `-R owner/repo`, with a `cd DIR &&` prefix) is unaffected.
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
- **`on-the-record/hooks/spawn-allow-gate.sh` carries the identical
  bypass the after-proposal hunt found** (same shipped
  `re.sub(r"'[^']*'", "", rest)` regex, same backslash-escaped-quote
  desync): applying that file's own exact check to a `python3 <...
  spawn.py> ... \';evil;'X'`-shaped remainder reports no forbidden
  operator reachable (verified live, this session, same method as the
  hunt record). This is a currently-armed, currently-shipped hook, not
  a draft — more urgent than the other two flagged findings above, but
  still a different file outside this issue's frozen write set. Flagged
  here as the strongest candidate for an immediate follow-up issue, not
  fixed here.

## How you'll know it worked

`python3 -m pytest on-the-record/hooks/test_merge_allow_gate.py -q`
passes, including new cases proving a `gh pr merge <n> && <anything>`
(and `;`/`|` variants, either chain direction, plus the hunt's
backslash-escaped-quote payload `\';evil;'X'`) command gets no `allow`
decision while a pure `gh pr merge <n>` (bare, flagged, or `cd`-prefixed)
still does when READY. `python3 -m pytest gates/ tests/
on-the-record/hooks/ -q` reports 0 failures.
