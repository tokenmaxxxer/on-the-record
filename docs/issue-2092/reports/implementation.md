---
code_under_review: HEAD
loop_state: landed
type: bugfix
breaking: false
verdict: pass
---

# issue-2092: expand tilde before using cd-extracted path as subprocess cwd

## What was done

`on-the-record/hooks/contract-guard.sh` extracted a `cd <path> &&` prefix
from the Bash command via `re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)` and used
the raw captured group directly as `target_cwd`, which is later handed to
`subprocess.run(..., cwd=target_cwd, ...)` as the `cwd=` argument. When the
extracted path started with `~` (e.g. `cd ~/tm-dicequest && gh pr merge
1`), Python's `subprocess.run` does not expand `~`, so the call raised
`FileNotFoundError: [Errno 2] No such file or directory: '~/tm-dicequest'`,
surfacing as a PreToolUse hook traceback and silently fail-opening the
guard.

Fix: wrap the captured group in `os.path.expanduser(...)` at the point of
extraction in `contract-guard.sh:96`
(`target_cwd = os.path.expanduser(cd_m.group(1))`), so the tilde is
resolved before it is ever used as a `cwd=` argument.

Sweep for the same pattern (issue's second acceptance item):
```
$ grep -rn 'cd_m = re.match(r"\^\\\\s\*cd\\\\s+(\\\\S+)\\\\s\*&&"' on-the-record/hooks/*.sh
absorbed-branch-recut-guard.sh:87:cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
merge-allow-gate.sh:167:cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
contract-guard.sh:94:cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
```
Both `absorbed-branch-recut-guard.sh` (line 88, printed straight into a
downstream cwd consumer) and `merge-allow-gate.sh` (line 169, assigned to
`target_cwd` then handed to `subprocess.run(..., cwd=target_cwd, ...)`,
identical shape to contract-guard.sh) carried the same unexpanded-tilde
bug and were changed identically to call `os.path.expanduser(cd_m.group(1))`.

Regression test added: `test_cd_prefix_with_tilde_expands_before_use_as_cwd`
in `on-the-record/hooks/test_contract_guard.py`, driving
`cd ~/targetrepo && gh pr merge 7 --merge` with `HOME` pointed at a tmp
directory containing the target checkout, asserting `returncode == 0` with
no `Traceback`/`FileNotFoundError` in stderr and that the target repo's
(not cwd's) approvers/PR body drove the allow verdict.

## Why

The guard's own gating logic is correct — the crash was a plumbing bug: an
unexpanded `~` was never a valid filesystem path for `subprocess.run`'s
`cwd=`, and Python does not shell-expand it. Fixing the extraction site is
the minimal, root-cause fix; the alternative (a `try/except
FileNotFoundError` fallback) was rejected because it would mask, not fix,
the fail-open — the guard would still silently skip the tilde-path repo
instead of correctly resolving it.

## Upstream

basis: issue #2092 (verbatim reproduction and acceptance quoted above).

## What did not work

None.

## Open findings

None.

## Test tiers (issue #1518 directive)

`.on-the-record/test-tiers.json` is present. This change touches
`on-the-record/hooks/*.sh`, matching the `slow` tier's
`trigger_change_classes`, so both tiers were exercised for the affected
hook tests directly (fast tier's `pytest -q -m "not slow"` filter is not
relevant here since these hook tests carry no `slow` marker):

canonical: python3 -m pytest on-the-record/hooks/test_merge_allow_gate.py on-the-record/hooks/test_absorbed_branch_recut_guard.py on-the-record/hooks/test_contract_guard.py -q (this turn's own run, output below)
```
$ python3 -m pytest on-the-record/hooks/test_merge_allow_gate.py on-the-record/hooks/test_absorbed_branch_recut_guard.py on-the-record/hooks/test_contract_guard.py -q
........................................                                 [100%]
40 passed in 1.30s
```

## Skill verdicts

skill-verdict: implementation-complexity-coupling-management — not-applicable: single-line extraction-site fix, no coupling/cohesion threshold or check-ordering decision involved.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern decision; this is a one-line bugfix at an existing extraction call.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm/communication-scheme choice involved.
skill-verdict: implementation-blueprint — not-applicable: pure bugfix, single-file-scope edits to three existing hook scripts, no new module/file structure to design.
skill-verdict: test-derivation — not-applicable: the issue's acceptance criteria were already concrete executable checks (one regression test, one grep sweep); no ambiguity in technique selection required derivation.
