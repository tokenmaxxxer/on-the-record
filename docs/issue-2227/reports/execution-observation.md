---
issue: 2227
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2227/reports/implementation.md
    sha: b2b9c748979a3ab3a59093af569dfbf7d30d58bd
  - path: spawn.py
    sha: b2b9c748979a3ab3a59093af569dfbf7d30d58bd
subject: PR #2338 (issue-2227, "per-path context scoping for the spawned-session
  directive"), commits c7207b3c322861a0330f1aa39b5be322869acbcd/b2b9c748979a3ab3a59093af569dfbf7d30d58bd,
  branch issue-2227/implementation, worktree checkout at
  b2b9c748979a3ab3a59093af569dfbf7d30d58bd (untracked in this tree -- lives
  on issue-2227/implementation, PR #2338)
test: independent re-execution of the docs-only vs engineering live-spawn
  size/cache/duration comparison and the empty-state (baseline never empty)
  claim cited in docs/issue-2227/reports/implementation.md's Acceptance
  evidence -- commands and outputs below, run in a fresh git worktree
  checkout of the PR branch plus two fresh throwaway git repos for the live
  `claude -p` spawns, independent of the PR's own pasted output
result: passed
assertedBy: execution-observation session for issue-2227, independent of
  PR #2338's authoring (implementation) session
---

# issue-2227 — execution-observation record

## What was done

canonical: `git fetch origin issue-2227/implementation` and
`git worktree add /tmp/pr2338-review origin/issue-2227/implementation` --
an independent checkout of the PR's `spawn.py`/`_role_touches_code()` /
`directive_section_files(code_scoped=...)` change, never the PR's pasted
transcripts taken as given. Spawning prompt scoped this observation to
two specific re-executions: the docs-only vs engineering live-spawn
size/cache/duration comparison, and the empty-state claim (a role that
matches no path scope still gets the invariant baseline, never an empty
directive).

canonical: `gh pr view 2338 --json state,mergedAt -q '. | "state=\(.state) mergedAt=\(.mergedAt)"'`
-- result: `state=OPEN mergedAt=null` -- confirms PR #2338 is open, not
yet merged to main; its files are therefore untracked in this branch's
own tree and were read from the independent worktree checkout below
instead.

### Pure-function directive-size comparison — reproduced exactly

canonical: `python3 -c "import spawn; ..."` (PR worktree, same one-liner
shape as the record's own Acceptance evidence, re-typed independently) --
result:
```
code files: ['completion-and-landing.md', 'repo-discovery.md', 'known-paths.md', 'turn-budget.md', 'skill-obligations.md'] 5885
docs files: ['completion-and-landing.md', 'repo-discovery.md', 'turn-budget.md', 'skill-obligations.md'] 5035
delta bytes: 850
```
Matches the record's claim exactly: 5885B / 5035B / 850B (14.4%) smaller.

### Empty-state and role inventory — reproduced exactly

canonical: `spawn._role_touches_code([])` and
`spawn.directive_section_files(code_scoped=False)` (PR worktree) --
result:
```
empty write_scope code_scoped: False
baseline present: True True True
known-paths absent: True
```
An empty `write_scope` (the `requirements-engineering` /
`product-discovery` / `user-discovery` shape the record cites) is not
code_scoped, and the three baseline sections
(`completion-and-landing.md`, `repo-discovery.md`, `turn-budget.md`)
survive regardless -- the directive is never empty. Confirms Acceptance's
"empty state" bar independently of the record's own test file.

canonical: live inventory over the real `roles/*.json` files (PR
worktree) -- result:
```
code_scoped roles: ['implementation']
total roles: 44
```
Matches the record's claim: `implementation` is the sole code_scoped role
among 44 shipped roles today.

### Unit tests — reproduced exactly, including the one pre-existing failure

canonical: `python3 -m pytest tests/test_spawn_directive_assembly.py -q -m ""`
(PR worktree) -- result:
```
1 failed, 38 passed in 1.38s
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
```
Same count (38 passed / 1 failed) and same failing test as the record's
own Test plan. The failure's own assertion output confirms the record's
explanation: it fails because `CORE_BUILD_NOW` is present in *this very
session's* `os.environ` (`AssertionError: 'CORE_BUILD_NOW' unexpectedly
found in {...}`) -- an environmental fact of running under the build-now
bypass, not something the diff's content controls. Independently
confirmed reproducible, not diff-caused.

### Live-spawn measurement — direction confirmed, one metric-attribution deviation found

canonical: built `$SYS_ENG` / `$SYS_DOCS` from this worktree's own
`spawn.directive_section_files(skills_mounted=True, code_scoped=True/False)`
+ `_directive_system_prompt_block()` (byte-identical to the pure-function
comparison above: 5885B / 5035B), then ran two independent live
`claude -p` invocations against two fresh throwaway git repos this
session created (`/tmp/eo2338-dirA`, `/tmp/eo2338-dirB` -- not the PR
session's own directories), same task prompt, same flags
(`--output-format stream-json --verbose --max-turns 3
--permission-mode bypassPermissions
--exclude-dynamic-system-prompt-sections --setting-sources ""`) as the
record's own methodology:

Engineering run (`code_scoped=True`, 5,885-byte block):
```
duration_api_ms 5470
duration_ms 4484
ttft_ms 4468
usage.cache_creation_input_tokens 4160
usage.cache_read_input_tokens 20360
tool_use events: 0
```

Docs-only run (`code_scoped=False`, 5,035-byte block):
```
duration_api_ms 5149
duration_ms 4264
ttft_ms 4246
usage.cache_creation_input_tokens 4160
usage.cache_read_input_tokens 19938
tool_use events: 0
```

Both runs' assistant text answers the landing-rule question correctly
with 0 tool_use events, confirming the appended content (baseline-only
for docs, baseline+known-paths for engineering) reaches the model
correctly in both cases -- matching the record's own qualitative check.

**Direction reproduces**: the docs-only run is faster
(`duration_api_ms` 5149 < 5470, -321ms/-5.9%; `ttft_ms` 4246 < 4468,
-222ms) and reads/creates 422 fewer total tokens
(`cache_creation_input_tokens + cache_read_input_tokens`: 24098 vs
24520), matching the record's qualitative claim that the docs-only
bundle is genuinely cheaper to bootstrap, not just byte-smaller on
paper.

**Metric-attribution deviation, not a code defect**: the record's own
evidence shows the 422-token delta landing entirely in
`cache_creation_input_tokens` (8595 -> 8173, -422) with
`cache_read_input_tokens` identical between its two runs (15917 both).
This session's independent re-execution shows the same 422-token delta
landing entirely in the *other* field --
`cache_read_input_tokens` (20360 -> 19938, -422) with
`cache_creation_input_tokens` identical between its two runs (4160
both). The net token saving (422) and its sign (docs-only always lower)
reproduce exactly; which usage field carries it does not. This is
consistent with Anthropic prompt-cache accounting depending on what
prefix was already warm on the API side at call time (this session ran
the engineering variant first, so the docs variant's shared prefix up to
the point of divergence was already cached from that first call -- a
property of call order and host cache state, not of `spawn.py`'s
content), the same class of "host-state-dependent, not code-dependent"
variability a prior execution-observation record (issue-2298) hit on
live host-log measurements. Recorded as an open finding below, not a
verdict-changing defect: the record's own qualitative claim (docs-only
directive costs measurably less to bootstrap) holds under independent
re-execution; only the specific usage-field the record chose to cite as
"the" evidence field is not the field an independent re-run happens to
land the delta in.

## Why

Delegated scope was re-execution, not re-derivation of new claims: the
issue's Acceptance explicitly requires "a size claim without both live
spawns does not satisfy this," so the highest-value independent check is
re-running both live spawns from a clean worktree/clean throwaway repos
and comparing signs and magnitudes against the record's own numbers,
the same posture prior execution-observation records in this repo
(issue-2298, issue-2314) have taken toward PR-pasted live-run evidence.

## Upstream basis

- `docs/issue-2227/reports/implementation.md` (untracked in this tree --
  lives on branch `issue-2227/implementation` at commit
  `b2b9c748979a3ab3a59093af569dfbf7d30d58bd`, PR #2338; see the
  `gh pr view 2338` citation under What was done for the open/unmerged
  status) -- the record whose Acceptance evidence this session
  re-executed; quoted and compared inline above.
- `spawn.py` at the same commit (untracked in this tree, same branch) --
  `_role_touches_code()`, `directive_section_files(code_scoped=...)`, and
  the `_spawn_one()` call site this session ran directly (pure-function
  checks) and indirectly (live-spawn system-prompt construction).
- `tests/test_spawn_directive_assembly.py` at the same commit (untracked
  in this tree, same branch) -- the declared gate, re-run in the PR
  worktree, not this branch (which does not carry the PR's changes).

## Open findings

- The docs-only-vs-engineering live-spawn token/duration delta's sign
  and magnitude (422 tokens, ~300-700ms) reproduce under independent
  re-execution, but which `usage` field (`cache_creation_input_tokens`
  vs `cache_read_input_tokens`) carries the delta is call-order/
  cache-state dependent, not deterministic per the diff's content alone
  -- see Live-spawn measurement above for the pasted numbers from both
  this session's runs and the record's own. Resolution path: no action
  needed against this PR -- the record's qualitative claim holds under
  independent re-execution -- but flag for whoever next writes a
  live-spawn size/cache record: cite the *sum*
  (`cache_creation_input_tokens + cache_read_input_tokens`), which is
  stable across the field-attribution variability observed here, rather
  than a single sub-field.

## Next steps

None -- `loop_state` above is this record kind's terminal value,
`handed-off`.
