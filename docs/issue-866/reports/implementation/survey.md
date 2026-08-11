# Current-state survey — issue #866

Scout-directive skip record: this is a pure bugfix (regenerate a
deterministic hash index) plus a reproduction-only investigation of an
existing gate script — no product-shaped design decision is open, so
the scout sweep is skipped per the directive's own skip condition.

## What's broken

derived: `python3 -m pytest tests/test_spec_index.py -q`, this session,
on `origin/main` (branch tip at survey time, before any change)

```
FAILED tests/test_spec_index.py::t_baseline_repo_passes
1 failed, 3 passed in 0.06s
```

canonical: `gates/spec_index.py`, this session's Read — the `check()`
function walks `docs/specs/reconciled-index.md`'s "Tracked documents"
table and re-hashes each listed file. Row 26 records
`docs/handbooks/setup.md` at the pre-PR#863 hash
(`df9c710683663f26…`); the file's current content hashes to
`240ea33619b461c7…` (pasted directly from the pytest failure above) —
the two no longer match.

## Root cause

canonical: `gh pr view 863 --json files --jq '[.files[].path]'`, this
session, output:

```
["docs/handbooks/setup.md","docs/issue-857/reports/implementation.md","spawn.py","tests/test_spawn.py"]
```

canonical: `git diff 502981d^:docs/specs/reconciled-index.md 502981d:docs/specs/reconciled-index.md`, this session — empty diff (no output), and `git show 502981d -- docs/handbooks/setup.md`, this session — two new paragraphs (a Korean block and an English block) documenting the new `MUSTER_STATE_ROOT` env var, PR #863 (`issue-857: isolate fixture spawn.py roster/watch state via MUSTER_STATE_ROOT`, landed on main as `502981d`) added those paragraphs to `docs/handbooks/setup.md` without touching `docs/specs/reconciled-index.md` in the same change.

`docs/handbooks/setup.md` is a tracked row in the index (row 26,
confirmed below), so the drift is exactly what `gates/spec_index.py`
exists to catch — it just wasn't caught before landing.

## Why `spec-index-preflight.sh` didn't block it — reproduced, not inferred

The issue asks two direct questions: does the hook's trigger scope cover
`docs/handbooks/*.md`, and did it trigger-but-fail-open? Both were
checked live, not read out of the script.

### 1. Trigger scope: not limited to `docs/specs/`

canonical: `grep -n "setup.md" docs/specs/reconciled-index.md`, this
session, output:

```
26:| `docs/handbooks/setup.md` | `df9c710683663f260679d3629ce8733c7f0af60196dbfbaf6b92d8e2205f3e73` |
```

`on-the-record/hooks/spec-index-preflight.sh`'s embedded Python walks
every row in `docs/specs/reconciled-index.md`'s table — the row's *left
column* (an arbitrary repo-relative path), not its containing directory.
`docs/handbooks/setup.md` sits at row 26 of that table per the grep
output directly above, so it is exactly as much "in scope" for this
hook as any file under `docs/specs/`. The scope question resolves to:
not limited to `docs/specs/` — any tracked row, wherever it lives, is
checked by this hook.

### 2. Does the hook's own detection logic actually catch this drift?

canonical: this session's own live reproduction transcript below (not
static reasoning about the script's source).

Built an isolated worktree at `502981d`'s parent (`59016f0`), then
`git cherry-pick -n 502981d` to stage the exact same change-set (without
committing), reproducing what the local working tree looked like the
moment before that PR's one commit (`ac8156d6`) was made:

```
$ git worktree add --detach /tmp/repro-866 502981d^
$ cd /tmp/repro-866 && git cherry-pick -n 502981d
$ git diff --cached --name-only
docs/handbooks/setup.md
docs/issue-857/reports/implementation.md
spawn.py
tests/test_spawn.py
$ grep -n "setup.md" docs/specs/reconciled-index.md
26:| `docs/handbooks/setup.md` | `df9c710683663f260679d3629ce8733c7f0af60196dbfbaf6b92d8e2205f3e73` |
$ git show :docs/handbooks/setup.md | sha256sum
240ea33619b461c7b0ca6c8f4433121249247ff5bfedd2ace39d46a940525df8  -
```

Then ran the actual hook script (unmodified, from this branch) against
that staged state, feeding it a synthetic `PreToolUse`/`Bash` payload for
a `git commit`:

