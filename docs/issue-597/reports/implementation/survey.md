# Current-state survey — issue-597, implementation phase

## Write surface: `delegated-judgment-gate.sh`

`on-the-record/hooks/delegated-judgment-gate.sh` (418 lines) is a
`PreToolUse`/`Bash` hook already registered in `on-the-record/hooks/hooks.json`.
Its Python payload (embedded via heredoc) inspects `tool_input.command` for
`gh pr create` (`re.search(r"\bgh\s+pr\s+create\b", cmd)`), derives
`issue`/branch from `git rev-parse --abbrev-ref HEAD` matched against
`issue-(\d+)/([\w-]+)`, and posts via a `_gh()` helper that shells out to
`gh issue comment <n> --body-file -`/`--body` (best-effort, fail-open — a
posting failure never changes the hook's own exit code, matching
`pr-preflight.sh`'s posture). Adding a sixth firing condition means adding
new `re.search` dispatch arms beside the existing `gh pr create` check,
each producing its own `_gh()` call — no new hook registration needed
(architecture.md section 2 confirms this).

## Existing firing conditions (for the "sixth condition" framing)

The script's Python body currently branches on exactly one command shape
(`gh pr create`) and, following AND-rule resolution, posts at most four
issue-timeline lines per run: "Judgment opened" (unconditional once
`gh pr create` matches and diff paths are non-empty), "Verdict: ... →
escalate" (early-return branches), "Verdict: ... → approve/reject" (after
full panel synthesis), "Remediation routed round N", and "Escalated to
operator". Issue #597's architecture.md table names five section-12
events including "Remediation PR merged" as a sixth-adjacent count, but
that event's underlying merge-detection call does **not** exist anywhere
in this script or in `spawn.py` (see next section) — it was explicitly
scoped out of issue-573's own implementation phase
(`docs/issue-573/proposals/implementation.md` "Out of scope": *"wires the
comment-posting call for that event but does not build a new
merge-watcher"* — and even that wiring was never added; no
`"Remediation merged"` string exists in the tree).

## Delivery-merged detection: no existing signal to reuse

Architecture.md's trigger table (section 2, row 1) claims delivery-merged
reuses `spawn.py`'s watch/session-end signal, citing
`_post_session_end_comment()` in `spawn.py`
(`_SESSION_END_COMMENT_MARKER = "[watch] {key}: session-end:"`). Reading
that function: it posts once per session end, with body `"... {line}"`
where `line` is `"PR #<n> opened"` (if a PR is open OR merged —
`_pr_open_or_merged_for_branch` does not distinguish the two states in
the posted text), `"no PR (pr-check-failed)"`, or `"no PR"`. **There is no
merge-specific event or marker distinguishable from "opened."** The
architecture proposal's row is aspirational, not a reusable signal — this
survey corrects that for the implementation phase. Building on it would
mean parsing ambiguous prose out of `spawn.py`, a `CONTRACT_ROOT_FILES`-tier
file per `delegated-judgment-gate.sh`'s own reversibility table (the
highest-risk `AXIS_MAX` impact tier), for a large file (3900+ Python
lines) well outside this hook's component boundary
(`docs/issue-573/proposals/implementation.md` "Out of scope": *"Any
change to `impact-guard.sh` or `gates/risk_report.py` ... both are
read-only dependencies"* — the same boundary logic applies to `spawn.py`,
never touched by any existing hook here).

Alternative available in the SAME file already being extended: `gh pr
merge` is itself a `Bash` command, visible to the exact same
`PreToolUse`/`Bash` hook this script already runs as, at the exact
detection mechanism architecture.md's own prose describes for all three
transitions — *"by pattern-matching the `gh` command about to run, at the
same `PreToolUse` point"* (architecture.md section 2, lead sentence,
which the row table then contradicts for row 1 only). Matching `gh pr
merge` keeps the entire write set inside `on-the-record/hooks/`, at the
low-impact tier this script already occupies, and needs no new detection
channel at all — the `Bash` hook already fires on every outgoing command,
`gh pr merge` included.

