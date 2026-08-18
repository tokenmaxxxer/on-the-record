# Survey — issue #1734

Write surfaces:

- `on-the-record/monitors/poll-heartbeat.sh:244-291` — the Python heredoc's per-line
  keying loop. `TAG_RE` (line 245) matches only an enumerated tag list
  (`poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr`)
  followed by `] name:`; `ENTRY_RE` (line 246) matches `path/like/entry: `;
  `BULLET_RE` (line 247) matches an indented `- ` continuation under the
  last seen key. Any line matching none of the three — an unenumerated
  bracket tag such as `[spawn-on-pr]`, or a fully freeform line — falls
  to the `else` branch at line 281, which unconditionally assigns
  `key = "__fixed__"`. The same-tick collision block at lines 282-289
  then disambiguates by appending an appearance-order ordinal
  (`__fixed__~1`, `__fixed__~2`, ...) whenever a key repeats within one
  tick's text — since every unkeyed line shares the literal `"__fixed__"`
  key before this disambiguation runs, that ordinal is assigned purely by
  the line's position in the block, not by its content.
  canonical: on-the-record/monitors/poll-heartbeat.sh:244-291 (this session, read verbatim)
- `on-the-record/monitors/poll-heartbeat.sh:305-324` — the diff loop that consumes
  `curr`/`order`: for each `key` in appearance order it compares
  `prev_lines.get(key)` against the current line's text and emits on
  mismatch (`first_tick or changed or ALWAYS_RE.search(line)`). Because
  ordinal keys are positional, inserting or dropping one unkeyed line
  shifts every following unkeyed line onto a different ordinal, so each
  shifted line is compared against a *different* line's previous text —
  the false "changed" verdict this issue reports.
  canonical: on-the-record/monitors/poll-heartbeat.sh:305-324 (this session, read verbatim)