```
$ CG_PAYLOAD='{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}'
$ bash on-the-record/hooks/spec-index-preflight.sh <<< "$CG_PAYLOAD"
spec-index-preflight: staged content changed for tracked spec file(s) [docs/handbooks/setup.md] but docs/specs/reconciled-index.md was not updated to match in the same staged set. Regenerate with `python3 gates/spec_index.py --update`, stage the updated index, and retry the commit.
exit code: 2
```

canonical: the fenced transcript directly above, this session, run
against the unmodified `on-the-record/hooks/spec-index-preflight.sh` on
this branch — the hook denies (exit 2) when fed this exact staged
drift. Its detection logic is correct on this input shape; this is not
a silent fail-open here.

canonical: `python3 on-the-record/hooks/test_spec_index_preflight.py`,
this session, on `origin/main`, output:

```
PASS: red: tracked file staged content changed, index not staged -> mismatch
PASS: red: tracked file changed, index staged but still carries OLD hash
PASS: green: tracked file changed, staged index carries matching NEW hash
PASS: green: unrelated file staged, tracked file untouched -> no mismatch
PASS: green: tracked file staged but content unchanged -> no mismatch
PASS: skip: tracked file staged but git show failed (deletion) -> no mismatch
all tests passed
```

That pre-existing pure-logic unit suite (all cases pasted above) already
exercises the same comparison function this session's live subprocess
reproduction exercised end-to-end; both agree the logic itself is sound.

### 3. So why did it land anyway? Two separate gaps, only one checkable from artifacts alone

**Gap A — the original branch commit.**

canonical: `gh pr view 863 --json commits --jq '[.commits[] | {oid, messageHeadline}]'`, this session — one commit, `ac8156d6ec3e7122d944f07ec6dc7466c614390c`, and `git show ac8156d6ec3e7122d944f07ec6dc7466c614390c -s --format="%an <%ae>%n%cn <%ce>%nGPG: %G?"`, this session, output:

```
Jiwon Jung <Jiwon8297@gmail.com>
Jiwon Jung <Jiwon8297@gmail.com>
GPG: N
```

Author and committer are both the local git identity, unsigned — an
ordinary local commit, not GitHub-authored.

canonical: `git diff ac8156d6 502981d -- docs/handbooks/setup.md docs/specs/reconciled-index.md`, this session — empty diff (no output). The squash landed nothing different about these two files' content versus the original branch commit, so `ac8156d6`'s own tree already carries the exact drift reproduced in section 2 above.

If `spec-index-preflight.sh` was active in whatever session ran the
`git commit` that produced `ac8156d6`, it should have denied it, per
the reproduction in section 2.

canonical: `spawn.py`'s `plugin_dirs()` function, this session's Read
(around line 310) — wires `--plugin-dir` per role session, so the hook
is *expected* to be active for a normal role session.

No session transcript or log for the specific `git commit` call that
produced `ac8156d6` is available to this session. Whether that call
actually had the hook active, and if so why it was not denied, is not
determinable from repo artifacts alone — recorded here as an open
unknown, not asserted in either direction.

**Gap B — the actual landing commit sits outside this hook's reach,
independent of Gap A.**

canonical: `git show 502981d -s --format="%an <%ae>%n%cn <%ce>%nGPG: %G?%nParents: %P"`, this session, output:

```
Jiwon Jung <87398933+JiwonJung94@users.noreply.github.com>
GitHub <noreply@github.com>
GPG: E
Parents: 59016f06ca3a9dd402ba5a0cc9791cca62f08b46
```

`502981d` — the commit that actually broke `origin/main` — carries
committer `GitHub <noreply@github.com>`, a GPG signature (verification
status `E`, GitHub's own signing key not present in this local
keyring), and a single parent — the shape of GitHub's server-side
squash-merge, not a local `git commit` invocation.

canonical: `on-the-record/hooks/spec-index-preflight.sh`, this
session's Read — the script is a `PreToolUse` hook: it only runs when a
Claude Code session's Bash tool actually issues a matching command. A
commit fabricated server-side by `gh pr merge`/the GitHub "Squash and
merge" button never runs a local `git commit` inside any session, so
there is no Bash tool call for the hook to intercept — by construction,
not by a defect in this script. Even a perfectly-wired, always-active
`spec-index-preflight.sh` on every prior session could not have stopped
this specific commit from landing, because the landing operation itself
never goes through the surface this hook watches.

