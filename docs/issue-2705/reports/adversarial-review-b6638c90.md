---
issue: 2705
role: adversarial-review-b6638c90
author: adversarial-review-b6638c90
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: on-the-record/hooks/gate-registration-guard.sh at PR #2774 head (0d9858b0), the `_pending_add_segments`/`_new_frame`/`_match_untracked` cwd model
loop_state: landed
type: verification
breaking: false
verdict: CHANGES — the per-frame cwd model is still one shape behind. `cd -`, `popd` on an empty stack, and matched `pushd`/`popd` are correctly modeled and live-verified. But bare `pushd` (no argument — bash swaps the top two stack entries) and `pushd +N`/`pushd -N` (stack rotation) are unhandled: bare `pushd` silently no-ops instead of swapping, and `pushd +N` is parsed as a literal directory named `+N`, fabricating a bogus cwd. Both are live-reproduced as real, silent bypasses of the guard against the actual hook script, not just model mismatches. This is a fourth round finding a fresh cwd-tracking gap in the pushd/popd family the PR itself claims to have closed — the PR's own round-3 test only exercises a *matched* pushd-then-popd pair, never bare `pushd`, `pushd +N`, or `pushd -N` alone.
upstream:
  - path: PR #2774 (issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b), head 0d9858b02aba95b30be4b99db3227cb138629969
    sha: 0d9858b02aba95b30be4b99db3227cb138629969
  - path: PR #2763 (issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99), head f943d3fc9fa052e006072eed471db4cc535f6313
    sha: f943d3fc9fa052e006072eed471db4cc535f6313
---

# issue-2705 — adversarial-review-b6638c90 record

## What was done

skill-verdict: adversarial-review — applied: invoked; this session is
structurally the independent evaluator the skill describes (separate
session, no access to the builder's reasoning, artifact-only input via
`gh pr view 2774`/`gh issue view 2705`) — used its emphasis on
re-deriving rather than trusting the artifact's own claims to justify
building a standalone probe harness and real bash/git ground truth
instead of accepting the PR's stated test results.

