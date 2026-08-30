# Commit-time gate hooks

`on-the-record/hooks/hooks.json` registers `PreToolUse` (`Bash`) hooks
that inspect a `git commit` attempt before it lands and can deny it
(exit 2) when they positively determine a violation. All of them fail
open (exit 0) on environment gaps — missing `python3`/`git`, a
non-commit command, or nothing relevant staged — and all respect the
`ORCHESTRATE_OFF` kill switch (any value other than empty/`0`/`false`/
`no`/`off` disables the hook for that invocation).

## role-axis-completeness-guard.sh (issue #650)

Denies `git commit` when the staged `roles/*.json` set violates axis
completeness: `gates/role_spec_shape.py`'s `check_axis_ownership` (each
of the five fixed methodology axes — `alignment`,
`maintenance_complexity`, `external_burden`, `attack_potential`,
`performance` — must be owned by exactly one role across the whole set)
and `check_role_judgment_axes` (a role's own `judgment_axes` array, when
present, must only name axes from that closed set).

Evaluates the WHOLE `roles/*.json` set, not just the staged delta: staged
paths are read via `git show :<path>` (what would actually land), every
other `roles/*.json` file is read from the working tree, since ownership
is a property of the assembled set.

Imports `gates/role_spec_shape.py` rather than re-porting the check logic
(same precedent `role-spec-reference-guard.sh` set for this module). The
packaged `on-the-record/gates` copy of that module can lag the top-level
`gates/` copy — this hook tries each candidate gates directory
(`on-the-record/gates`, then the top-level `gates/`) in turn and uses the
first one that actually exposes both `check_axis_ownership` and
`check_role_judgment_axes`, rather than hard-coding a single path that
may be stale.