This is consistent with the issue's own background note that there is
no CI (#460) — enforcement today is entirely local-session-side; the
moment a change lands via a server-side GitHub operation instead of a
local `git commit`, every hook in this family
(`spec-index-preflight.sh` included) sits out of reach by design, not
by defect.

## Decision inputs for the proposal

1. Regenerating the index is mechanical and mandatory (issue's own
   framing) — no design decision.
2. canonical: `git show 502981d -- docs/handbooks/setup.md`, this
   session (full diff read, both language blocks) — the change is a
   pure *addition*: two new paragraphs describing `MUSTER_STATE_ROOT`.
   It does not edit or contradict `docs/specs/reconciled-index.md`'s
   existing "Resolved ambiguities" section, which — canonical: this
   session's Read of `docs/specs/reconciled-index.md` in full (43
   lines) — currently holds exactly one entry: ledger storage location,
   unrelated to roster/workspace-index state. No other tracked document
   (`protocol.md`, `docs/handbooks/operations.md`,
   `docs/handbooks/on-the-record.md`, `on-the-record/commands/run.md`)
   makes any claim about `MUSTER_STATE_ROOT` or roster/workspace-index
   file location that this addition could conflict with, so "Resolved
   ambiguities" needs no new entry for this specific drift.
3. Gap B, above, is a structural property of the landing mechanism
   (server-side GitHub merge), not a defect in
   `spec-index-preflight.sh`'s own comparison logic — independently
   verified correct by the live reproduction in section 2 and already
   covered by its pre-existing unit suite. A `PreToolUse` hook cannot be
   made to see an event it is never invoked for, so no code change to
   `spec-index-preflight.sh` closes Gap B. Gap A (see above) stays an
   open unknown in this record rather than a claimed root cause, because
   no session transcript exists to settle what happened
   during `ac8156d6`'s own authoring — a script whose logic was
   independently verified correct is not a defect this session can
   respond to with a code change without guessing at an unconfirmed
   cause, so no edit to `spec-index-preflight.sh` is made either way.

## After-proposal hunt finding and resolution

canonical: `docs/issue-866/reports/implementation/2026-08-11-hunt-regenerate-spec-index-and-record-preflight-gap.md`
(after-proposal, stance 0) — the hunter found that
`spec-index-preflight.sh`'s original trigger check,
`re.search(r"\bgit\s+commit\b", cmd)`, requires `commit` to follow `git`
with only whitespace between them. `git -c commit.gpgsign=false commit -m
x` — an entirely ordinary way to pass a one-off git config value for a
single commit — has `-c commit.gpgsign=false` between the two words, so
the regex never matches and the check is skipped outright.

canonical: this session's own re-run of the hunter's reproduction,
against the exact PR #863-shaped staged drift built in section 2 above
(the `/tmp/repro-866` worktree), output:

```
$ CG_PAYLOAD='{"tool_name":"Bash","tool_input":{"command":"git -c commit.gpgsign=false commit -m \"test\""}}'
$ bash on-the-record/hooks/spec-index-preflight.sh <<< "$CG_PAYLOAD"
exit code: 0
```

No stderr, exit 0 — the same drift that the plain `git commit -m x` form
correctly denies (section 2 above) lands silently through this form.
`python3 -c 're.search(r"\bgit\s+commit\b", "git -c commit.gpgsign=false commit -m x")'`
shows the regex itself returns no match — a second, independent check
of the same conclusion, not only the subprocess reproduction above.

This overturns this survey's earlier "the hook's own logic is correct,
nothing here is fixable" conclusion — it was correct about the
hash-comparison logic (section 2), wrong to extend that verdict to the
trigger-detection step in front of it. Resolved by widening the trigger
check in `on-the-record/hooks/spec-index-preflight.sh` from a strict
adjacency regex to a `shlex.split`-based token check (`"git" in tokens
and "commit" in tokens`), which tolerates any global option between the
two words while still not firing on `commit` appearing inside an
unrelated token (`--grep=commit`, `commit-tree`) or inside a quoted
string — re-verified against the same three shapes plus the original
6-case suite, all passing (see the implementation record's Acceptance
verification section for the full transcript).

This also gives Gap A (above) a plausible, not settled, mechanism: if
whatever session authored `ac8156d6` ran a `git -c <cfg>=<val> commit`
form — for instance to set a one-off `user.email`/`user.name` or disable
gpg signing for that single commit — the pre-fix hook would have let it
through exactly this way, with no denial and no stderr. No literal
command string for that historical commit is available to this session,
so this stays a plausible mechanism, not a settled cause — Gap A
itself is not reclassified as solved.
