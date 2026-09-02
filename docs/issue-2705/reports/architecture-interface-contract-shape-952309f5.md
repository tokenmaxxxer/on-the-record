---
issue: 2705
role: architecture-interface-contract-shape-952309f5
author: architecture-interface-contract-shape-952309f5
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: complete
upstream:
  - path: git show de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:docs/issue-2705/reports/architecture-interface-contract-shape-3f3d4ef5.md (branch issue-2705/architecture-interface-contract-shape-3f3d4ef5, PR #2864's own delivery record; not a path in this working tree, fetched this turn via `git fetch origin issue-2705/architecture-interface-contract-shape-3f3d4ef5` then `git show`)
    sha: de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0
  - path: on-the-record/hooks/gate-registration-post-guard.sh, on-the-record/hooks/test_gate_registration_post_guard.py, on-the-record/hooks/hooks.json, docs/specs/enforcement-boundary.md, docs/specs/generated-paths.md, docs/handbooks/hooks.md (final, CHANGES-round-fixed state on that same branch, materialized onto this branch byte-for-byte)
    sha: 3db2ebeebb72f5e39bf2b214c2e4ada412975371
---

# issue-2705 — architecture-interface-contract-shape-952309f5 record

## What was done

Materialized this issue's already-designed, adversarially-reviewed, and CHANGES-round-fixed
weaker-promise companion guard onto this delivery branch, and independently re-verified every
acceptance-relevant claim myself, live, before landing it here.

**Discovery mid-session, before building anything of my own (full account in "What did not
work"):** this session first wrote its own PreToolUse-side fix for `gate-registration-guard.sh`
(a `git add --dry-run`-based projection of the bundled `git add` pathspec, ported from
`handbook-trigger-gate.sh`'s existing issue-141 D2 pattern), then discovered — via `git log`
on this repo and `gh issue view 2705 --comments` (both read in full this turn) — that this exact
class of fix (predict the eventual staged set from the bundled command's text) had already been
attempted and formally ruled a dead end on this same issue, across four adversarial rounds, before
this session started.
canonical: `gh issue view 2705 --comments`, read in full this turn — the seam-consult hold comment
quotes all four rounds (`cd`/subshell path resolution; `:(exclude)` pathspecs; `cd -`, a symlinked
directory component, `pushd`/`popd`; bare `pushd`'s two-argument swap, `pushd +N`/`-N` rotation,
unmodeled `CDPATH`) and the hold-lift comment cites `tokenmaxxxer-core#233`/`#367`/`#374` as the
same conclusion reached independently.
My own discarded fix did not even track `cd`/`pushd` across the bundled command's segments (it ran
`git add --dry-run` at the payload's reported `cwd` unconditionally), so it was strictly weaker
than the round-3 attempt those four rounds had already exhausted, and reverted in full.

The accepted resolution (originally built on branch `issue-2705/architecture-interface-contract-
shape-3f3d4ef5`, PR #2864, then CHANGES-round-fixed on that same branch by this same role identity
per that branch's own commit trailers) moves the check to the one point that requires no
prediction: git's own post-commit record. `gate-registration-guard.sh` keeps its strong,
synchronous, pre-commit refusal for the unbundled shape (stage in one Bash call, commit in a
following one) exactly as before #2705. A new, separate,
`on-the-record/hooks/gate-registration-post-guard.sh` catches the bundled shape with a weaker,
asynchronous, "report after the fact" promise: `post` mode (`PostToolUse`/`Bash`) reads the
`[<branch> <sha>] <subject>` line `git commit` prints on success out of the payload's own
`tool_response` text (never the command text), inspects that exact commit's tree via `git show
--name-status`, and records any missing-registration finding to a session-keyed state file; `pre`
mode (`PreToolUse`, broad matcher, next tool call) re-checks the current working tree and, only
while still genuinely open, emits `hookSpecificOutput.additionalContext` naming the commit, the
missing row, and explicitly that this is a report, not a refusal.

I copied the final (CHANGES-round-fixed) files from that branch's head onto this one byte-for-byte
(`on-the-record/hooks/gate-registration-post-guard.sh`,
`on-the-record/hooks/test_gate_registration_post_guard.py`, `on-the-record/hooks/hooks.json`,
`docs/specs/enforcement-boundary.md`, `docs/specs/generated-paths.md`, `docs/handbooks/hooks.md`)
rather than re-deriving the design from scratch: the sync/async two-guard split is the settled
outcome of a seam consult this issue already ran.
canonical: PR #2864's review comment, "The seam decision itself is right and I am not reopening
it," quoted in that branch's own record (`git show de8ecb01...:docs/issue-2705/reports/
architecture-interface-contract-shape-3f3d4ef5.md`, read this turn) and independently confirmed
via `gh pr view 2864 --json comments`, read this turn.
I did not trust that copy on the strength of the upstream record alone — every acceptance-relevant
claim below is this session's own execution against the copied files, not a restatement.

acceptance: `python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q` (this
branch, this turn) — result:
```
........                                                                 [100%]
8 passed in 0.93s
```

**Live demo A — original `gate-registration-guard.sh` on the bundled shape (the reported bug),
reproduced first, before any fix was in place:** a `PreToolUse` payload for `git add
gates/new_gate.py && git commit -m test` against a fresh scratch repo
(`docs/specs/enforcement-boundary.md` tracked with no row for the new file) fed to the unmodified
`gate-registration-guard.sh` —
acceptance: `echo "$payload" | bash on-the-record/hooks/gate-registration-guard.sh` — result: exit
0, no output (silent pass, the reported gap, reproduced live).

**Live demo B — the real bundled commit, fed through the companion:** ran the actual
`git add gates/new_gate.py && git commit -m test` for real in that scratch repo, captured git's
real stdout, fed it as a `PostToolUse` payload's `tool_response` (with the original
`tool_input.command` alongside it, matching a real `PostToolUse` payload's shape) to
`gate-registration-post-guard.sh post` —
acceptance: result: exit 0, state file written (`demo-session-1.json`, 143 bytes). Then fed a
`PreToolUse` payload for the next tool call to `gate-registration-post-guard.sh pre` —
acceptance: result: exit 0, `hookSpecificOutput.additionalContext` naming commit `8501457` and
`gates/new_gate.py: no row in docs/specs/enforcement-boundary.md` verbatim — the guard fires on
the bundled shape, which is acceptance criterion 1 satisfied via the weaker, reported-not-refused
promise this issue's own must-not clause requires naming explicitly (see "Why").

**Live demo C — self-heals once the row lands:** staged and committed the missing
`enforcement-boundary.md` row in the scratch repo, then fed `gate-registration-post-guard.sh pre`
again —
acceptance: result: exit 0, no `additionalContext` (silent), and `ls` on the state dir shows zero
files — the lifecycle fix (see "Why") holds under my own independent re-drive, not just the
upstream record's.

**Live demo D — unbundled shape still refuses exactly as before:** staged a second new gate file
in one call, then fed a `PreToolUse` payload for `git commit -m test2` alone (in a following call)
to the unmodified `gate-registration-guard.sh` —
acceptance: result: exit 2, the same deny text as before #2705 — acceptance criterion 2 (the
unbundled shape's behavior is unaffected).

**Regression parity against `origin/main`:**
acceptance: `python3 -m pytest test/ gates/ on-the-record/ -q` (this branch, this turn) — result:
```
15 failed, 506 passed, 3 xfailed in 31.52s
```
canonical: same failing-test-NAME set as the upstream branch's own re-measurement against a fresh
`origin/main` worktree (15 failed, 498 passed, 3 xfailed — 506 = 498 + this delivery's 8 new
tests), per `git show de8ecb01...:docs/issue-2705/reports/architecture-interface-contract-shape-
3f3d4ef5.md`, read this turn; the 15 failing test names here are the pre-existing
`test_spawn_*`/`test_convention_equivalence`/`test_local_dependency_env` set, unrelated to this
change.
acceptance: `python3 -m pytest test/ -k "fleet_scan or monitor or watch" -q` (this branch, this
turn) — result:
```
...............                                                          [100%]
15 passed in 1.25s
```

## Why

**Only "move the check to where git already knows" satisfies acceptance criterion 1.** Declaring
the bundled shape outside `gate-registration-guard.sh`'s `PreToolUse` jurisdiction would leave
criterion 1 unmet — the issue body's own words are "the guard fires on the bundled shape... show
the refusal," not "the guard disclaims the bundled shape." A true pre-commit block of an
already-executed bundled commit is architecturally impossible (`PreToolUse` fires once over the
whole compound command, not between its `&&`-joined parts) without predicting the eventual staged
set from command text — the exact approach four adversarial rounds already exhausted on this
issue (see "What did not work"). Reading git's own post-commit record instead needs no such
prediction: git's commit-success line either names a real, existing commit object, checked live in
demo B above via `git show --name-status <sha>`, or the `post`-mode grep finds no such line and
exits 0 — there is no third, ambiguous case to predict.

**Two separate guards, not one guard silently widened, because the shapes now carry genuinely
different guarantees — the must-not clause's own requirement.**
`gate-registration-guard.sh`'s pre-commit refusal for the unbundled shape is untouched (demo D);
a NEW, separately-named contract with an explicitly weaker, "report after the write, not a refusal
before it" promise catches the bundled shape (demo B). Growing the old guard's meaning silently to
mean "blocks — except when it doesn't, in which case it reports later" would reproduce this
issue's own diagnosis in the guard's own contract text — canonical: issue #2705 body's own
"Why this is larger than one missed row" paragraph, `gh issue view 2705`, read in full this turn.

**The state-file lifecycle fix (this branch's copy, same as the CHANGES-round fix) is the smallest
change that restores the invariant the fast path already assumed.** `_save()` previously wrote a
`{"violations": []}` file for every resolved-or-clean outcome and nothing ever deleted it, so the
`pre`-mode bash-only fast path (which checks file existence, not content, to stay cheap on the
broadest-matcher hook in the system) degraded permanently after the first bundled commit touching
any gate/hook/workflow file, clean or not — this is exactly what demo C's re-drive checks holds
fixed. Deleting the state file whenever no violation remains keeps "a file exists" and "a
violation is genuinely outstanding" the same fact.

**Copied rather than re-derived, but re-verified rather than trusted.** The design fork (sync vs.
async, one guard vs. two) is a genuinely architectural decision this issue already ran a seam
consult on; re-litigating it from a fresh, uninformed attempt (as this session's own first attempt
did, unknowingly) wastes review cycles reproducing a known-dead-end round 5. But copying code
without independently re-executing its claims would relocate the same "looks like a fix" risk this
issue is about — so every acceptance-relevant number and behavior in "What was done" is this
session's own live execution against the copied files this turn.

## What did not work

inline-fix: built a full PreToolUse-side fix for `gate-registration-guard.sh` first — a
`git add --dry-run --`-based projection of any `git add` segment preceding `git commit` in the
same bundled command, closely porting `handbook-trigger-gate.sh`'s existing issue-141 D2 pattern
(same repo, same problem class, already landed and unchanged; canonical:
`core/hooks/handbook-trigger-gate.sh` lines 95–178, read this turn, quoted in full below).
```python
r = git("diff", "--cached", "--name-only")
...
commit_m = re.search(r'\bgit\b[^\n;&|]*\bcommit\b(?!-)', cmd)
if commit_m:
    segments = re.split(r'&&|;|\|', cmd[:commit_m.start()])
    for seg in segments:
        ...
        dr = git("add", "--dry-run", *bulk_flags, "--", *pathspecs)
        for ln in dr.stdout.splitlines():
            ...
```
Live-verified my ported version against both literal acceptance-criterion shapes before discovering
the prior rejection —
acceptance: bundled `git add gates/new_gate.py && git commit -m test` through the patched guard —
result: exit 2 (deny, closing the reported gap for the simple case);
acceptance: unbundled shape (stage then commit) — result: exit 2 identically;
acceptance: bundled `git add $(ls gates/*.py) && git commit -m test` (shell-expansion pathspec) —
result: exit 2 with a distinct "cannot be projected statically" message, not a silent pass;
acceptance: bundled shape with the registration row already staged in the same `git add` — result:
exit 0 (no false positive).
canonical: `gh issue view 2705 --comments`, read in full this turn — the seam-consult hold comment
records that this exact projection approach was attempted across four adversarial rounds on this
same issue (round 1: `cd`/subshell path resolution and directory-add; round 2, `PR #2763`: closed
`:(exclude)` pathspecs; round 3, adversarial review: found `cd -`, a symlinked directory component,
and `pushd`/`popd`; round 4, `PR #2774`: found bare `pushd`'s two-argument swap, `pushd +N`/`-N`
rotation, and unmodeled `CDPATH` inside the same `pushd`/`popd` family round 3 had just closed) and
was formally ruled undecidable in general by the seam consult before this session started. My own
version additionally never tracked `cd`/`pushd` across the bundled command's segments at all (it
ran `git add --dry-run` at the payload's reported `cwd` unconditionally), making it bypassable by
a bundled `cd tmp && git add ../gates/x.py && git commit` — strictly weaker than the round-3
attempt those four rounds had already exhausted, not merely equivalent to it.
Reverted the file to byte-unchanged (`git checkout -- on-the-record/hooks/gate-registration-
guard.sh`) rather than ship a fix already known to be a dead end under a different name. No trace
of this attempt remains in the delivered diff —
derived: `git diff main -- on-the-record/hooks/gate-registration-guard.sh` (this turn) — result: 0
lines of difference.

## Upstream basis

- `git show de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0:docs/issue-2705/reports/architecture-
  interface-contract-shape-3f3d4ef5.md` (branch `issue-2705/architecture-interface-contract-shape-
  3f3d4ef5`, PR #2864's own delivery record — the original two-guard design and its rationale; not
  a path in this working tree), sha `de8ecb01159baf2e5a42c42e2a9f1d9e5af364f0`.
- `on-the-record/hooks/gate-registration-post-guard.sh`,
  `on-the-record/hooks/test_gate_registration_post_guard.py`, `on-the-record/hooks/hooks.json`,
  `docs/specs/enforcement-boundary.md`, `docs/specs/generated-paths.md`,
  `docs/handbooks/hooks.md` at their CHANGES-round-fixed state (state-file lifecycle fix + 3-hook
  orphan enumeration) on that same branch, sha `3db2ebeebb72f5e39bf2b214c2e4ada412975371` — copied
  onto this branch byte-for-byte, then independently re-verified (see "What was done").
- Issue #2705 body (acceptance criteria, must-not clause) and its comment thread (seam-consult
  hold and hold-lift comments, four adversarial rounds' history) — `gh issue view 2705 --comments`,
  read in full this turn.

## Open findings

- **Acceptance criterion 3, enumeration of every other `PreToolUse` hook that reads staged or
  working-tree state, with the same blind-spot verdict** (re-derived independently this turn,
  before I found the upstream branch, across all 21 `pretooluse_dispatcher.py`-routed gates plus
  the 1 `hooks.json`-direct `approach-cap-warning.sh` in `on-the-record/hooks/`, and all 12
  `PreToolUse` gates in `tokenmaxxxer-core`'s `core/hooks/`) —
  derived: `grep -nE '"(diff|status|ls-files)"' <each of the 34 hook scripts>` (this turn), cross-
  checked against `tools=`/`GATES`-list categories parsed out of both dispatchers (this turn).

  | hook | reads staged/working-tree git state to gate a Bash `git commit`? | verdict | command that established it |
  |---|---|---|---|
  | `on-the-record/hooks/gate-registration-guard.sh` | yes | same blind spot — this issue's own subject; strong unbundled-shape refusal unchanged, weaker post-commit companion added for the bundled shape (this delivery) | demos A/D above |
  | `on-the-record/hooks/spec-index-preflight.sh` | yes (`git diff --cached --name-only`, no dry-run/text-projection of a preceding `git add`) | same blind spot, unfixed (out of this issue's scope) | live-reproduced this turn: a scratch repo with a tracked, index-registered spec file, content changed but the index not regenerated — bundled `git add docs/specs/foo.md && git commit` → exit 0 (silent pass); the identical file staged in a prior call, committed in the next → exit 2 (correct refusal) |
  | `on-the-record/hooks/acceptance-command-real-run-guard.sh` | yes (`git diff --cached --name-status`, identical structure to `gate-registration-guard.sh` pre-fix, `if not staged: sys.exit(0)`) | same blind spot, unfixed (out of scope) | `grep -n "dry-run" on-the-record/hooks/acceptance-command-real-run-guard.sh` this turn — no match |
  | `on-the-record/hooks/live-fire-claim-real-run-guard.sh` | yes (identical structure to the above) | same blind spot, unfixed (out of scope) | `grep -n "dry-run" on-the-record/hooks/live-fire-claim-real-run-guard.sh` this turn — no match |
  | `core/hooks/trailer-gate.sh` | yes (`git diff --cached --name-only`, `if not issues: allow()` on an empty staged set) | same blind spot, unfixed (out of scope) | `grep -n "dry-run" core/hooks/trailer-gate.sh` this turn — no match |
  | `core/hooks/handbook-trigger-gate.sh` | yes | not vulnerable, already fixed (issue-141 D2: projects any preceding `git add` segment's pathspec via `git add --dry-run --` and unions the result into the judged staged set — the pattern this session's own discarded fix ported) | full D2 block read this turn, quoted in "What did not work" |
  | remaining 15 `on-the-record/hooks/` `PreToolUse` gates (`retry-loop-bound.sh`, `deliverable-guard.sh`, `heredoc-command-refusal-gate.sh`, `upstream-defect-scope-guard.sh`, `contract-guard.sh`, `pr-preflight.sh`, `pr-base-guard.sh`, `impact-guard.sh`, `merge-allow-gate.sh`, `spawn-allow-gate.sh`, `gh-write-allow-gate.sh`, `git-push-guard.sh`, `credential-network-guard.sh`, `record-claim-guard.sh`, `credential-record-guard.sh`, `accumulation-claim-guard.sh`, `approval-gate.sh`, `approach-cap-warning.sh`) | no | not applicable — none read `git diff --cached`/`git status`/`git ls-files` to gate on staged state; the `WRITE_TOOLS`-triggered subset (`deliverable-guard.sh`, `record-claim-guard.sh`, `credential-record-guard.sh`, `accumulation-claim-guard.sh`, `approval-gate.sh`) additionally cannot share this blind-spot class structurally — they fire once per single `Write`/`Edit` call, whose payload carries the new content directly, with no bundled-shell-command staging step to race | `grep -nE '"(diff|status|ls-files)"' on-the-record/hooks/{each file}` this turn — no hits beyond the rows named above |
  | remaining `core/hooks/` `PreToolUse` gates (`board-gate.sh`, `gh-guard.sh`, `ordering-gate.sh`, `citation-gate.sh`, `facet-keyword-gate.sh`, `proposal-shape-gate.sh`, `record-fields-gate.sh`, `survey-order-gate.sh`) | no (`record-fields-gate.sh` reads `git diff --name-only HEAD`, working-tree-vs-HEAD not `--cached`, and triggers on `WRITE_TOOLS` — a single `Write`/`Edit` call, not a bundled Bash command, so staging order cannot race it; `board-gate.sh`'s `GIT_READ_SUBCOMMANDS` list classifies the CURRENT command's own git subcommand as read/write from its text, it is not an oracle query against prior staged state) | not applicable | same broad grep, plus a direct read of each hit's surrounding code this turn |
  | `on-the-record/hooks/gate-registration-post-guard.sh` (this delivery, new) | reads current working-tree state in `pre` mode, but only to re-check whether an already-reported violation has since been resolved — never to gate the write that produced it, which has already happened by the time this hook can act | not applicable by design (this is the fix; the entire point is not being raced by bundling) | demo C above |

  Resolution path for the unfixed same-blind-spot hooks (`spec-index-preflight.sh`,
  `acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`, and
  `core/hooks/trailer-gate.sh`, per the table above) if picked up: the identical `post`/`pre`
  companion shape this delivery adds for `gate-registration-guard.sh` applies unchanged. Not fixed
  here — this issue's acceptance criteria name only `gate-registration-guard.sh` for an actual fix
  and require the enumeration-with-verdict for the rest, not a fix for each.

- **3 hooks claimed live in `docs/specs/enforcement-boundary.md` but never wired into their
  claimed event** (found by the upstream CHANGES round, reproduced independently this turn):
  `live-fire-test-guard.sh` (claimed `PreToolUse`/`Bash`) —
  derived: `grep -n "live-fire-test-guard" on-the-record/hooks/hooks.json
  on-the-record/hooks/pretooluse_dispatcher.py` this turn — result: no match, exit 1.
  `deviation-log-guard.sh` and `product-capture-stopgate.sh` (both claimed `Stop`) —
  derived: `python3 -c "import json; print(json.load(open('on-the-record/hooks/hooks.json'))
  ['hooks']['Stop'])"` this turn — result: exactly 3 entries,
  `stop-poll-rearm.sh`/`stop-gate.sh`/`skill-verdict-guard.sh`; neither name present. Not fixed
  here — the same #909-class orphan defect, explicitly out of #2705's own non-goals ("the
  registration requirement itself" and other hooks' individual gaps). Resolution path: a separate
  issue for the #909 orphan class generally.

## Next steps

None — both required acceptance shapes and the full enumeration are demonstrated live above
(canonical: this record's own "What was done" and "Open findings" sections, all `acceptance:`/
`derived:` tags executed this turn), the test suite is green at parity with `origin/main`, and
`loop_state` is set to its terminal value on that strength.

skill-verdict: work-in-english — not invoked via the Skill tool (guidance-only per this session's
own skill-obligations note, enforced by core hooks rather than requiring invocation); followed
throughout by writing all code, comments, this record, and the commit/PR text in English while the
conversation itself was addressed in Korean.
other mounted skills: verify-finding-record — not-applicable: this session neither writes a
`docs/issue-<n>/reports/defect-verification.md` file nor is its work a reproduction-outcome record
of that shape; it is the delivery role for this issue's own acceptance criteria.
