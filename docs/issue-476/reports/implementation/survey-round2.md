# current-state survey — issue #476 round 2 (implementation)

## Scope

Build target: a new zero-install `PreToolUse` hook script under
`on-the-record/hooks/`, per
`docs/issue-476/proposals/architecture-round2.md` (approved,
`APPROVE issue-476/architecture`, PR #572 merged). The architecture
proposal is an ADR-shaped decision that already fixes the hook's file
path, matcher regex (verbatim inheritance of `pr-preflight.sh`'s), ported
check logic (verbatim copy of `gates/claim_scan.py`'s `CLAIM_RE`/
`EVIDENCE_MARKER_RE`/fence-adjacency, not an import), all three fail
branches (ambiguity/positive-hit-warn/future-deny), the kill switch, and
the `hooks.json` insertion point. This survey exists to confirm the
write set is real and to check whether any design decision is still
open for this round — per the scout-directive skip condition, not to
re-derive the design.

## Skip condition invoked (scout-directive)

**"the spec leaves no design decision open."** Architecture-round2's
Decision section (points 1-7) pins: file path, matcher regex text, the
exact source module and constant names to port, the three-branch fail
structure with each branch's exit code, the kill-switch shape verbatim
from `pr-preflight.sh`, and the H1b two-week/60% flip rule text to cite
in the header. Nothing in this round is a build-direction choice —
implementation is a character-for-character port plus wiring. No scout
sweep was run; this is the mandatory skip record, not an omission.

## Files read to confirm the write set

- `gates/claim_scan.py` (current `HEAD`) — the source of the four names
  the proposal must port verbatim: `CLAIM_RE`, `EVIDENCE_MARKER_RE`,
  `FENCE_RE`, and the fence-adjacency helper trio
  (`_fence_spans`/`_in_fence`/`_nearby_evidence`, adjacency window
  `ADJACENCY_LINES = 5`). `TARGET_RE`/`_cite_matches`/`_dotted_to_file`
  (repo-target traceability) are **not** in architecture-round2's ported
  list — the ADR's point 3 names only "`CLAIM_RE`, `EVIDENCE_MARKER_RE`,
  and the code-fence adjacency check," not target traceability.
  Confirmed by re-reading point 3's text: it says nothing about
  `repo_targets`/`_cite_matches`, and point 5's warn-mode finding shape
  is "claim vocabulary present with no adjacent evidence marker/fence"
  only — traceability is out of this round's scope, matching
  `scan_text`'s own `repo_targets=None` mode (text-only judgment, no
  repo read).
- `on-the-record/hooks/pr-preflight.sh` (current file, read in full) —
  confirmed the exact patterns to inherit verbatim: the kill-switch line
  (`case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;;
  esac`), the `gh\s+pr\s+(create|edit)` regex against the raw `Bash`
  command string via `re.search`, and the `--body`/`--body-file`
  extraction regex pair (quoted/unquoted value capture, unreadable
  body-file yields `exit 0`). No PR-lookup/phase/plan logic from
  `pr-preflight.sh` is relevant here — this new hook does not gate on
  issue phase or plan completeness, only on claim-scan findings.
- `on-the-record/hooks/hooks.json` (current file, read in full) — the
  `PreToolUse` `"Bash"` matcher array currently lists, in order:
  `contract-guard.sh`, `pr-preflight.sh`, `spec-index-preflight.sh`,
  `impact-guard.sh`. Architecture-round2 point 1 places the new entry
  immediately after `pr-preflight.sh` and before
  `spec-index-preflight.sh` — confirmed this is a small JSON insertion
  (one object) between those two existing entries, no other array
  touched.
- `on-the-record/hooks/record-claim-guard.sh` (read in full) — confirmed
  it resolves `gates/claim_scan.py` via a relative-path `sys.path`
  insert back to the dev-checkout `gates/` directory (same-repo
  convenience, not a zero-install pattern) — this is the precedent
  architecture-round2's Decision point 3 and Alternatives-considered #1
  name as rejected for this new hook; confirmed still true by direct
  read, not assumed from the ADR's prose. The same file's own guard
  logic (this repo's own dogfooding) also confirms, live: a
  backtick-quoted relative path referenced in new record/proposal
  content must already exist in the working tree, or the write is
  denied (issue #330 mirror) — meaning this survey and the proposal it
  feeds must describe not-yet-created files in prose, never as a
  backtick-quoted path, until they exist.

## Existing conventions to match (mechanical, not a design choice)

- Every `PreToolUse` `Bash` guard in this repo reads the JSON payload
  from stdin via `payload="$(cat 2>/dev/null || true)"`, passes it to an
  embedded Python heredoc via an environment variable plus `python3 -c`,
  and the Python side re-parses it with `json.loads` guarded by a broad
  `except ValueError: sys.exit(0)` — `pr-preflight.sh`'s stdin handling
  is the exact shape to copy for the new hook.
- `additionalContext` output shape: Claude Code's `PreToolUse` hook JSON
  contract expects a `hookSpecificOutput.additionalContext` string on
  stdout for a non-blocking advisory message — checked against an
  existing `on-the-record/hooks/` sibling (`spec-index-preflight.sh`)
  that already emits this exact shape on its own warn path, confirmed by
  direct read. The new hook's warn-mode branch (architecture-round2
  point 5) reuses this same JSON shape plus a mirrored stderr write, not
  a novel output contract.
- The repo's `test/` tree holds root-level Python test scripts
  (`test_latency_report.py`, `test_portability_audit_table.py`, etc.) —
  no subdirectory for hook-specific tests and no existing test file for
  any hook script under `on-the-record/hooks/` was found; hook scripts
  in this repo are currently untested by any committed test file. The
  proposal's test file is therefore a new root-level `test/`-tree
  script following the same plain-function-plus-`main()` runner shape
  as the `gates/test_*.py` files, invoking the shell script as a
  subprocess and asserting on exit code plus stdout/stderr JSON.

## Write set (confirmed real, matches architecture-round2's Files section)

- A new hook script under `on-the-record/hooks/` (name fixed by
  architecture-round2's own header: `claim-scan-preflight.sh`).
- `on-the-record/hooks/hooks.json` — one new array entry.
- A new test script, root-level under `test/`, covering the new hook
  (new file, no prior test to extend).
- `on-the-record/UNENFORCED-CLAUSES.md` — gates-table row update per
  architecture-round2's Files section (`claim_scan.py`'s enforcement
  class changes from CI-supplement to zero-install-hooked now that a
  second site enforces it).
- `docs/issue-476/reports/implementation.md` — phase-2 record, waits for
  Approve per contract.

## Open questions the proposal must settle

None — architecture-round2 leaves no design decision open for this
round (see Skip condition above). The proposal's remaining job is
sequencing the port and stating the test plan's exact assertions.
