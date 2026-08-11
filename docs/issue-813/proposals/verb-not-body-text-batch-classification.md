---
status: proposed
files:
  - on-the-record/hooks/impact-guard.sh
  - on-the-record/hooks/test_impact_guard.py
  - docs/issue-813/reports/implementation/survey.md
  - docs/issue-813/proposals/verb-not-body-text-batch-classification.md
---

## Request

`impact-guard.sh` classifies a Bash command as a batched-merge approval
act by counting `gh pr merge` substring matches across the *entire raw
command string* — including the contents of a `--body`/`--body-file`/
here-string argument. A `gh issue comment`/`gh pr comment` whose body
text merely discusses or quotes the merge verb (e.g. design notes on
merge automation) gets miscounted as a batch and denied, even though no
merge was invoked. Fix it to classify by the actual invoked command
verb, not by merge-verb literals appearing inside a quoted argument
body, while a genuine batch of two real merge invocations must still be
caught.

## Constraints

- Only `on-the-record/hooks/impact-guard.sh` and its test file are in
  scope — the sibling `merge-allow-gate.sh` hook has the same substring-
  scan shape but is out of scope (see Out of scope).
- Must not change the hook's fail-open posture: an unparseable command
  (e.g. unbalanced quoting) still falls through without denying.
- Must not weaken true-positive detection: a genuine two-`gh pr merge`
  compound command must still be denied when a high-reversibility
  proposal is open.

## Rationale

**Considered: strip quoted spans with a regex before counting, then
apply the existing substring regex to what remains.** Rejected —
`docs/issue-824/proposals/strict-merge-allow-validation.md`'s own
"Rejected" section already worked through this exact alternative for the
sibling `merge-allow-gate.sh` hook and found a hand-rolled quote-pairing
regex "equally fooled by the same payload shape" as the naive approach
(it cannot correctly track bash's quote/escape state across nested or
escaped quotes). The same defect applies here — a regex-based strip is
not more correct than the regex it is trying to correct.

**Chosen: tokenize with `shlex.shlex(cmd, posix=True,
punctuation_chars=True)`, then count adjacent `("gh", "pr", "merge")`
token triplets.** This is Python's own POSIX-mode shell tokenizer — it
tracks quote/escape state correctly (issue #824 already validated this
for the sibling hook), so a quoted `--body` argument collapses into a
single token regardless of what merge-verb text it contains, while a
real invocation's verb tokens stay three separate bare words. This
reuses a tokenizer already proven correct in this repo rather than
inventing a second ad hoc parser.

## What will be done

- Replace `impact-guard.sh`'s `merge_count = len(re.findall(r"\bgh\s+pr\s+merge\b", cmd))`
  with a `_count_merge_invocations(cmd)` helper that tokenizes via
  `shlex.shlex(cmd, posix=True, punctuation_chars=True)` and counts
  adjacent `("gh", "pr", "merge")` token triplets. Unparseable
  (`ValueError`) commands return 0, preserving the existing fail-open
  posture (a command that cannot be tokenized cannot be proven to be a
  batch, so it is not treated as one).
- Add a regression test,
  `t_comment_body_mentioning_merge_verb_is_not_misclassified_as_a_batch`,
  to `on-the-record/hooks/test_impact_guard.py`: a `gh issue comment
  --body` mentioning `gh pr merge` twice must pass (exit 0) even with a
  high-reversibility proposal open.
- Leave the existing `t_batch_with_high_impact_proposal_is_denied` test
  as the true-positive-still-denied regression pin — it already covers a
  genuine two-`gh pr merge` compound command and needs no change under
  the new counting logic.

## Out of scope

- `merge-allow-gate.sh`'s own `re.search(r"\bgh\s+pr\s+merge\b", cmd)`
  check has the same substring-scan shape but is a different hook with
  its own open proposal (`docs/issue-824/proposals/
  strict-merge-allow-validation.md`) already targeting it — fixing it
  here would exceed this issue's write set.
- Heredoc (`<<EOF ... EOF`) bodies are not addressed — the issue names
  `--body`/`--body-file`/here-string specifically, all of which are
  quoted-argument shapes the chosen tokenizer already handles; an
  unquoted heredoc body is a different shape not raised by the issue.

## How you'll know it worked

`python3 on-the-record/hooks/test_impact_guard.py` passes all 5 tests,
including the new false-positive-now-passes test and the pre-existing
true-positive-still-denied test, both exercised live against the real
hook script (not a reimplementation).
