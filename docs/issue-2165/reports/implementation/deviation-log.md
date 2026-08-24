# issue-2165 — deviation log

- 2026-08-24T07:19:16Z inline: during investigation, briefly edited
  gates/spawn_on_pr.py (added the sticky merged-seen cache directly)
  before recognizing this is a phase-1 (survey+proposal) session with no
  CORE_BUILD_NOW and no prior Approve — code changes belong to phase 2.
  Reverted via `git checkout -- gates/spawn_on_pr.py` before any commit;
  the design was carried forward into
  docs/issue-2165/proposals/2026-08-24-sticky-merged-confirmation-cache.md
  instead. No code ever landed from this; the edit never left the
  working tree and was never committed.