## Reopen/close detection: direct precedent

No existing script matches `gh issue reopen`/`gh issue close`. Same
`PreToolUse`/`Bash` payload, same `re.search` idiom as the existing `gh pr
create` match — a single-line addition per command, consistent with the
existing dispatch style (guard clause + `sys.exit(0)` when no transition
command matches).

## Citation-resolvability precedent to reuse

`record-claim-guard.sh` (134 lines, `on-the-record/hooks/`) already ports
`gates/record_lint.py`'s `orphaned_path_reference_check(root, text)` —
given a repo root `Path` and text, it regex-extracts backtick-quoted
relative paths and reports any that don't resolve under `root` (function
defined in `gates/record_lint.py`). This is exactly the "citation must
resolve" mechanism architecture.md section 4 calls for.
`record-claim-guard.sh` resolves `gates_dir` relative to
`${BASH_SOURCE[0]}` (`script_dir/../gates` or `script_dir/../../gates`)
and does `sys.path.insert(0, gates_dir); import record_lint`.
`delegated-judgment-gate.sh` explicitly avoids any `gates`-package import
per its own file-header constraint ("Zero-install consumer surface ...
no gates-package import and no on-the-record checkout resolution — the
four-axis reversibility grade this hook needs is ported inline below
rather than imported from `gates/risk_report.py`, so this script runs in
a target repo that never clones the on-the-record checkout at all").
The citation check must follow the same inline-port convention, not the
`record-claim-guard.sh` import path — a same-shape, ported-inline version
of `orphaned_path_reference_check` (existence check on a path string
against `TARGET`, plus a commit-sha regex fallback for the "or a valid
commit sha" clause architecture.md section 4 states) belongs inside this
script's own Python body, mirroring how the impact axis was already
ported inline from `gates/risk_report.py` for the identical zero-install
reason.

## Role-record and audit-record sources available to synthesize from

- `docs/issue-<n>/reports/<role>.md` — role records, read via the
  existing `role_record_path()` helper for the `judgment_axes` panel;
  the same helper resolves a record path for a given role from
  `roles/*.json`'s `write_scope`.
- `docs/issue-<n>/decisions/auto-<seq>.md` / `remediation-<seq>.md` —
  audit records this same script already writes, directly readable as
  citation sources for "resolved problem"/"still broken" (a
  `reject`/`escalate` verdict is a fact already on disk).
- Issue body acceptance criteria — available via `gh issue view <n> --json
  body` at transition time; the baseline (section 5) cites the issue
  itself when no prior record exists, per architecture.md's own worked
  example.

## Test-authoring precedent

`on-the-record/hooks/test_delegated_judgment_gate.py` (existing, live-fires
the real script against a synthetic bare-git TARGET repo with a stubbed
`gh` that logs invocations instead of touching the network) is the
established fixture pattern for this file — `_init_target()`,
`_stub_gh()`, then invoking `SCRIPT` via `subprocess.run` with
`DJG_PAYLOAD`/`DJG_TARGET` env vars matching the hook's own bash wrapper.
New tests for the three #597 transitions extend this same file rather
than adding a parallel fixture.

## Hand-off boundary already drawn by architecture.md

Architecture.md's "Out of scope (implementation-role territory)" section
explicitly leaves the reopen/close regex, the field-extraction logic
pulling record text into the four elements, and the test fixtures to this
phase — confirmed by this survey; no further architecture-level ambiguity
found blocking implementation. The one correction this survey makes to
architecture.md's own claim (row 1 of its trigger table) is scoped inside
"implementation-role territory" per that same section: *"The exact
regex/parse for matching `gh issue reopen`/`gh issue close` command
lines"* generalizes to *"the exact command-pattern each of the three
transitions is detected by,"* which is what this survey resolves for row
1 by choosing `gh pr merge` over the unusable `spawn.py` signal.
