# issue-1981 current-state survey

design-research-skip: mechanical — the issue's own `design-research-skip:
mechanical` field plus `validity-consult` already name the accepted
approach (low-risk static change, adopt first); the only open question is
placement/wording inside `_spawn_one()`, not whether to do this.

## Write surface

`spawn.py:7972-7982` (`_spawn_one()`) builds the always-on task preamble
prepended to every role spawn — the "완료의 정의"/headless-single-shot
block. This is unconditional: every `_spawn_one()` call gets it, with no
mode flag gating it off.

canonical: `grep -n "_spawn_one" spawn.py` output, read below
`consult_cmd()` (spawn.py:5658) and `panel_cmd()` (spawn.py:6395) are
separate functions entirely — neither calls `_spawn_one()` nor shares its
task-string assembly. `grep -n "_spawn_one" spawn.py` shows the symbol
only at its own def (line 7874), its two call sites
(`_respawn_or_cap()` line 4066, `main()` line 7189, and the watchdog
region around line 8550), and in test files — never inside
`consult_cmd`/`panel_cmd`'s bodies. Those two functions build their own
prompts independently (`consult_cmd()` docstring, spawn.py:5661:
"커밋도 PR 도 만들지 않는다"). So anything appended inside
`_spawn_one()`'s block is structurally absent from consult/panel
directives — no extra conditional needed to satisfy the acceptance's
"consult/panel (no-commit modes) do not contain it" half.

## Prior art: #1978's injection pattern (spawn.py:7983-7997, merged
4f952e08)

canonical: `git show 4f952e08 -- spawn.py`, read above
`--single-phase` appends a module-level constant block
(`_SINGLE_PHASE_CONTRACT_LINE`) to `task` right after the always-on
preamble, gated on a bool flag. That injection is conditional
(flag-gated); this issue's is not — the checkpoint-commit rule is meant
to apply to every commit-capable spawn, same as the surrounding
"완료의 정의" text it extends, so the natural precedent is the *unconditional*
preamble at spawn.py:7972-7982 itself, not the conditional pattern next to
it.

## Existing test pattern

canonical: `tests/test_spawn_directive_assembly.py:1-60`, read above
`tests/test_spawn_directive_assembly.py` (`_spawn_test_support.py` shared
harness) mocks the spawn machinery down to `spawn_cmd` returning
`(["cat"], {})`, so the assembled task string round-trips through `cat`
into the roster log, and the test reads that log file and asserts on
substring presence/absence. The same harness is reusable for this issue's
acceptance check (assert the rule line is in `_spawn_one()`'s assembled
text; assert `consult_cmd()`/`panel_cmd()` prompts, built independently,
never gain it — no shared code path exists that could make them gain it).

## Existing wording precedent to mirror

canonical: spawn.py:7972-7982, read above
The current preamble already carries the "headless/single-shot" framing
(spawn.py:7979-7982) about backgrounded work dying with the parent turn.
No existing spawn.py string says "checkpoint-commit before long
verification" today.

canonical: `grep -n "checkpoint\|commit -m" spawn.py` output
Grepping `commit` region hits (spawn.py:1169-1178, 5591-5610) are the
consult-trace-commit and pre-existing generic commit helpers, unrelated
to directive text — confirming no prior checkpoint-commit directive line
exists to reuse verbatim; this issue's line is new wording, paraphrased
from the issue body's own quoted rule text.

## Test-tier note (issue #1518 directive)

canonical: `ls .on-the-record/test-tiers.json` (not found)
No `.on-the-record/test-tiers.json` at repo root. Per the observe-only
directive, will run the new/relevant test module directly with
`-o addopts=""` (serial — spawn-invoking tests hang under xdist, issue
#1986, mirrored from #1978's phase-2 record at
docs/issue-1978/reports/implementation.md) rather than a full untiered
suite, and will record that choice plus the untiered-suite gap note in
the phase-2 implementation record.
