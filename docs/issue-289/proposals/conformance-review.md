# Conformance-review proposal — issue-289 sandbox dotfile leak + lock masquerade (phase 1)

## Upstream / basis

Issue #289 (closed). Closing PRs: #300 (merged `09be57b0`, phase 1
survey/proposal + phase 2 `b22f46a8` — dotfile exclude on workspace
create, `_SANDBOX_REFUSAL_PATTERNS` regex for the lock-masquerade
message) and #421 (merged `9907b40c` — spec-index re-verification after
H2). Artifact: `spawn.py` (`issue_workspace()`,
`_SANDBOX_REFUSAL_PATTERNS`), `protocol.md`/`protocol.ko.md` §4,
`tests/test_spawn.py`. Related hunt record:
`docs/reports/2026-08-07-hunt-issue-289-phase2.md`.

## Requirement list (extracted from issue #289's Acceptance section; verdict deferred to phase 2)

1. **R1 — Fresh role workspace does not surface home dotfiles to `git
   status`; the write-set exclusion covers the full dotfile set, not a
   sample.** Source: issue #289 acceptance bullet 1, check `test_spawn.py`.
   Live run this session: `tests/test_spawn.py::WorkspaceExcludesHomeDotfiles::test_fresh_workspace_excludes_dotfile_set`
   PASSED.
   Open concern carried into phase 2: `docs/reports/2026-08-07-hunt-issue-289-phase2.md`
   records a live-reproduced finding that `issue_workspace()`'s dedupe
   (`missing = [ln for ln in lines if ln.rstrip("/") not in existing]`,
   `spawn.py:5919` in this session's checkout) is a whole-file substring
   check, not a line-exact match — an unrelated existing line that merely
   *contains* a dotfile name as a substring (e.g. a comment mentioning
   `.bashrc`) silently suppresses that dotfile's exclude entry. The passing
   test above only exercises a freshly-created workspace with an empty
   `.git/info/exclude`, never the pre-existing-content case the hunt
   reproduced — so R1's "covers the full set rather than a sample" clause
   is Present for the tested scenario but the dedupe's robustness is
   unverified against the substring-collision case. Phase 2 renders a
   verdict on this distinction explicitly rather than treating the passing
   test as closing the requirement outright.

2. **R2 — A sandbox-denied git operation is reported as a denial rather
   than as `File exists`.** Source: issue #289 acceptance bullet 2, check
   `test_spawn.py`. Live run this session:
   `tests/test_spawn.py::EventReporting::test_git_lock_masquerade_is_classified_as_sandbox_refusal`
   PASSED. Check: `_SANDBOX_REFUSAL_PATTERNS` (`spawn.py`) carries a regex
   scoped to `cannot lock config file .*\.git/config.*: File exists`,
   narrow enough not to swallow unrelated "File exists" errors.

3. **R3 — The recorded spec-index hash matches the tracked files, so a
   doc note landing alongside a fix cannot leave the index stale.**
   Source: issue #289 acceptance bullet 3, check
   `test_spec_index.py::t_baseline_repo_passes`. Live run this session:
   PASSED.

4. **R4 — No session needs to delete a lock file to make progress.**
   Source: issue #289 acceptance bullet 4, marked `unverifiable` in the
   issue body itself ("absence of a workaround across future sessions,
   which no single run can establish"), with a named mechanical stand-in:
   the R2 refusal-pattern check above, which turns the condition that
   provoked the workaround (a masqueraded denial) into a named denial
   instead of a bare `File exists`. Phase 2 records this as Unverifiable
   with the same reason, not as a gap.

## Out of scope (phase 2 will not re-litigate)

- Whether the dotfile list itself (`.bashrc`, `.bash_profile`, `.profile`,
  `.zshrc`, `.zprofile`, `.gitconfig`, `.gitmodules`, `.mcp.json`,
  `.claude/`, `.idea`, `.vscode`, `.ripgreprc`) is exhaustive of every
  possible sandbox-overlaid dotfile — issue #289's own H1 finding named
  this specific set from direct `git status` observation in three
  workspaces; auditing for additional undiscovered overlay files is a new
  hunt, not a conformance check against this issue's stated requirements.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic quality
  read.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `spawn.py`, `test_spawn.py`,
`test_spec_index.py`, `protocol.md`/`protocol.ko.md` §4, and issue #289's
own body/acceptance section — the builder's `docs/issue-289/reports/
implementation.md` prose is not read as evidence for verdicts, consistent
with this role's artifact-only rulebook; it may be cited only to locate
code, never to substitute for reading the code directly. R1's
substring-dedupe concern is resolved by direct re-read of the current
`issue_workspace()` source at phase-2 time (already reproduced once this
session; re-confirmed against the current tree, not assumed carried over
from the hunt record).

## What did not work

(none yet — phase 1, no verdicts attempted)

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

- R1's dedupe-robustness gap (substring vs. line-exact match) is flagged
  above for phase-2 verdict; the passing test does not cover it, and the
  hunt record's live reproduction still reproduces against the current
  `spawn.py` (`missing = [ln for ln in lines if ln.rstrip("/") not in
  existing]`, unchanged since the hunt record was written).

## Next steps

Await approval (`APPROVE issue-289/conformance-review` per contract v3
s19, single-account mode, from a `docs/specs/approvers.md`-listed
account). On approval: render the phase-2 per-requirement verdicts (R1-R4
above) in `docs/issue-289/reports/conformance-review.md`.

## Resolution path

Phase 2 resolves R1 by re-reading `issue_workspace()`'s dedupe logic
against the substring-collision reproduction above and rendering an
explicit verdict (likely Present-with-caveat or Incorrect, not a bare
Present) rather than letting the passing fresh-workspace test stand in
for the full "covers the full set rather than a sample" acceptance
clause.
