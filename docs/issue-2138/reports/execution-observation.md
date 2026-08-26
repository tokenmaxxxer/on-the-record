---
issue: 2138
role: execution-observation
author: execution-observation
loop_state: landed
upstream:
  - path: docs/issue-2138/reports/implementation.md
    sha: d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8
subject: PR #2520 (branch issue-2138/implementation, "gate-retirement re-scope closed with evidence, no code change")
test: independent re-derivation of the three re-scoped claims (impact-guard.sh/accumulation-claim-guard.sh disposition, live-fire-test-guard.sh registration status, four-leftover-script enumeration), performed without citing the PR's own text as evidence
result: passed
assertedBy: execution-observation
---

# issue-2138 — execution-observation record

## What was done

Independently re-derived, without reusing any of the implementation
record's own commands or citing its conclusions as evidence, the three
claims PR #2520 makes.

**Claim 1 — impact-guard.sh / accumulation-claim-guard.sh check logic is
mechanical, not judgment-shaped.**

canonical: `cat on-the-record/hooks/impact-guard.sh` (this turn, full file
read).

- The script denies a Bash tool call only when it tokenizes (via `shlex`,
  not a naive regex) two or more `gh pr merge` invocations in one command,
  then calls `risk_report.scan_open_proposals()` /
  `risk_report.batch_blocked()` over the TARGET repo's real, currently-open
  `status: proposed` proposals and denies iff at least one of them is
  individually-required by `docs/specs/impact-classification.md`'s
  four-axis rule. Every branch is a function of on-disk proposal state and
  a fixed classification rule.

canonical: `cat on-the-record/hooks/accumulation-claim-guard.sh` (this
turn, full file read).

- The script denies only when (a) the touched file trips one of two fixed
  shape detectors — an AST walk (`ast.parse` + `ast.walk`) counting inline
  `subprocess.run/check_output/check_call/Popen` call sites at `>= 3`, or a
  `roles/[^/]+\.json` path-shape match — and (b) the resident proposal
  file's `## Accumulation` section is checked only for **non-empty
  presence** (`_has_filled_accumulation`: at least one non-blank line
  under the heading), never for what that content says. The script's own
  comment states this directly: "field-presence strengthening ... content
  is never interpreted, contract §14."

canonical: the two full-file reads directly above show both checks are
deterministic functions of code-computed conditions (an AST count, a path
regex, a section-presence boolean, a proposal-state classifier), not
prose judgment calls — KEEP (both) is correct.

**Claim 2 — live-fire-test-guard.sh's absence from GATES is an intentional
DEMOTE, not a dropped registration.**

derived (this turn, run fresh, not copied from the PR record):
```
grep -n "live-fire-test-guard" on-the-record/hooks/pretooluse_dispatcher.py \
  on-the-record/hooks/hooks.json on-the-record/hooks/test_gate_registry.py
```
result: the only hit is `on-the-record/hooks/test_gate_registry.py:113:
"live-fire-test-guard.sh",` — absent from both `hooks.json` and
`pretooluse_dispatcher.py`'s dispatch table.

derived: `git log --oneline --all | grep -i c93f744f` — result:
`c93f744f issue-2138: gate retirement — RETIRE 15, DEMOTE 15 with
guidance landings, registry test (#2144)`, confirmed as a real, landed
commit via `git show --stat c93f744f` (this turn).

derived (this turn, fresh Python import, not a text search):
```
python3 -c "
import sys; sys.path.insert(0, 'on-the-record/hooks')
import test_gate_registry as t
print('live-fire-test-guard.sh' in t.DEMOTED)
"
```
result: `True` — `DEMOTED` is a 15-item frozen set inside the test module.

derived: `python3 -m pytest on-the-record/hooks/test_gate_registry.py -q`
(this turn) — result: 5 passed — the registry test that would fail if
`live-fire-test-guard.sh` were ever re-added to `GATES` /
`DISPATCHED_SCRIPTS` / `hooks.json` without also updating `DEMOTED` is
green right now.

canonical: the three derivations directly above (grep absence from
`hooks.json`/dispatcher, `c93f744f` as a real commit, `DEMOTED` set
membership plus a green registry test) together show this is the
**intentional-DEMOTE** branch, not the **silently-dropped-registration**
branch — the removal is attributable to a specific commit and pinned by a
regression-protecting test, which a silent drop would show neither of.

**Claim 3 — the four leftover scripts are unreferenced on every hook
event, not just PreToolUse.**