Wires a real operational caller for the axis-completeness check
(hunt #628 finding on issue #650): the check previously had a
`--roles-dir` CLI entrypoint with zero callers outside its own unit
tests — the same dead-code class already fixed once in #594/#586.

Regression coverage: `on-the-record/hooks/test_role_axis_completeness_guard.py`
drives the hook script itself (subprocess, real git repo fixtures), not
`role_spec_shape.py`'s CLI.

## post-landing-obligation-gate.sh (issue #1098)

`PostToolUse` (`Bash`), registered alongside `retry-loop-bound.sh post` in
the same `Write|Edit|MultiEdit|Bash` group. Opens a post-landing
verification obligation after a successful `gh pr merge` — northpole
req#3/req#5's "every landed fix is verified by actually running the
changed behavior" needs a default, no-operator-prompt-required tracked
state to hang off of; before this hook, only a human remembering to run
the loop by hand produced that state.

Command-shape detection reuses `merge-allow-gate.sh`'s strict shlex-based
`gh pr merge` / `cd DIR && gh pr merge` tokenization (issue #824) — the
same two recognized shapes, no other chaining/substitution operator
tolerated anywhere in the tail. Success is a heuristic over the
`tool_response` text (no exit-code field is available in the
`PostToolUse` payload for `Bash`) — the same substring-based posture
`gates/landing_readiness.py`'s own `_pr_checks_summary` already uses for
`gh pr checks` output; a handful of known gh-merge failure phrases
("failed to merge", "graphql error", "could not merge", "is not
mergeable") suppress obligation-opening.

Issue/role resolution reads the merged PR's own `headRefName` via
`gh pr view <pr> --json headRefName,mergeCommit` and expects the
`issue-<n>/<role>` shape contract v3 already mandates per branch — NOT
the caller's own current branch (before-landing warrant-hunter finding:
`gh pr merge` is orchestrator-only per `merge-allow-gate.sh`'s own
invariant, and the orchestrator merges from the base/main checkout, so
reading the caller's branch never matched on the one call shape that
actually happens). A `headRefName` that does not match is a no-op (fail
open — no false obligation on an unresolvable branch). On a match, it
shells out to `gates/landing_obligation.py open` to write
`.landing-obligations/<issue>-<role>-<pr>.json`
(`{status: "open", pr, sha, issue, role, opened_at}`), using the PR's
`mergeCommit.oid` when available, else `HEAD` in the caller's checkout.

Resolution composes with the existing `reexecution_gate.py` verdict
instead of re-implementing execution:
`gates/landing_obligation.py:resolve_with_reexecution_verdict` flips the
obligation to `"resolved"` on a `pass` verdict that post-dates
`opened_at`, or to `"failing"` on `fail`/`error`.
`gates/landing_readiness.py:obligation_blocking_cause` turns an
`"open"`/`"failing"` obligation into a `blocking_causes` entry scoped to
the owning PR's own record path (`docs/issue-<n>/reports/<role>.md`),
the same scoping `reexecution_blocking_cause` already established (ADR
§6) to avoid a `gates/`-prefix cause over-covering unrelated PRs.

Known gap (after-proposal hunt,
docs/issue-1098/reports/architecture/2026-08-12-hunt-post-landing-verify-refile-loop.md):
a PR merged through the GitHub web UI, a raw REST call, or another CLI
wrapper never fires this `PostToolUse` command-shape trigger, so no
obligation is opened for it. Resolution path (phase-2, out of this
write set): a periodic or `Stop`-hook-driven reconciliation pass over
`gates/landing_readiness.py`'s existing `gh pr list --json state` read,
treating any actually-merged PR with no obligation on record as
`"open"`.

Regression coverage: `on-the-record/hooks/test_post_landing_obligation_gate.py`
drives the hook script itself (subprocess, real git repo fixtures),
proving it opens an obligation only on an actually-successful `gh pr
merge` for a resolvable PR number on an `issue-<n>/<role>` branch, and is
a no-op for every other Bash command, a failed-merge response, a
chained-command bypass attempt, a non-issue-role branch, and an implicit
current-PR merge.

## gate-registration-guard.sh / gate-registration-post-guard.sh (issue #2705)

`gate-registration-guard.sh` (issue #759/#909) reads `git diff --cached
--name-status` from `PreToolUse`/`Bash` and denies a `git commit` staging
a newly-added `gates/*.py`/`on-the-record/hooks/*.sh`/
`.github/workflows/*.yml` mechanism file with no matching
`docs/specs/enforcement-boundary.md` row. That read is correct for the
unbundled shape (stage in one Bash call, commit in the next — by the time
`PreToolUse` fires on the `commit` call, the earlier `add` call already
finished, so the index really does hold what `--cached` reports) and
structurally blind to the bundled shape this repo's own landing-batching
guidance (#2135) recommends: `git add gates/new_gate.py && git commit -m
"..."` in ONE Bash call has nothing staged yet when `PreToolUse` fires
*before that whole call runs*, so `--cached` reads empty and the check
passes silently.

Issue #2705's history is the record of why this is not a parsing gap:
four adversarial-review rounds each closed one text-prediction shape (`cd`/
subshell resolution, directory-add, `:(exclude)` pathspecs, `cd -`,
symlinked components, `pushd`/`popd` stacks) and the next round found a
fresh bypass inside the SAME family the prior round had just closed. The
seam consult's conclusion: predicting what a bash command will eventually
stage, from its text, before it runs, is undecidable in principle —
subshells, aliases, functions, and `CDPATH` all change what gets staged
without changing what the command looks like. Growing the parser further
was ruled out; two honest alternatives remained (state the bundled shape
as outside this guard's jurisdiction and stop there, or move the check to
where git itself already knows and name that a weaker promise). #2705's
own acceptance criteria require the guard to actually catch the bundled
shape, which only the second alternative can satisfy — so
`gate-registration-guard.sh` itself is UNCHANGED (it still refuses the
unbundled shape exactly as before) and `gate-registration-post-guard.sh`
is a new, separate, explicitly weaker-promise companion for the shape the
first guard cannot see.

`gate-registration-post-guard.sh` never reads command text to guess a
staged set. Its `post` mode (`PostToolUse`/`Bash`) reads git's own
reported outcome instead: a successful `git commit` prints
`[<branch> <sha>] <subject>` to its own stdout, which lands in the
`PostToolUse` payload's `tool_response` (no exit-code field is available
there for `Bash` — the same gap `post-landing-obligation-gate.sh`
documents above). Extracting that `sha` and running `git show
--name-status <sha>` gets the EXACT set of files that commit touched,
independent of `cd`, subshells, `pushd`, or any other command-text shape
— because it is read from git's own object store after the fact, not
predicted before it. A miss is recorded to a session-keyed state file
(`${OTR_GRG_POST_STATE_DIR:-$TMPDIR/otr-grg-post}/<session_id>.json`,
same shape `approach-cap-warning.sh` already uses for its own per-session
counter).

Nothing about `post` mode can deny — the commit already exists in git
history by the time `PostToolUse` fires, the same invariant
`post-landing-obligation-gate.sh`'s own comment states. Surfacing the
finding to the session therefore happens the way this repo's other
non-blocking nudges do it: NOT from `post` mode itself (which, like
`retry-loop-bound.sh`'s own `post` mode, only ever records state and
never emits `additionalContext`), but from a separate `pre` mode
registered at `PreToolUse` on the next tool call (any tool — same broad
matcher `approach-cap-warning.sh`'s `pre` mode uses). `pre` mode re-checks
the CURRENT working tree first (a follow-up commit may already have added
the row) and, only for a violation still open, emits
`hookSpecificOutput.additionalContext` naming the commit, the missing
row, and — in the words the session actually reads, not only in this
handbook or the script's own header comment — that this is a report
after the write already happened, that this hook cannot block or revert
it, and that `gate-registration-guard.sh`'s own pre-commit refusal still
applies unchanged whenever the file was staged in an earlier, separate
Bash call. It repeats on every subsequent tool call until the row lands,
mirroring `approach-cap-warning.sh`'s own "cannot scroll out of context"
rationale, then clears.

Regression coverage: `on-the-record/hooks/test_gate_registration_post_guard.py`.

## The shared input parser, the fail-open ledger, and the wrapper (issue #2093)

Three pieces close the hook-crash *class*, of which #2092 was one instance.

### `hook_input.py` — one total parser

Every hook that reads a Bash command used to carry its own payload decode
and its own `cd <path> &&` regex. The decode was wrapped in a
`try/except`; the extraction was not, so an edge input — an unexpanded
`~`, a heredoc body, unbalanced quotes, an empty or 100KB command, a
missing `tool_input` — raised *past* the decode, deep inside the
filesystem calls fed from it.

`on-the-record/hooks/hook_input.py` is the shared boundary. Its contract:

- **No function in it raises**, for any `str`, `bytes`, `None`, or
  arbitrary object argument. Failure is a returned value carrying a
  machine-readable `reason`, never an exception.
- `parse_payload(raw) -> Payload | Unparseable(reason)`.
- `tool_command(payload) -> str` (`""` when absent).
- `cd_target(command) -> CdTarget(path) | NoCdTarget(reason) | OpaqueCommand(reason)`,
  with `~` expanded. `OpaqueCommand` covers a heredoc body, unbalanced
  quotes, and an oversize command — cases where the string cannot be
  structurally trusted at all.
- `cd_target_dir(command) -> str | None` — the `cd` target only when it
  exists as a directory here. A `cd` target is *claimed*, not verified;
  handing the claim to `subprocess(cwd=...)` is what raised
  `FileNotFoundError` inside `contract-guard.sh`.
- `resolved_cwd(command, default=None) -> str`, `usable_dir(path) -> bool`.

Entry points take a **string**, never stdin: the payload reaches python
through an env var in most hooks.

**Forbidden import direction.** `hook_input.py` imports the standard
library only — never `gates/`, never another hook. It lives next to the
hooks rather than under `gates/` because a zero-install hook cannot
assume `gates/` exists in the consumer repo (`pr-preflight.sh:7-9`), and
the consumer checkout is exactly where the crash class bites. A hook
reaches it with
`sys.path.insert(0, os.environ.get("OTR_HOOKS_DIR", ""))`, where the
shell side exports
`OTR_HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"` on the
`python3 -c` invocation line.

### `fail-open-wrapper.sh` — recording what the exit-code table cannot stop

The platform's table is fixed: exit 0 = allow, exit 2 = block, every
other nonzero — including the 1 a traceback produces — is
**non-blocking**. A crashing guard cannot be made to fail closed. What it
can stop doing is failing *silently*.

Every `hooks.json` registration is therefore wired as
`fail-open-wrapper.sh <real-hook.sh> [args...]`. The wrapper runs the
real hook with its original argv and stdin, re-emits the child's stdout,
stderr and exit code **unchanged**, and appends one ledger line when the
child exits nonzero-and-not-2, or emits a `Traceback` on stderr even at
exit 0. It is verdict-neutral by construction; every ledger step is
best-effort, because a wrapper that could change a verdict would be a
worse defect than the one it records.

Anything reading `hooks.json` command strings must expect this shape:
take the *second* token as the hook under test, and `re.findall` rather
than `re.search` when collecting wired script basenames.

### The ledger

`hook_ledger.record_fail_open()` appends one JSON object per line to
`$OTR_FAIL_OPEN_LEDGER`, defaulting to
`~/.claude/on-the-record/fail-open.jsonl` — env-overridable (hence
testable) and outside any repo, following `contract-guard.sh`'s
provenance-log precedent rather than a repo-relative `runs/` path that
would scatter ledgers across every consumer checkout. Line format:

```json
{"ts": "...Z", "event": "fail-open", "hook": "x.sh", "argv": ["...", "pre"],
 "digest": "sha256:<16 hex>", "exit_code": 1, "reason": "nonzero-exit|traceback"}
```

The input is recorded as a digest, never verbatim: a payload can carry
anything the session typed.

### Conformance coverage

`on-the-record/hooks/test_hook_crash_conformance.py` is parametrized over
every entry parsed out of `hooks.json` — the *entry*, not the script
file, because the same script appears under different argv and argv
selects the parse path — crossed with an edge-input corpus. It asserts
exit code in `{0, 2}` and no traceback on stderr, in a throwaway HOME and
cwd with `gh`/`curl` stubbed. `deliverable-guard.sh`'s deliberate
fail-*closed* behaviour on unverifiable stdin is encoded as a declared
expectation, not an exemption. The full matrix is `slow`-marked; a
fast-tier smoke runs the same corpus against the five migrated hooks.
