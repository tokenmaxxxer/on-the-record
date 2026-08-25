---
proposal: docs/issue-2211/proposals/conformance-review.md
---

# Hunt record — conformance-review

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — survey.md misattributes its cited live PreToolUse read-block to `approval-gate.sh`, but that script (on-the-record/hooks/approval-gate.sh, identical to the live marketplace-installed copy) only ever inspects `Write|Edit|MultiEdit` payloads and structurally allows any `Bash` read; the message the survey actually quotes ("no Approve review on an open PR...") never appears anywhere in that script's own `deny()` call sites.
Kind: design-error
Seed: docs/issue-2211/proposals/conformance-review.md, docs/issue-2211/reports/conformance-review/survey.md (git diff --cached origin/main)
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 342
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:45:00Z

### Reproduce

survey.md's "Board / approval state" section cites, as canonical evidence for the phase-1/phase-2 boundary:

> this session's own PreToolUse denial when a Bash read named a path
> under docs/issue-2211/reports/implementation/ (a different role's
> phase-2-only material), verbatim: "neither the PR for
> issue-2211/conformance-review nor issue #2211 carries an approval
> from a listed human approver (jiwonjung94, jjongkwann)..." — live
> evidence that phase 2 is not yet open for this role.
canonical: `git diff --cached origin/main -- docs/issue-2211/reports/conformance-review/survey.md`, its "Board / approval state" section (this session, this diff).

and the survey's closing "other mounted skills" line states the
phase-1/phase-2 boundary is "enforced live by approval-gate.sh (see
'Board / approval state' above)."
canonical: same diff, closing line of the "skill-verdict"/"other mounted skills" block.

Step 1 — read `on-the-record/hooks/approval-gate.sh` (the file the
survey names). It gates only Write/Edit/MultiEdit:

```
if not isinstance(e, dict) or (e.get("tool_name") or "") not in ("Write", "Edit", "MultiEdit"):
    sys.exit(0)
```
canonical: `on-the-record/hooks/approval-gate.sh` lines 68-71 (read directly, this session); confirmed byte-identical to the live installed copy via `diff -q on-the-record/hooks/approval-gate.sh ~/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/approval-gate.sh` (executed this session, no output = identical).

and its own header comment says so explicitly: "the only two hooks
that read an APPROVE comment (contract-guard.sh, pr-preflight.sh) are
both Bash-matcher, gated on `gh pr` verbs only, never reached by a
plain write" — i.e. by the script's own account, nothing in the
Write-tools-only approval-gate.sh path is reached by a Bash read
either.
canonical: `on-the-record/hooks/approval-gate.sh` header comment lines 4-7 (read directly, this session).

Step 2 — extract that exact guard body by line range and run it in
isolation against a synthetic `tool_name: "Bash"` payload targeting the
exact path the survey names:

```
sed -n '67,330p' on-the-record/hooks/approval-gate.sh > /tmp/hunt-test/guard_body.py
```
canonical: command executed directly this session; verbatim shell output confirmed by `wc -l /tmp/hunt-test/guard_body.py` -> 264.

then (as a plain `.py` file, `/tmp/hunt-test/run_guard.py`, no `-c`/heredoc, written via the Write tool this session):

```python
import json, os, runpy
os.environ["AG_PAYLOAD"] = json.dumps({
    "session_id": "x", "tool_name": "Bash",
    "tool_input": {"command": "cat docs/issue-2211/reports/implementation.md"},
    "cwd": "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2211-conformance-review",
})
os.environ["CLAUDE_ROLE"] = "conformance-review"
try:
    runpy.run_path("/tmp/hunt-test/guard_body.py", run_name="__main__")
    print("COMPLETED WITHOUT sys.exit -> falls through as allow")
except SystemExit as e:
    print("approval-gate.sh guard exit code for a Bash-tool payload:", e.code)
```

run with `python3 /tmp/hunt-test/run_guard.py`.
canonical: `/tmp/hunt-test/run_guard.py`, executed directly this session (see Observed for its stdout).

Step 3 — separately confirm the exact deny text the survey quotes does
not exist anywhere inside `approval-gate.sh` itself:

```
grep -n "carries an approval from a listed human approver" on-the-record/hooks/approval-gate.sh
grep -n "Approve review on an open PR" on-the-record/hooks/*.sh
```
canonical: both commands executed directly this session (zero matches for either, see Observed).

### Observed

- `python3 /tmp/hunt-test/run_guard.py` prints: `approval-gate.sh guard
  exit code for a Bash-tool payload: 0` — approval-gate.sh, exactly as
  shipped in this repo (and identical to the live marketplace install
  per the Step-1 `diff -q`), *allows* a Bash read of another role's
  un-approved phase-2 record. It never branches on Bash payloads at
  all; the phase-2-target check, the approvers.md/APPROVE-comment scan,
  and every `deny()` call site are unreachable from a `tool_name:
  "Bash"` event.
  canonical: `/tmp/hunt-test/run_guard.py` stdout, this session.
- Both greps in Step 3 return zero matches: `approval-gate.sh`'s own
  `deny()` text is "no matching 'APPROVE issue-%d/%s' issue comment ...
  needs phase-2 approval first" (lines ~283-291) — nowhere does it
  construct the phrase "carries an approval from a listed human
  approver" or mention a PR review at all (it only ever reads `gh issue
  view --json comments`, never `gh pr view`/`gh api .../reviews`). The
  text survey.md quotes verbatim is not producible by this file for any
  input.
  canonical: `on-the-record/hooks/approval-gate.sh` lines 283-291 (read
  directly, this session); grep commands from Step 3 (executed this
  session, zero output for both).
- Separately, this session did observe a live PreToolUse block with
  that exact wording when actually attempting a Bash read of the
  implementation role's record on the `issue-2211/implementation`
  branch — confirming the boundary itself is real and live-enforced by
  *something* — but the accompanying denial also carried a second,
  distinct message prefixed `board-gate:` naming a foreign-role-record
  refusal. No file matching `*board-gate*`, and no occurrence of the
  string "board-gate", exists anywhere under `on-the-record/hooks/` or
  in `on-the-record/hooks/hooks.json` in this repo.
  canonical: `find on-the-record/hooks -iname "*board-gate*"` and
  `grep -n "board-gate" on-the-record/hooks/hooks.json` (both executed
  this session, zero output/matches).

### Expected

If survey.md's citation were accurate, the isolated guard-body run in
Step 2 should have denied (nonzero exit, with text drawn from
approval-gate.sh's own `deny()` calls) for a Bash read of another
role's phase-2-only record. Instead it allows unconditionally, and the
literal deny text the survey quotes cannot be produced by this file for
any input (Step 3). The survey's "Board / approval state" section
should have cited the actual enforcing script (evidently something
outside `on-the-record/hooks/` entirely, given the `board-gate:`
co-occurring message with no matching file in this tree) rather than
attributing live read-side enforcement to
`on-the-record/hooks/approval-gate.sh`, which — as shipped in the very
repo under conformance review — provides no such enforcement.