derived (this turn, independently re-authored — tracks and prints which
`hooks.json` event(s) reference each script name rather than only a set
difference):
```
python3 -c "
import json, sys
from pathlib import Path
HOOKS_DIR = Path('on-the-record/hooks')
data = json.loads((HOOKS_DIR/'hooks.json').read_text())
sys.path.insert(0, str(HOOKS_DIR))
from pretooluse_dispatcher import DISPATCHED_SCRIPTS
registered = set()
for event, groups in data['hooks'].items():
    for group in groups:
        for hook in group['hooks']:
            tokens = hook['command'].split()
            target = tokens[1] if (Path(tokens[0]).name == 'fail-open-wrapper.sh'
                                    and len(tokens) > 1) else tokens[0]
            registered.add(Path(target).name)
dispatched = set(DISPATCHED_SCRIPTS)
four = {'quality-bar-gate.sh', 'plan-order-guard.sh',
        'report-framing-check.sh', 'decision-queue-stopgate.sh'}
print('four in registered (any event)?', four & registered)
print('four in PreToolUse-dispatched?', four & dispatched)
print('hooks.json events present:', sorted(data['hooks'].keys()))
"
```
result:
```
four in registered (any event)? set()
four in PreToolUse-dispatched? set()
hooks.json events present: ['SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop']
```
derived: `python3 -c "import json; d=json.loads(open('on-the-record/hooks/hooks.json').read()); [print(e,'|',h['command']) for e,gs in d['hooks'].items() for g in gs for h in g['hooks']]" | sort -u`
(this turn) — result: 11 distinct `event | command` lines; every
`SessionStart`/`PostToolUse`/`Stop` entry routes through
`fail-open-wrapper.sh <target>`, the sole `PreToolUse` entry is
`pretooluse-dispatcher.sh` directly, `UserPromptSubmit` is `directive.sh`
via the wrapper — none of the 11 lines name any of the four scripts under
review.

canonical: the two derivations directly above (all five `hooks.json`
event keys iterated, plus the 11-line full enumeration) confirm the four
scripts are absent from registration under every event and absent from
`DISPATCHED_SCRIPTS`.

**Test-tier check-runner note.** derived: `git ls-files | grep
check_runner` (this turn) — result: `gates/check_runner.py`,
`gates/test_check_runner.py` exist; the check-runner comment on PR #2520
shows a false FAIL because the PR's own acceptance bullet quotes the path
`on-the-record/hooks/` in backticks and the classifier reads any
backticked, slash-containing token as an in-repo path assertion, with no
carve-out for a token that merely names a directory rather than asserting
a change at that path. `dfd87617` (#2509, landed) fixed only the
foreign-owner and stating-verb false-FAIL shapes, not this one — a false
FAIL in the check-runner's classifier, not a defect in PR #2520's
delivery.

## Why

The task explicitly asked for independent re-derivation rather than
citing the implementation record's own commands or trusting its
"Present" framing — the point being that a gate that quietly stopped
enforcing (claim 2's alternative branch) would be a materially worse
finding than an intentional, evidenced demotion, and that distinction is
exactly the kind of thing a reviewer must re-derive rather than accept on
the author's say-so. All commands used above were re-typed independently
(not copied verbatim from the implementation record), and claim 3's
script was restructured to explicitly enumerate per-event registration
rather than reusing the record's exact set-difference formulation, so a
bug in the original script's logic would not have silently survived into
this review.

## Upstream basis

- `docs/issue-2138/reports/implementation.md` — untracked on this branch
  (`issue-2138/execution-observation`); lives on branch
  `issue-2138/implementation`, commit
  `d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8`, read via `git show
  d51e4b1ead81ee2cc0b9d4a8307d36158e1459c8:docs/issue-2138/reports/implementation.md`
  (this turn). This is the record under review; PR #2520.
- `on-the-record/hooks/impact-guard.sh`,
  `on-the-record/hooks/accumulation-claim-guard.sh` — read in full this
  turn, same-commit (unmodified).
- `on-the-record/hooks/pretooluse_dispatcher.py`,
  `on-the-record/hooks/hooks.json`,
  `on-the-record/hooks/test_gate_registry.py` — read/grepped/imported this
  turn, same-commit (unmodified).
- `gates/check_runner.py` — derived: `git ls-files | grep check_runner`
  (this turn) — result: `gates/check_runner.py`, `gates/test_check_runner.py`
  — same-commit (unmodified).
- `c93f744f` — issue-2138 gate-retirement execution commit (RETIRE 15,
  DEMOTE 15, registry test), resolved via `git log`/`git show` this turn.

## Open findings

None. derived: `python3 -m pytest on-the-record/hooks/test_gate_registry.py -q`
(this turn, same run cited under Claim 2) — result: 5 passed. Combined
with the full-file reads under Claim 1 and the per-event enumeration
script under Claim 3, each of the three re-scoped items' evidence stands
on its own executed command in "What was done" above, and each matches PR
#2520's stated disposition.

## Next steps

None. `loop_state: landed`. derived: the command/result pairs under Claims
1-3 in "What was done" above (this turn) are the acceptance evidence for
this record; no further verification step is queued.

## What did not work

None.