- `on-the-record/monitors/poll-heartbeat.sh:333` — the bounded ~30-minute aliveness
  heartbeat's session count: `healthy = sum(1 for k in new_lines if "#" not
  in k and not k.startswith("__fixed__"))`. This is the one other site in
  the file that names the `__fixed__` key literally; any rename of the
  unkeyed-line key scheme must also update this filter or the "N
  session(s) tracked" count would start including fixed-class lines.
  canonical: on-the-record/monitors/poll-heartbeat.sh:326-343 (this session, read verbatim)
- `grep -rn '__fixed__' --include='*.py' --include='*.sh' .` (excluding
  `.git/`) — exactly two hits, both the two lines above, both inside
  `on-the-record/monitors/poll-heartbeat.sh`. No test file or other script
  matches the literal string, so the rename is contained to this one file.
  canonical: `grep -rn "__fixed__" --include="*.py" --include="*.sh" .` (this session) —
  output: `on-the-record/monitors/poll-heartbeat.sh:281:        key = "__fixed__"` and
  `on-the-record/monitors/poll-heartbeat.sh:333:        healthy = sum(1 for k in new_lines if "#" not in k and not k.startswith("__fixed__"))`
- `on-the-record/monitors/test_poll_heartbeat.py:93-108` — the existing `_run_tick(checkout,
  home, report)` two-tick-against-the-same-checkout harness (issue #1719),
  which drives `poll-heartbeat.sh` twice against the same `TOKENMAXXXER_CHECKOUT`
  so state persists across calls, exactly the shape the issue's Acceptance
  provenance calls for. `t_returned_pr_new_item_emits_on_due_tick` (lines
  484-505) and `t_board_sweep_lock_skip_treated_as_no_change` (lines
  508-532) already use this harness for adjacent delta-suppression
  behavior and are the closest existing precedent for the two new tests
  this issue's Acceptance calls for.
  canonical: on-the-record/monitors/test_poll_heartbeat.py:93-108, 464-532 (this session, read verbatim)
- `gates/test_poll_heartbeat_delta.py:26-27` — resolves `POLL_HEARTBEAT` as
  `REPO_ROOT / "on-the-record" / "monitors" / "poll-heartbeat.sh"`, confirming the
  Acceptance section's `monitors/poll-heartbeat.sh` and
  `monitors/test_poll_heartbeat.py` references are shorthand for the actual
  repo-relative paths `on-the-record/monitors/poll-heartbeat.sh` and
  `on-the-record/monitors/test_poll_heartbeat.py` — the repo root has no
  top-level `monitors/` directory of its own (`gates/` and its two
  `test_poll_heartbeat_*.py` siblings do live at repo root, unchanged).
  canonical: `find . -iname "poll-heartbeat.sh" -o -iname "test_poll_heartbeat*"` (this
  session) — output: `./on-the-record/monitors/poll-heartbeat.sh`,
  `./gates/test_poll_heartbeat_patrol.py`, `./gates/test_poll_heartbeat_delta.py`,
  `./on-the-record/monitors/test_poll_heartbeat.py`
- `pytest.ini:2` — `python_functions = test_* t_*`, confirming the
  repo's three `t_`-prefixed suites (`on-the-record/monitors/test_poll_heartbeat.py`,
  `gates/test_poll_heartbeat_delta.py`, `gates/test_poll_heartbeat_patrol.py`) are
  pytest-collectible as-is, matching the Acceptance section's
  `python3 -m pytest ...` invocation.
  canonical: pytest.ini:1-7 (this session, read verbatim)
- bash 3.2.57(1)-release is the installed `/bin/bash` and `bash` in this
  environment — the same stock macOS bash the file's own lines 224-232
  comment warns about (a documented landmine: editing this heredoc's
  comment apostrophe count has previously flipped `bash -n`/execution to
  a false "unexpected EOF" parse failure even though the `<<'PY'`
  delimiter is fully quoted). Any edit inside lines 233-347 needs a
  `bash -n on-the-record/monitors/poll-heartbeat.sh` re-check before landing.
  canonical: `bash --version` (this session) — output `GNU bash, version
  3.2.57(1)-release (arm64-apple-darwin25)`

Cross-issue note:
canonical: `gh issue view 1732 --json state,title` (this session) — output `{"state":"OPEN","title":"poll-heartbeat: drop the 30-minute 'monitoring active … no changes' line — it wakes the session with nothing to report"}`
Issue #1732 (OPEN per that output) proposes dropping the same `[heartbeat] monitoring active, ...` emit cited above at poll-heartbeat.sh:326-343 — the same `to_emit`/heartbeat block this issue's fix sits next to, not the lines this issue edits (244-291, plus the `__fixed__` filter at line 333).
canonical: `git merge-base --is-ancestor 89dd625d HEAD` (this session) — exit non-zero, "NOT ANCESTOR"
#1732's proposal commit `89dd625d` is not an ancestor of this branch's HEAD per that command, so no #1732 implementation has merged to main or this branch as of this survey, and no rebase conflict exists yet.

If #1732 lands on main first, this branch will later need to rebase past a deletion of lines 326-341, carrying the `healthy = ...` line's `fixed:` filter forward by hand; if this branch lands first, #1732's phase-2 session rebases past this issue's renamed key instead — both are ordinary same-function rebase conflicts, not a design conflict, since the two changes touch disjoint parts of the same `to_emit` block and do not depend on each other's outcome.

canonical: `gh issue view 1734` output (this session, read verbatim) — issue body carries `validity-consult-skip: trivial` and `design-research-skip: mechanical` as closed-vocabulary skip tags, and its Acceptance section fully specifies the fix (content-derived key from leading tag + check name, hash fallback, same-tick ordinal disambiguation kept) and the two new tests' shape.

Skip condition: pure bugfix — per the canonical citation directly above, the issue's own body specifies the exact keying replacement (tag+name primary, hash fallback, same-tick ordinal disambiguation unchanged) and both new test cases; no design decision is left open beyond the alternative already weighed in this survey's cross-issue note. `validity-consult-skip: trivial` and `design-research-skip: mechanical` are the issue's own skip tags. Scouting is skipped per scout-directive's pure-bugfix skip condition.
