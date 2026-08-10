# issue-684 — current-state survey: generated write paths in target repos

derived: `grep -nE "write_text\(|open\([^)]*['\"]w|\.mkdir\(|shutil\.(copy|move)" on-the-record/hooks/*.sh` plus manual read of each hit and its enclosing hook.

## Inventory (generator: file, line -> path written -> classification)

| generator | file | line | path written | key material | classification |
|---|---|---|---|---|---|
| `record-scaffold.sh` | `on-the-record/hooks/record-scaffold.sh` | 90 | `<target-repo>/docs/issue-<n>/reports/<role>.md` | `<n>` = CLI arg `issue-n`, `<role>` = CLI arg | issue-scoped (safe) |
| `delegated-judgment-gate.sh` (triage) | `on-the-record/hooks/delegated-judgment-gate.sh` | 589 | `<target>/docs/issue-<n>/decisions/*` (via `TRIAGE_DECISIONS_DIR`) | `<n>` = payload-derived issue number (same file, line 555) | issue-scoped (safe) |
| `delegated-judgment-gate.sh` (auto decision) | `on-the-record/hooks/delegated-judgment-gate.sh` | 678 | `<target>/docs/issue-<n>/decisions/auto-<seq>.md` | `<n>` from payload (same file, line 120); `<seq>` sequential within that dir | issue-scoped (safe); `<seq>` collision is within-issue same-role concurrency, out of this issue's cross-issue scope |
| `delegated-judgment-gate.sh` (remediation) | `on-the-record/hooks/delegated-judgment-gate.sh` | 759 | `<target>/docs/issue-<n>/decisions/remediation-<seq>.md` | same as above | issue-scoped (safe) |
| `product-capture-stopgate.sh` | `on-the-record/hooks/product-capture-stopgate.sh` | 150 | `<target-repo>/docs/product/<cat>.md` | `<cat>` = a fixed category label from `CATEGORIES` (e.g. `pricing`, `roadmap`) — **no issue number** | **collision-risk**: global-by-topic-name; two concurrent issue sessions both surfacing e.g. a "pricing" sentence append to the same file |
| `retry-loop-bound.sh` | `on-the-record/hooks/retry-loop-bound.sh` | 97 | `${OTR_RETRY_BOUND_STATE_DIR:-$TMPDIR/otr-retry-bound}/<session_id>.json` | keyed by session id, rooted at `$TMPDIR` | out-of-tree (safe) — never inside the target repo's git tree |
| `self-update.sh` | `on-the-record/hooks/self-update.sh` | 46 | `$CHECKOUT/.shallow-check` where `$CHECKOUT` = `$TOKENMAXXXER_CHECKOUT` or `~/.claude/tokenmaxxxer/on-the-record` | fixed marker name, but path is the **shared plugin checkout**, not the target repo | out-of-tree relative to target repo (safe from the git-merge-conflict framing this issue targets); cross-session races on the same marker are a liveness concern, not a target-repo git collision, and out of this issue's scope |
| `directive.sh` | `on-the-record/hooks/directive.sh` | 37 | `git clone` into `$own` (same shared checkout path as above) | fixed | out-of-tree (safe), same reasoning as self-update.sh |
| `impact-guard.sh` | `on-the-record/hooks/impact-guard.sh` | 51 | same shared checkout clone | fixed | out-of-tree (safe) |
| `decision-queue-stopgate.sh` | `on-the-record/hooks/decision-queue-stopgate.sh` | 41 | same shared checkout clone | fixed | out-of-tree (safe) |

## Hooks confirmed to generate nothing (n/a)

Read for write side-effects (`write_text`, `open(...,'w')`, `mkdir`, `shutil.copy/move`) — none found: `accumulation-claim-guard.sh`, `approval-gate.sh`, `call-shape-guard.sh`, `claim-scan-preflight.sh`, `contract-guard.sh`, `deliverable-guard.sh`, `pr-preflight.sh`, `record-claim-guard.sh`, `report-framing-check.sh`, `role-axis-completeness-guard.sh`, `role-spec-reference-guard.sh`, `role-test-claim-guard.sh`, `spec-index-preflight.sh`, `stop-gate.sh`. These read/validate only.

## Vendored gates (`gates/*.py`, `on-the-record/gates/*.py`)

Searched the same write-call set: no `write_text`/`open(...,'w')`/`mkdir` hits outside the hooks above. Gates in `gates/` run in CI against the plugin's own repo (this repo), not as generators inside a target repo's worktree — out of this issue's "writes into a target repo" scope, confirmed via `gates/test_boundary.py`'s own framing (checks `gates/*.py`, `on-the-record/hooks/*.sh`, `.github/workflows/*.yml`, `spawn.py` completeness against `docs/specs/enforcement-boundary.md`, not target-repo writes).

## Existing enforcement pattern to reuse

`gates/test_boundary.py` derives its mechanism inventory from `Path.glob` over `gates/*.py` and `on-the-record/hooks/*.sh` (function `_actual_mechanisms`, near the top of the file) and cross-checks it against a markdown table in `docs/specs/enforcement-boundary.md`. The same shape — glob the hook sources, derive the generated-path set mechanically (not hand-maintained), assert each is out-of-tree or issue-scoped — is the pattern this issue's acceptance criteria call for.

## One finding requiring a fix

`product-capture-stopgate.sh` line 150 builds `docs/product/<cat>.md` from a fixed category label only — no issue number, no out-of-tree root. Two concurrent sessions on different issues that both trip the same product-signal category (e.g. both mention pricing) append to the identical path, producing a human-resolved merge conflict on a file neither session's issue owns. This is the one violating generator the survey found.
