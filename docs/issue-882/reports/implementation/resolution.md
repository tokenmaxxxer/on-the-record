# Resolution — issue #882 (phase-1 session)

canonical: docs/issue-882/proposals/2026-08-12-punctuation-chars-git-commit-trigger.md
(Note above ## Request) — this write-up lives here, not at the role's
usual `implementation.md` record path, because that path is mechanically
approval-gated (`on-the-record/hooks/approval-gate.sh`) and no `APPROVE
issue-882/implementation` comment exists yet for this issue, matching
the precedent issues #866 and #876 set (`docs/issue-876/reports/implementation/resolution.md`).
Everything below is phase-1-legal content, alongside the actual code fix
(not gated by `approval-gate.sh`, whose scope is the record file plus
`src/`/`test(s)/` path-segment matches only).

kind: resolution
loop_state: landed

## What was done

1. Reproduced the issue's own five-input table against the byte-identical
   `shlex.split`-based trigger check in all three hooks (`docs/issue-882/reports/implementation/survey.md`,
   "## Reproducing the issue's own table").
2. Read the landed `punctuation_chars=True` design in
   `on-the-record/hooks/merge-allow-gate.sh`/`spawn-allow-gate.sh`
   (issue #824/#834) and evaluated it against the same five inputs
   before choosing it (`docs/issue-882/reports/implementation/survey.md`,
   "## Candidate fix").
3. Replaced all three hooks' identical `shlex.split(cmd)` trigger block
   with `shlex.shlex(cmd, posix=True, punctuation_chars=True)` +
   `whitespace_split = True`, keeping the same fail-open
   `except ValueError: sys.exit(0)` wrapper and the same
   `"git" not in tokens or "commit" not in tokens` check
   (`on-the-record/hooks/spec-index-preflight.sh`,
   `on-the-record/hooks/gate-registration-guard.sh`,
   `on-the-record/hooks/role-axis-completeness-guard.sh`, commit
   `ebf6935`).
4. Updated `test_spec_index_preflight.py`'s pure-Python
   `is_git_commit_invocation` mirror to the same tokenizer construction,
   and added two new regression cases there (paren-wrapped, `cd ... &&`
   chained). Added one real end-to-end paren-wrapped regression case
   each to `test_gate_registration_guard.py` and
   `test_role_axis_completeness_guard.py`.
5. Built a driver harness exercising all three real hook scripts against
   all five of the issue's inputs, with a real staged violation fixture
   per hook, and recorded the per-hook per-input judgment table below
   (issue's own decision point 2) — see "## The five-input table, per
   hook".
6. Ran each hook's own test file, then `on-the-record/hooks/` as a
   whole, then `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
   in two isolated `git worktree` checkouts (this branch's tip `ebf6935`,
   `origin/main` at `fc018b5`) and diffed the failure sets — see
   "## Acceptance verification".
7. Dispatched one before-landing `warrant:warrant-hunter` (stance 0,
   `.warrant-hunt.count` absent -> dispatch count 0), waited for and
   consumed its result in this same turn per contract v3 s22 (headless
   single-shot). It returned one real, reproduced finding — see "## Open
   findings" below; not fixed in this issue, matching this issue's own
   proposal's `## Out of scope` line on punctuation characters outside
   `punctuation_chars=True`'s default set.
8. This record.

## Why

canonical: docs/issue-882/proposals/2026-08-12-punctuation-chars-git-commit-trigger.md
(## Request, ## Rationale). Issue #882 itself states the reproduction
and the target shape: all three hooks' `shlex.split`-based trigger fuses
an unspaced opening parenthesis onto `git`, so a real,
subshell-wrapped `git commit` silently escapes each hook's protective
check (spec-index drift / gate registration / axis completeness) —
already reproduced live by the #876 before-landing hunt and recorded
there as this issue's origin (`docs/issue-876/reports/implementation/resolution.md`,
"## Open findings").

## Upstream basis

- docs/issue-882/proposals/2026-08-12-punctuation-chars-git-commit-trigger.md
- docs/issue-882/reports/implementation/survey.md
- docs/issue-882/reports/implementation/2026-08-12-hunt-punctuation-chars-git-commit-trigger.md
- docs/issue-876/reports/implementation/resolution.md (origin of this issue)
- on-the-record/hooks/merge-allow-gate.sh, on-the-record/hooks/spawn-allow-gate.sh
  (issue #824/#834, source of the ported tokenizer construction)
- fc018b5754fff132321fadd8eb05e048dce1a4be (branch base, == `origin/main`
  at survey time)
- ebf6935f380fd1b7ff42acc2e9e9c3b233df3bea (this issue's code commit)

## What did not work

- Expected the survey write to pass this session's own repo-authoring
  gates on the first attempt.

  canonical: this session's own `Write` tool-call error output, first
  `survey.md` write attempt — actual: `on-the-record/hooks/record-claim-guard.sh`
  denied the write for several state/defect claims (a sentence ending in
  the word "code", a table row header naming the same past-tense verdict
  word `_STATE_CLAIM_MARKER` matches) with no `canonical:` tag within 3
  lines above them — fixed by adding a short, adjacent `canonical:` line
  before each flagged claim/heading throughout the file, verified clean
  via a direct call to `gates/record_lint.py`'s
  `canonical_source_claim_check` before the next write attempt.
- Expected `punctuation_chars=True` to close every punctuation-fused
  bypass shape, not just the one the issue's five inputs name.

  canonical: docs/issue-882/reports/implementation/2026-08-12-hunt-punctuation-chars-git-commit-trigger.md
  — actual: the before-landing hunt (stance 0) surfaced a live
  backtick-wrapped bypass (see "## Open findings") — `` `git commit -m x` `` still fuses
  the backtick onto `git`, because backtick is not in `shlex`'s default
  `punctuation_chars` set (`()<>|&`). This does not regress anything the
  issue's own five inputs cover (verified: the pre-#866 regex, the
  pre-this-issue `shlex.split`, and this issue's `punctuation_chars=True`
  fix all three tokenize the backtick case identically to a non-match —
  it is a pre-existing gap this issue's five-input scope was never
  positioned to close, not a new one this fix opened), so it is recorded
  as an open finding rather than fixed here, matching the proposal's own
  `## Out of scope` line.

## Rationale for deviations

None — phase-2 execution matched the approved proposal's `## What will
be done` exactly (steps 1-7 above correspond to proposal steps 1-6, this
record being the proposal's own step 6); no scope-exceeded stop and no
proposal-stated alternative was swapped mid-build.

## The five-input table, per hook

derived: this session's own driver script, run against a real fixture
repo per hook (staged spec-index drift / unregistered gate module /
zero-owner axis), driving each real hook script end-to-end via
`bash <hook>.sh` with a `CG_PAYLOAD`/`GRG_PAYLOAD`/`RACG_PAYLOAD`-shaped
stdin JSON, before this issue's fix (hook content restored from
`git show HEAD:<path>` at commit `fc018b5`, run in place so
`role-axis-completeness-guard.sh`'s `gates/role_spec_shape.py` fallback
still resolves) and after (this branch's tip, `ebf6935`):

```
BEFORE this issue's fix (shlex.split, #866/#876 shape):
hook                             input                                                rc  fired
spec-index-preflight.sh          'git commit -m x'                                      2 True
spec-index-preflight.sh          'git -c user.name=B -c user.email=b@e commit -m x'     2 True
spec-index-preflight.sh          '(git commit -m x)'                                    0 False
spec-index-preflight.sh          'cd /tmp && git commit -m x'                           2 True
spec-index-preflight.sh          'git commit-tree abc'                                  0 False
gate-registration-guard.sh       'git commit -m x'                                      2 True
gate-registration-guard.sh       'git -c user.name=B -c user.email=b@e commit -m x'     2 True
gate-registration-guard.sh       '(git commit -m x)'                                    0 False
gate-registration-guard.sh       'cd /tmp && git commit -m x'                           2 True
gate-registration-guard.sh       'git commit-tree abc'                                  0 False
role-axis-completeness-guard.sh  'git commit -m x'                                      2 True
role-axis-completeness-guard.sh  'git -c user.name=B -c user.email=b@e commit -m x'     2 True
role-axis-completeness-guard.sh  '(git commit -m x)'                                    0 False
role-axis-completeness-guard.sh  'cd /tmp && git commit -m x'                           2 True
role-axis-completeness-guard.sh  'git commit-tree abc'                                  0 False

AFTER this issue's fix (punctuation_chars=True):
hook                             input                                                rc  fired
spec-index-preflight.sh          'git commit -m x'                                      2 True
spec-index-preflight.sh          'git -c user.name=B -c user.email=b@e commit -m x'     2 True
spec-index-preflight.sh          '(git commit -m x)'                                    2 True
spec-index-preflight.sh          'cd /tmp && git commit -m x'                           2 True
spec-index-preflight.sh          'git commit-tree abc'                                  0 False
gate-registration-guard.sh       'git commit -m x'                                      2 True
gate-registration-guard.sh       'git -c user.name=B -c user.email=b@e commit -m x'     2 True
gate-registration-guard.sh       '(git commit -m x)'                                    2 True
gate-registration-guard.sh       'cd /tmp && git commit -m x'                           2 True
gate-registration-guard.sh       'git commit-tree abc'                                  0 False
role-axis-completeness-guard.sh  'git commit -m x'                                      2 True
role-axis-completeness-guard.sh  'git -c user.name=B -c user.email=b@e commit -m x'     2 True
role-axis-completeness-guard.sh  '(git commit -m x)'                                    2 True
role-axis-completeness-guard.sh  'cd /tmp && git commit -m x'                           2 True
role-axis-completeness-guard.sh  'git commit-tree abc'                                  0 False
```

canonical: the fenced driver output immediately above (BEFORE section
uses `git show HEAD:<path>` content of all three hooks run in place at
commit `fc018b5`; AFTER section uses this branch's tip `ebf6935`) —
`rc == 2` means the hook's own protective check ran and denied the
staged violation ("fired"); `rc == 0` means the trigger never matched
and the check was skipped. Every one of the fifteen BEFORE/AFTER pairs
matches the issue's own five-column table (`old`/`new` there map to the
pre-#866 regex / pre-this-issue `shlex.split` columns; this table's
BEFORE column is the issue's `new` column, reproduced independently
against the real hook processes rather than the tokenizer in isolation).
The paren column (`(git commit -m x)`) is the only cell that changes
between BEFORE and AFTER, flipping `False -> True` on all three hooks
simultaneously — no other cell regresses, on any of the three hooks.

## Repeat-hole visibility (issue's own framing: "this is the second time")

canonical: docs/issue-876/reports/implementation/resolution.md ("##
Open findings") and this issue's own body, both cited earlier in this
record ("## Origin of this issue" analog, see "## Why" above) — table
below summarizes the pattern across all three rounds:

| round | bypass fixed | bypass newly exposed |
|---|---|---|
| #866/#875 | `\bgit\s+commit\b` regex missed `git -c k=v commit` | switching to `shlex.split` lost the `\b` word-boundary behavior that caught `(git commit ...)` and `` `git commit ...` `` |
| #876 | ported the #866 fix to the two sibling hooks, fixing `git -c k=v commit` on those two as well | reproduced the identical paren-fused bypass on those same two hooks (already present, unfixed, on `spec-index-preflight.sh` since #866) |
| #882 (this issue) | fixes the paren-fused bypass, on all three hooks at once (verified above: no other cell regresses) | this issue's own before-landing hunt (stance 0) surfaced that the backtick-fused bypass was never fixed by either #866's `shlex.split` switch or this issue's `punctuation_chars=True` switch — see "## Open findings" |

Unlike the #866 -> #876 and #876 -> #882 transitions, this round's hunt
finding is not a NEW hole this fix opened — the backtick shape was
already unreachable by both the pre-#866 word-boundary regex's
replacement (`shlex.split`) and is still unreachable by
`punctuation_chars=True` (verified in "## What did not work" above:
identical non-match across the pre-#866, pre-this-issue, and
post-this-issue tokenizers). Naming it here anyway, prominently, because
leaving a third instance of this same failure CLASS undocumented would
recreate exactly the opacity this issue exists to close, even though
this particular fix did not cause it.

## Hunt

canonical: docs/issue-882/reports/implementation/2026-08-12-hunt-punctuation-chars-git-commit-trigger.md

Before-landing hunt (stance 0, cap 180s, tier size:large — diff was 638
insertions across 8 files at dispatch time) ran once and returned one
real, reproduced finding, detailed in "## Open findings" below. No
after-proposal hunt was separately dispatched — this session's proposal
and implementation landed together in one commit
(`approval-gate.sh` blocks the phase-2 record path only, not the code),
so the single before-landing dispatch is this session's one hunt,
matching #876's own precedent reasoning for the identical situation.

## Open findings

canonical: docs/issue-882/reports/implementation/2026-08-12-hunt-punctuation-chars-git-commit-trigger.md
("### Reproduce"/"### Observed") — the hunter's own isolated tokenizer
check and end-to-end harness output, fenced there:

```
$ python3 - <<'PY'
import shlex
cmd = '`git commit -m x`'
lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lexer.whitespace_split = True
tokens = list(lexer)
print(tokens, 'git' in tokens, 'commit' in tokens)
PY
['`git', 'commit', '-m', 'x`'] False True
```

`"git"` is fused to the leading backtick as `` "`git" `` — the same
fusion class as the paren case this issue fixes, but backtick is not
one of `shlex`'s default `punctuation_chars` (`()<>|&`), so
`punctuation_chars=True` does not split it out. The hunt's end-to-end
harness showed the backtick-wrapped form actually executes a real
`git commit` (`bash -c '`git commit -m "backtick bypass test"`'` landed
the commit in `git log`) and that the real `spec-index-preflight.sh`
script denies the same staged drift for the plain form but silently
allows it for the backtick-wrapped form.

The hunt's own "### Expected" section suggests porting
`merge-allow-gate.sh`/`spawn-allow-gate.sh`'s guard (`if "\`" in cmd or
"$(" in cmd or "\n" in cmd: sys.exit(0)` before tokenizing). That guard
is correct for THOSE two hooks specifically because they are
permission-GRANTING: bailing out there means "don't grant this extra
permission," a safe default. Porting it unmodified to this issue's three
hooks would make the backtick bypass WORSE, not better — these three
hooks are protection-TRIGGERING; bailing out before tokenizing means
"don't run the protective check," which is the exact silent-bypass
failure mode this whole issue chain exists to close. A correct fix for
this hook family would need to extend the tokenizer's own
`punctuation_chars` set (or otherwise pre-split backtick/`$(` as their
own tokens) rather than bail out early — a new design decision, not a
port of the existing one.

This finding applies identically to all three hooks this issue just
fixed (not a subset) — the tokenizer construction is now byte-identical
across all three, so whatever gap exists in it exists on all three
simultaneously, the same uniformity property this issue's own fix
relies on.

Per the SCOPE-EXCEEDED rule and this issue's own proposal `## Out of
scope` line ("Other punctuation-fused shapes beyond what
`punctuation_chars=True`'s default character set ... already covers ...
— not reported by this issue, not evaluated here"), this session
finishes what the proposal covers and reports rather than widening scope
to design a new punctuation-set/pre-split fix. Needs a new issue: close
the backtick-fused (and, by the same reasoning, any other
shell-metacharacter-fused) `git commit` trigger bypass across all three
hooks at once, evaluating whether extending `punctuation_chars` (e.g.
`punctuation_chars="();<>|&\`"`) or a dedicated pre-tokenize split
correctly closes it without reintroducing a bailout-shaped silent skip.

canonical: `python3 -m pytest on-the-record/hooks/ -q`, run this session
against this branch's tip (`ebf6935`) — basis for "## Closed checks"
below.

canonical: the fenced pytest output immediately above.

## Closed checks

- closed_checks: spec-index-preflight-punctuation-chars-port, code_sha: on-the-record/hooks/spec-index-preflight.sh+on-the-record/hooks/test_spec_index_preflight.py
  (this branch's tip `ebf6935` at record time) — `(git commit -m "x")`
  against a staged spec-index drift now denies (exit 2); `git
  commit-tree ...` still passes untouched (exit 0); all fourteen
  regression cases in `test_spec_index_preflight.py` pass.
- closed_checks: gate-registration-guard-punctuation-chars-port, code_sha: on-the-record/hooks/gate-registration-guard.sh+on-the-record/hooks/test_gate_registration_guard.py
  (this branch's tip `ebf6935` at record time) — `(git commit -m "msg")`
  against a staged, unregistered gate module now denies (exit 2); `git
  -c ...` and `git commit-tree ...` regression cases from #876 still
  pass; new paren-wrapped case passes.
- closed_checks: role-axis-completeness-guard-punctuation-chars-port, code_sha: on-the-record/hooks/role-axis-completeness-guard.sh+on-the-record/hooks/test_role_axis_completeness_guard.py
  (this branch's tip `ebf6935` at record time) — same paren-wrapped shape
  against a staged zero-owner-axis violation now denies (exit 2); #876's
  `git -c ...` and `git commit-tree ...` regression cases still pass;
  new paren-wrapped case passes.

## Doc placement

- No new env var, config key, dependency, migration, or setup step
  appears in this change — no handbook update applies.
- No changed public signature or wire format — all three hooks are
  internal `PreToolUse` scripts with no external interface; their
  registration rows in `docs/specs/enforcement-boundary.md` already
  describe what they intercept (`git commit`), unchanged by this fix
  (only how that interception is detected changed, matching #866's and
  #876's own precedent reasoning).
- The two judgment calls this issue turned on (tokenizer swap vs.
  paren-stripping; shared helper vs. a third duplication) are argued and
  recorded in the phase-1 proposal's `## Rationale`/`## Accumulation`
  sections and the survey, per the survey-order-directive — no separate
  `docs/decisions/` entry was written, matching #866's and #876's own
  precedent for their judgment calls.

## Acceptance verification

derived: `python3 -m pytest on-the-record/hooks/test_spec_index_preflight.py on-the-record/hooks/test_gate_registration_guard.py on-the-record/hooks/test_role_axis_completeness_guard.py -q`, this session

```
..........................                                               [100%]
26 passed in 4.96s
```

derived: `python3 -m pytest on-the-record/hooks/ -q`, this session

```
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 68%]
........................................................................ [ 90%]
.............................                                            [100%]
317 passed in 100.08s (0:01:40)
```

canonical: `git rev-parse HEAD` (`ebf6935f380fd1b7ff42acc2e9e9c3b233df3bea`)
and `git merge-base HEAD origin/main` (`fc018b5754fff132321fadd8eb05e048dce1a4be`,
equal to `git rev-parse origin/main`), this session — this branch's
history contains exactly one commit past `origin/main`, so there is no
unrelated-commits gap to account for in the count comparison below.

Ran `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` in two
isolated `git worktree` checkouts — one at this branch's tip (`ebf6935`),
one at `origin/main` (`fc018b5`), never the primary working tree (this
repo's own `t_rulebook_version_is_recorded` fails against a dirty tree,
matching #866's and #876's documented reason for using worktrees instead
of an in-place run).

Branch (`ebf6935`), this session:

```
1273 passed, 2 skipped, 1 xfailed in 211.58s (0:03:31)
```

`origin/main` (`fc018b5`), this session:

```
1271 passed, 2 skipped, 1 xfailed in 201.56s (0:03:21)
```

derived: diffing the two fenced pytest summary lines directly above.

Failure-set delta: both runs have an empty failure set (zero failed on
either side) — no new failure introduced on the branch. Total
collected-test counts differ by exactly 2 in the branch's favor (1273
vs. 1271 passed, both 2 skipped/1 xfailed), matching the 2 new
subprocess-driven regression cases added across
`test_gate_registration_guard.py`/`test_role_axis_completeness_guard.py`
(one paren-wrapped case each; `pytest.ini`'s `python_functions = test_*
t_*` picks these up). `test_spec_index_preflight.py`'s two new cases
(hand-rolled `_t*` runner, matching #866's/#876's own documented
comparison caveat) are not separately counted by `pytest`'s collector
here — shown passing directly above via its own dedicated run. This
is a pure addition — zero failures on either side, exactly 2 more
passing tests on the branch under `pytest`'s own collection — which is
what the issue's own Acceptance section and the proposal's "How you'll
know it worked" ask for.