Independently verified PR #2774 (`issue-2705: finish the cwd model in
gate-registration-guard.sh (cd -, symlink, pushd/popd)`), which
supersedes PR #2763. canonical: `gh pr view 2774 --json title,body,commits,files,headRefName,baseRefName,state`
and `gh issue view 2705 --json title,body,comments`, both read in full
this session. Checked out both PR heads read-only via `git worktree add
/tmp/wt-2774 pr-2774` / `/tmp/wt-main main` (no writes to either, both
worktrees removed at end of session via `git worktree remove --force`),
extracted the guard's `_shell_segments`/`_new_frame`/
`_pending_add_segments`/`_match_untracked` functions into an importable
module (`/tmp/grg-funcs.py`, a scratch file outside repo history, built
via `sed -n '1,2p;116,312p'` of the extracted PY heredoc body — verified
`python3 -c "import ast; ast.parse(...)"` succeeds), and probed it
directly in Python against the ten shapes named in the task: `cd -`
twice, `popd` on an empty stack, `pushd` with no argument, `pushd
+N`/`-N` rotation, `cd --`, a symlink chain, a subshell `pushd` that
never pops, `popd` inside a subshell affecting the outer frame, and
CDPATH.

derived: `python3 /tmp/probe2.py` (scratch probe script, not part of
this repo) — result:
```
cd - twice -> [('/b', ['x'])]
popd empty -> [('/repo', ['x'])]
pushd no-arg -> [('/other', ['x'])]
pushd +1 -> [('/other/+1', ['x'])]
pushd -0 -> [('/other', ['x'])]
cd -- normal -> [('/tmp', ['x'])]
cd symlink chain -> [('/tmp/tmpd8emq6iv/real', ['x'])]
subshell pushd no pop -> [('/repo', ['x'])]
subshell popd -> [('/tmp', ['x'])]
plain relative cd -> [('/repo/sub', ['x'])]
```

Cross-checked every probe against real bash/git ground truth in a real
throwaway repo (`mktemp -d`, `git init`, `mkdir tmp other`), not just the
parser's self-consistency:

- `cd -` twice: derived: `bash -c 'cd repo && cd tmp && cd ../other && cd - && cd - && pwd'` — result: `repo/other`. Matches the parser's `/b` (final = second dir after two swaps). Correct.
- `popd` empty: bash's own `dirs` stack starts as a single entry (`[cwd]`); `popd` with `len(dirs) <= 1` is bash's own "directory stack empty" case (no change). Parser matches (`/repo` unchanged) per the probe output above.
- `pushd` no-arg: derived: `bash -c 'cd repo && pushd tmp && pushd ../other && pushd && pwd'` — result: `repo/tmp`. Parser gives `/other` (probe output above) — no swap happened. Mismatch, confirmed bug.
- `pushd +1`: derived: `bash -c 'cd repo && pushd tmp && pushd ../other && dirs -v; pushd +1 && pwd'` — result: `dirs -v` shows stack `(0: other, 1: tmp, 2: repo)`; `pushd +1 && pwd` gives `repo/tmp`. Parser gives `/other/+1` (probe output above) — treats the literal token `+1` as a relative path segment under `/other`, fabricating a directory that doesn't exist. Mismatch, confirmed bug, and worse than a no-op since it invents a bogus cwd.
- `pushd -0`: derived: `bash -c 'cd repo && pushd tmp && pushd ../other && pushd -0 && pwd'` — result: `repo` (rotates the last stack entry to the top). Parser's `-0` starts with `-`, gets filtered out as if it were a flag, and no-ops to `/other` (probe output above). Mismatch, confirmed bug.
- `cd --`: `cd -- foo` — the `--` token starts with `-`, gets filtered by the same generic flag-stripping the `-`-prefix check does, and `foo` is picked up as the target. Coincidentally correct for the plain case (probe output above: `/tmp`).
- symlink chain: kernel `chdir()` always resolves symlinks at the OS level regardless of bash's own logical `$PWD` bookkeeping, so a child process's (git's) actual `getcwd()` is always the realpath — the parser's `os.path.realpath` matches what git would actually see. Probe output above resolves through both symlink hops to the real directory. Correct.
- subshell `pushd` without popping / `popd` from inside a subshell: both correctly do not leak to the outer frame — `stack.append({...copy...})` on `(` and discard on `)` mirrors bash's own per-subshell dir-stack copy. Probe output above: outer cwd stays `/repo` after an un-popped subshell `pushd`, and stays `/tmp` (unaffected) after a subshell `popd` following an outer `pushd /tmp`.
- CDPATH: not modeled anywhere in the parser — derived: `grep -rn CDPATH /tmp/wt-2774 --include="*.sh" --include="*.py"` — result: zero hits — and not disclosed as an open edge in the PR's own record. Left as a minor, low-severity gap in Open findings below — no evidence CDPATH is ever set in this harness's session environment, so likelihood of it mattering in practice is low, unlike the pushd gaps.

### Live-fire of the bare-pushd bypass against the real hook script

Live-fired the bare-`pushd` bypass against the real, unmodified hook
script (not just the extracted-function probe), to confirm it is a real,
silently-passing bypass and not merely a model/ground-truth mismatch
with no practical consequence. Created an untracked probe file at the
path `gates/probe_unregistered_gate.py` inside the now-removed
`/tmp/wt-2774` worktree (a scratch worktree checkout of PR #2774, not a
path in this repo's own tree — the worktree was deleted via `git
worktree remove --force` at end of session, so that path no longer
exists anywhere and is not a claim about this repo's tracked files).

derived:
```
$ cat /tmp/payload.json
{"tool_name": "Bash", "tool_input": {"command": "pushd gates >/dev/null && pushd .. >/dev/null && pushd >/dev/null && git add probe_unregistered_gate.py && git commit -m x"}, "cwd": "/tmp/wt-2774"}
$ bash on-the-record/hooks/gate-registration-guard.sh < /tmp/payload.json ; echo "exit: $?"
exit: 0
```

with the probe file present and untracked (no row in
`docs/specs/enforcement-boundary.md`) — the guard passes silently
(exit 0), no refusal.

Confirmed this is a real bypass, not a false-positive test artifact, by
actually running the identical command text in real bash and checking
`git diff --cached --name-status`:

derived:
```
$ bash -c 'cd /tmp/wt-2774 && pushd gates >/dev/null && pushd .. >/dev/null && pushd >/dev/null && pwd && git add probe_unregistered_gate.py'
/tmp/wt-2774/gates
$ git diff --cached --name-status
A	gates/probe_unregistered_gate.py
```

Real git actually stages the new gate module — exactly the
newly-added, unregistered gate module this guard exists to catch — and
the guard, fed the identical command text, exits 0. Sanity-checked the
harness itself is wired correctly by re-running the same file through a
non-buggy shape (`cd gates && git add ...`), which correctly refuses:

derived:
```
$ bash on-the-record/hooks/gate-registration-guard.sh < /tmp/payload_sanity.json
gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
gates/probe_unregistered_gate.py: no row in docs/specs/enforcement-boundary.md
...
exit: 2
```

confirming the guard can catch this exact file under the exact same
untracked/registration conditions — the only variable is the `pushd`
shape.

### Re-ran the PR's own load-bearing claim (fail-before/pass-after, one shape)

Reproduced the PR's claimed fail-before/pass-after methodology for the
pushd/popd shape via a stash-equivalent script swap (copy PR #2763's own
head script over PR #2774's, run the new test subset, restore).

derived:
```
$ cp <pr-2763 head's gate-registration-guard.sh> on-the-record/hooks/gate-registration-guard.sh
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q -k "pushd or popd or Pushd or Popd"
FAILED ...BundledCwdStackFrameTest::test_pushd_popd_restores_directory_and_refuses_unregistered_gate
AssertionError: 0 != 2
1 failed, 1 passed in 1.73s
$ cp <pr-2774 head's gate-registration-guard.sh back>
$ python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q -k "pushd or popd or Pushd or Popd"
2 passed in 1.71s
```

canonical: the two pytest runs above (this session's own live transcript)
— FAILS (`0 != 2`) against PR #2763's true head, PASSES on PR #2774's
head — the PR's claimed fail-before/pass-after methodology reproduces
for this shape. This is exactly the *matched* pushd-then-popd pair the
PR's test covers — it does not touch bare `pushd`, `pushd +N`, or `pushd
-N`, which is why the bug found in this round survives this same test
suite.

derived: `python3 -m pytest test/test_gate_registration_guard_bundled_add_commit.py -q` at PR #2774 head — result: `24 passed in 3.99s` — matches the count the PR itself claims (24 = 20 pre-existing + 4 new).

### Standing invariants

- **No return of the retired role axis**: derived: `grep -n role on-the-record/hooks/gate-registration-guard.sh` — one hit, a pre-existing comment referencing `role-axis-completeness-guard.sh` as unrelated precedent (not new code, not a role-axis check reintroduced). derived: `grep -n role test/test_gate_registration_guard_bundled_add_commit.py` — zero hits. Clean.
- **No new bug, failing-test-NAME sets vs origin/main**: derived: `python3 -m pytest test/ gates/ -q` in the PR #2774 worktree, and the identical command in a clean `origin/main` worktree, then `diff` of the sorted `FAILED` line sets:
```
$ python3 -m pytest test/ gates/ -q   # PR #2774 worktree
15 failed, 454 passed, 3 xfailed in 11.37s
$ python3 -m pytest test/ gates/ -q   # origin/main worktree
15 failed, 433 passed, 3 xfailed in 3.21s
$ diff /tmp/failed_2774.txt /tmp/failed_main.txt   # both sorted FAILED-line lists
(empty — no output, sets are byte-identical)
```
  Confirmed as a SET-OF-NAMES comparison (the `diff` above), not a count comparison, per this task's own instruction.
- **No overhead increase**: derived: 10 live invocations of the real hook script (`bash on-the-record/hooks/gate-registration-guard.sh`) against the pushd-rotation-bypass payload (worst case among the tested shapes: three pushd segments plus a git add/commit), timed via `time.time()` around each `subprocess.run` — result: `min=0.061s median=0.068s max=0.074s` across the 10 runs. Within the PR's claimed ~0.08s and the prior round's ~0.06-0.08s noise band. No new subprocess call: confirmed by reading the diff directly (`git diff pr-2763 pr-2774 -- on-the-record/hooks/gate-registration-guard.sh`) — the added pushd/popd/cd-`-` logic is pure Python string/list manipulation, no new `subprocess.run` call in the added lines.
- **Monitor and watch machinery unbroken and not quieter**: canonical: `gh pr view 2774 --json files` (this session's own read, merge-base-relative and authoritative over a raw `git diff main..pr-2774`, which is contaminated by this branch's stale base against several since-merged main commits) — the PR's actual file list touches only: two new `docs/issue-2705/reports/*.md`, one deviation-log file, one product-priorities file, `on-the-record/hooks/gate-registration-guard.sh`, and the new test file. No monitor/watch/poll-rearm/hook-fires script is in that list; derived: `grep -rln "monitor\|watch" on-the-record/hooks/*.sh` — result: eight unrelated hook files (`directive.sh`, `hook-fires.sh`, `poll-rearm.sh`, `pr-base-guard.sh`, `pr-preflight.sh`, `record-claim-guard.sh`, `spawn-allow-gate.sh`, `stop-poll-rearm.sh`), none of which appear in the PR's own file list above. Unbroken by omission from this PR's diff — not independently re-verified as still passing their own tests in this session, since that machinery is untouched by this change.

## Why

canonical: this session's own bash/git ground-truth transcripts and the
live-fire against the real hook script, both in "What was done" above
(the `pushd` no-arg / `+1` / `-0` reproductions and the
`probe_unregistered_gate.py` bypass run).

The task's bound was explicit: three prior rounds each patched exactly
the bypass the previous round's review surfaced, and this round's job
was to judge whether the cwd model covers every shape, not only
re-check the three shapes named going in. Probing every named edge
against real bash/git ground truth (rather than only the parser's
internal consistency, per the sections above) is what surfaced that
`pushd`'s own no-argument and `+N`/`-N` forms were never actually
exercised by the round-3 fix or its test — the PR added one test
(`test_pushd_popd_restores_directory_and_refuses_unregistered_gate`)
that exercises a matched `pushd`+`popd` pair, which happens to return
the frame to its starting cwd regardless of whether the intermediate
`pushd` itself is modeled correctly. A matched round-trip test cannot
distinguish "pushd is modeled correctly" from "pushd is a no-op and
popd's `dirs[0]` reassignment coincidentally lands back at the start" —
that is the mechanism reproduced in the live-fire above.

## What did not work

None — the probe harness, ground-truth reproduction, and live-fire
bypass all worked on the first construction. The one iteration was
deriving the correct real-bash semantics for `pushd +N`/`-N` rotation by
running `dirs -v` and `pushd +1`/`pushd -0` directly in bash rather than
recalling them from memory, since the direction of rotation (left vs.
right, 0-indexed from which end) is easy to get backwards without
checking.

## Upstream basis

- PR #2774 (`issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b`), head `0d9858b0` — the subject of this review.
- PR #2763 (`issue-2705/secure-coding-input-validation-injection-defense+adversarial-review-bb9edf99`), head `f943d3fc` — the round-2 baseline PR #2774 builds on and the fail-before baseline used above.
- PR #2774's own record (`secure-coding-input-validation-injection-defense+adversarial-review-4b9dda8b.md`, read in full inside the PR #2774 worktree this session, sha: `0d9858b0`) — cites its two prior round-3 verification records as the ground-truthing for `cd -`/symlink/pushd-popd; referenced below re: the two edges PR #2774 leaves open.
- `on-the-record/hooks/upstream-defect-scope-guard.sh` (sha: current `main` tip `88a84684`) — sibling hook in this same repo whose own comments (around lines 56-57 and 173-174) treat a leading `cd <dir> &&` and `cd <dir>;` as equally-expected command shapes, cited below re: the semicolon edge's real-world prevalence.

## Open findings

canonical: the "Live-fire of the bare-pushd bypass against the real hook
script" and per-shape ground-truth transcripts under "What was done"
above (this session's own bash/pytest output, not a summary of them).

- **`pushd` with no argument does not swap the top two stack entries** — confirmed bypass, live-fired against the real hook (transcripts above: real bash lands at `repo/tmp`, the real hook exits 0 on the identical command against an untracked unregistered gate file, and the same file under a non-buggy `cd`-based shape correctly exits 2). Resolution path: when `pushd` is called with no non-flag argument and `len(frame["dirs"]) > 1`, swap `frame["dirs"][0]` and `frame["dirs"][1]` and set `frame["cwd"]` to the new `dirs[0]`, mirroring bash's own no-arg `pushd`; on `len(dirs) <= 1`, no-op (matches bash's "no other directory" error).
- **`pushd +N`/`pushd -N` rotation is unhandled and actively harmful, not merely a no-op** — `+N` survives the `-`-prefix filter and is parsed as a literal relative-path segment, fabricating a nonexistent cwd (`/other/+1` in the probe transcript above); `-N` is swallowed by the same filter that (correctly) strips real flags, and silently no-ops. Both are live-reproducible via the same mechanism as the no-arg case above (any `pushd +N`/`-N` in a bundled command after at least two prior `pushd`s reaches a cwd the guard never checks against). Resolution path: recognize `+N`/`-N` tokens as rotation directives before the generic flag filter (the same "recognize before the generic filter would swallow it" pattern this PR already used for `cd -`), rotate `frame["dirs"]` accordingly (left-rotate by N for `+N`, right-rotate by N for `-N`, bash's own indexing), and set `frame["cwd"]` to the new `dirs[0]`.
- These are a fourth round's finding of a fresh cwd-tracking gap in the exact family (`pushd`/`popd`) this PR's round claims to have closed. Per this task's own framing and the prior round's own stated bound (a fourth-round fresh gap is a signal about the approach, not the next shape to patch): the shape-by-shape patching approach has now run out of road inside a single family of the model, not just across independent shapes (`cd -` vs. symlink vs. pushd/popd) — the same family "fixed" this round still has two more sub-shapes of itself unfixed by the transcripts above. A fifth single-shape patch for `pushd +N`/`-N`/no-arg should not be assumed sufficient without first enumerating every `pushd`/`popd`/`cd`/`dirs` variant bash actually supports against real bash documentation (`help pushd`, `help popd`, `help dirs`), rather than discovering them one adversarial-review round at a time.
- **CDPATH is unmodeled and undisclosed** (unlike the two edges PR #2774 explicitly names as open — see below). Low severity: no evidence CDPATH is set anywhere in this harness's session environment (grep result under "What was done": zero hits), so the practical exposure looks low, but the PR's "two adjacent edges intentionally left open" framing is incomplete — CDPATH is a third, silently-unhandled edge, just one judged unlikely to matter here rather than one that was weighed and named.
- **The semicolon-joined nonexistent-`cd`-target edge PR #2774 leaves open is more central to this repo's actual command shapes than its framing suggests, though the restraint itself is defensible.** PR #2774's own record cites its prior round's ground-truthing as having already reproduced this bypass and explicitly scopes it out as not one of the three shapes the round-3 review named — an honest, disclosed deferral with a stated resolution path (an `os.path.isdir` check before committing a `cd` target), not a hidden gap. But `on-the-record/hooks/upstream-defect-scope-guard.sh` (this same repo, current `main`) explicitly treats `cd <dir> &&` and a semicolon-joined `cd <dir>` as equally-expected leading forms in its own cwd-resolution logic (its comments around lines 56-57 and 173-174 name both joiners side by side) — meaning the semicolon join is not a rare shape in this codebase's own model of how sessions write bundled commands, contrary to the impression that leaving it open is a narrow, low-traffic bound. This does not make the round-3 restraint wrong (it is consistent with the review's own stated scope and is disclosed, not hidden), but the PR's framing of it as a narrow "adjacent edge" undersells how normal that joiner actually is here.
- No other open findings from this round's probes: `cd -` (repeated), `popd` on empty stack, `cd --`, symlink-chain resolution, and subshell pushd/popd isolation (both directions) all match real bash/git ground truth as implemented — see the per-shape checks under "What was done" above.

## Next steps

canonical: the Open findings section above (this session's own confirmed
bugs and resolution paths), not a new claim.

loop_state: landed. This record is the terminal deliverable for this
review round — it does not itself patch `gate-registration-guard.sh`.
The next action belongs to whoever picks up PR #2774: either (a) a
fourth patch round closing bare-`pushd`/`pushd +N`/`pushd -N` the same
way this PR closed `cd -`/symlink/matched-pushd-popd, with the
enumerate-against-bash-docs-first caveat above, or (b) — given this is
now the second consecutive round finding a fresh gap in the same
`pushd`/`popd` family the prior round claimed to close — a step back to
ask whether shape-by-shape patching of this parser should continue at
all, consistent with the review's own previously stated bound.

other mounted skills: verify-finding-record — not-applicable: this
record's target path and shape (this file's own What was done/Why/What
did not work/Upstream basis/Open findings/Next steps sections) is not
the reproduced/not-reproduced/needs-repro-access outcome block that
skill governs, and this session did not write to any defect-verification
record path.
