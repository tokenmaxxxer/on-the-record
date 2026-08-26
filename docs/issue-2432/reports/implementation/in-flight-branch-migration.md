# In-flight branch handling — stage 4 (branch/record naming cutover)

**Path note (deviation, see this issue's own implementation record's
"Deviations" section)**: the stage-4 proposal's `files:` list names this
doc's frozen path as the parent program issue's own architecture-reports
tree. `board-gate.sh` R4 refused that write live this session —
canonical: refusal produced live this turn by this session's own
`board-gate.sh`, verbatim: "board-gate: writing docs/issue-2241/
requires branch issue-2241/implementation (current:
issue-2432/implementation), and issue #2432's body declares no matching
`maintenance-targets:` entry for issue-2241." — issue #2432's body
declares no `maintenance-targets: issue-2241` line (canonical: `gh issue
view 2432 --json body -q .body`, this turn, grepped for
`maintenance-targets` — no match), and this session cannot self-grant
that exception (`gh issue edit` is denied to a role session; only `gh
issue comment` is allowed — same shape as the precedent at
`docs/issue-2286/reports/implementation.md`'s "CHANGES-round fix
attempt" section for issue #2286/#2390). A second `board-gate.sh` R11
refusal (canonical, this turn, verbatim: "board-gate:
docs/issue-2432/reports/architecture/in-flight-branch-migration.md
belongs to another role. implementation writes only implementation.md,
implementation/** — never a foreign record.") ruled out placing this
copy under an `architecture/` subtree even inside this issue's own docs
tree — the `implementation` role's own write scope is `implementation.md`
/ `implementation/**` only. Filed as a comment on issue #2432 naming
both unblock paths for the frozen path (a session on the parent program
issue's own `implementation` branch, or a human adding a
`maintenance-targets` line naming that program issue to issue #2432's
body) — derived: `gh issue comment 2432 ...`, this turn. This copy lands
under this issue's own `implementation/` subtree instead, with the
frozen-path content below unchanged.

---

Gate deliverable for the stage-4 branch/record naming cutover proposal
(issue #2432). States plainly what happens to every branch already
using the old `issue-<n>/<role>` naming when this stage lands, per the
proposal's Rationale.

## What happens to an in-flight branch

Every branch open at this stage's landing time keeps its
`issue-<n>/<role>` name and finishes its lifecycle exactly as today —
reviewed, merged or closed, with no naming-related change. This stage
does not rename any branch, re-point any open PR's `head`, force-push
any existing branch, or touch the content of any commit already on an
open branch — derived: the diff this stage's own PR carries (`git diff
main...issue-2432/implementation`, this turn) touches only `pipeline.py`,
`board.py`, `roster.py`, `spawn.py` (new functions + re-exports, no
existing function deleted or renamed),
`test/test_branch_naming_dual_scheme.py`,
`docs/handbooks/branch-naming.md`, and this issue's own docs tree — no
`git branch`/`push --force`/`gh pr edit` invocation appears anywhere in
this session's command history.

Only newly spawned sessions **after** this stage lands are eligible to
use the new `issue-<n>/<skill>-<lease-disambiguator>` naming — and even
then, only once a future stage wires `spawn.py`'s live spawn path to call
`pipeline.checkout_issue_branch_for_skill()` (this stage adds that
function and the `board.py` dual-scheme reader; it does not flip the
default spawn path, since `spawn.py --skill ...` does not spawn a live
session yet — canonical: `spawn.py`'s own `--skill` branch, read this
turn: prints the resolved guidance JSON and `return 0` without calling
`checkout_issue_branch`/`_spawn_one` anywhere in that branch). Today's
only live session-spawning path is still the role positional
(`spawn.py <role> "<task>"`), which is untouched by this stage.

## Live re-check at landing time

acceptance: `gh pr list --state open` (this turn, before this stage's own
PR was opened) — result:
```json
[{"headRefName":"issue-2414/conformance-review","number":2435,"title":"issue-2414: re-review PR #2422's CHANGES-round stale-figure fix"},{"headRefName":"issue-2431/implementation","number":2434,"title":"issue-2431: drop the calendar bound for confirmed-dead-pid spawn-attempt orphans"},{"headRefName":"issue-2409/conformance-review","number":2420,"title":"issue-2409: conformance-review phase-1 (survey + proposal)"},{"headRefName":"issue-2409/execution-observation","number":2419,"title":"issue-2409: execution-observation phase-1 (survey + proposal)"},{"headRefName":"issue-2409/implementation","number":2416,"title":"issue-2409: attack exploratory-Bash, hook-refusal, and redundant-read waste"}]
```

5 open PRs at this stage's build time (the proposal's survey-time count
was 4 — expected drift, stated in the proposal's own Constraints). All 5
branch names are `issue-<n>/<role>` shape (`implementation`,
`conformance-review`, `execution-observation`) — none use the new
`<skill>-<disambiguator>` shape, which is expected since no live spawn
path produces that shape yet.

None of this stage's changes touch any branch-name regex or matching
site that these 5 PRs' branches would hit — derived: `grep -n
"checkout_issue_branch(\|board\.board(\|_sp\.board(" pipeline.py board.py
spawn.py`, this turn: every call site of the two modified functions
still calls them with the same arguments/shape as before this stage's
diff.

- `board.board()` gained an additive-only extension
  (`board._skill_axis_report_names()`) that runs *in addition to* the
  existing `_sp.ROLES` loop — the existing loop's own code (its `for r in
  _sp.ROLES` comprehension) is unedited by this stage's diff.
- `pipeline.checkout_issue_branch()` (the function these branches were
  created through) now delegates its checkout mechanics to
  `pipeline._checkout_named_branch()`, a pure extraction of the same
  logic that previously lived inline in that function, with no behavior
  change — acceptance: `python3 -m pytest
  test/test_branch_naming_dual_scheme.py -q` — result:
  ```
  9 passed in 0.91s
  ```
  (`CheckoutNamingSchemeTest::test_old_scheme_branch_shape_byte_identical`
  pins the old-scheme output shape against a live local git checkout).
- No hook, gate, or regex site that parses `issue-<n>/<role>` branch
  names (e.g. `pipeline.recut_if_absorbed_cli`'s own
  `re.fullmatch(r"issue-\d+/[A-Za-z0-9_-]+", br)`) was edited by this
  stage's diff — derived: `git diff main...issue-2432/implementation --
  pipeline.py`, this turn, shows no change inside
  `recut_if_absorbed_cli`.

Confirms: every currently-open PR still resolves correctly under the
dual-scheme reader; none becomes invisible to the board.

## Post-landing diff check

No existing open PR's branch name or content changed as a result of this
stage landing — derived: this stage's own PR's diff (`git diff
main...issue-2432/implementation`, this turn) only adds new files and
additive functions/re-exports in `pipeline.py`/`board.py`/`roster.py`/
`spawn.py`; it does not commit to, rename, or re-point any of the 5
branches listed above. A second `gh pr list --state open` run right
before this stage's own PR was opened shows the same 5 pre-existing
entries unchanged, plus this stage's own new PR as a 6th entry once
opened — not a modification of any of the 5 (see this issue's
implementation record for that second paste).
