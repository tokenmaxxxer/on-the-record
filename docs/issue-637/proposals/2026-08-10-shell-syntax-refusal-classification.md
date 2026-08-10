---
status: proposed
files:
  - docs/issue-637/reports/technical-feasibility/survey.md
  - docs/issue-637/proposals/2026-08-10-shell-syntax-refusal-classification.md
  - docs/issue-637/reports/technical-feasibility.md
---

## Request

Step 1 of #637: catalogue the exact blocked-command shapes from #623's
cross-cutting Scope A row, reproduce each refusal, and classify each as
fixable-on-our-surface vs harness-boundary-to-document, without
weakening any of this repo's own gates.

## Context

`docs/issue-623/reports/execution-observation.md`'s cross-cutting row
reports a live false-reject: a multi-line `for`-loop and a
JSON-literal Python heredoc were both refused pre-execution mid-drive,
forcing a file-based workaround — a live instance of the #476
`false_reject` class. That record explicitly declined to diagnose the
refusing surface ("diagnosing the analyzer's matching logic would
require reading `contract-guard.sh`'s internals as a fix, which is out
of scope for an observation role") and routed the diagnosis to this
issue.

This session reproduced the same command shapes live
(docs/issue-637/reports/technical-feasibility/survey.md, "Reproduction,
this session") and traced the refusal source to `spawn.py`'s own
refusal-classifier comment, which documents — independently of this
issue, at spawn.py:2231-2236 — that the matched patterns
(`cannot be statically analyzed`, `simple_expansion`) belong to the
harness command-approval layer (issue #232's layer taxonomy), not to
any `on-the-record/hooks/` or `gates/` gate
(docs/issue-637/reports/technical-feasibility/survey.md, "Root-cause
layer"). A repo-wide grep confirms no gate or hook in this repo emits
either matched string.

## Timebox and acceptance criteria

Timebox: this phase-1 step is already complete as scoped (reproduction
+ classification), no further spike needed — 0 additional days beyond
this session. Acceptance: (1) both #623-cited refusal shapes are
reproduced with their exact refusal text recorded; (2) each is
classified fixable-on-our-surface or harness-boundary-to-document with
a stated reason; (3) whatever is fixable ships as guidance, verified by
a re-run showing no refusal or a documented low-friction path — per
issue #637's own Acceptance section (`gh issue view 637`).

## Candidates considered

1. **Narrow the harness's own shell-syntax analyzer** (patch the
   pattern-matching logic that emits `cannot be statically analyzed` /
   `simple_expansion`) — rejected: that analyzer lives outside this
   repo's own surface (confirmed: no match for its refusal strings
   under `on-the-record/hooks/` or `gates/`, only inside `spawn.py`'s
   *classifier of* those strings) — patching it is not ours to do and
   is exactly the "weaken a gate we don't own" move issue #637 warns
   against attempting on the wrong surface.
2. **Do nothing beyond #623's existing action item** (route to a fresh
   remediation issue against #476, as #623's record already proposed)
   — rejected as the *only* action: it leaves the workaround
   undocumented for the next session that hits the same refusal,
   repeating #623's own mid-task rediscovery cost; a documentation fix
   is available now and does not require the harness change.
3. **Document the two verified low-friction workarounds as rulebook
   guidance** (chosen): add a short pattern note — when a Bash command
   refuses with `cannot be statically analyzed` / `simple_expansion` /
   `expansion obfuscation`, it is harness layer 2, not a repo gate;
   prefer `Write` the script to a file then `bash`/`python3 <file>`, or
   avoid heredocs containing literal JSON braces (`python3 -c
   '...'` with single quotes instead) — verified working, this
   session's reproduction. This is the only candidate actionable on our
   own surface without touching anything we don't own.
4. **Weaken the repo's own `contract-guard.sh` or a sibling gate** to
   pre-empt the harness refusal — rejected outright per operator
   principle 5 (never weaken our own gates in response to a
   harness-boundary refusal) and per this survey's own finding that our
   gates were never the refusing surface to begin with.

Chosen: candidate 3, combined with candidate 2's existing routing (both
are non-exclusive — the guidance ships now, the #476 remediation issue
remains the eventual harness-side fix).

## What will be done

1. Classification table (below) recording each #623-cited refusal
   shape, its reproduced exact text, root-cause layer, and
   fixable-on-our-surface vs harness-boundary-to-document verdict.
2. A guidance note (fixable-on-our-surface item) added to a handbook
   documenting the two verified workarounds, so future sessions do not
   re-discover them mid-task.
3. `docs/issue-637/reports/technical-feasibility.md` — this role's
   record, phase-gated per contract v3 s19, written on approval
   (phase 2).

## Classification table

| # | Blocked shape (this session's reproduction) | Exact refusal text | Root-cause layer | Classification | Verified low-friction path |
|---|---|---|---|---|---|
| 1 | `for h in a b c; do echo "$h"; done` (any form expanding the loop's own variable, quoted or not, single- or multi-line) | `Contains simple_expansion` | harness layer 2 (command-approval), per spawn.py:2238-2242's `_HARNESS_REFUSAL_PATTERNS` and its provenance comment at spawn.py:2231-2236 — not a match anywhere under `on-the-record/hooks/` or `gates/` | harness-boundary-to-document (analyzer is outside this repo's surface); **also** fixable-on-our-surface as a documented workaround (item 2 below) | `Write` the loop to a file, then `bash <file>` — verified this session (`val=a`/`val=b`/`val=c` printed, no refusal) |
| 2 | `python3 - <<'PYEOF' ... json.dumps({"tool_input": {...}}) ... PYEOF` (heredoc containing literal `{`/`}` with quotes inside) | `Contains brace with quote character (expansion obfuscation)` | harness layer 2, same pattern set/provenance as row 1 | harness-boundary-to-document; **also** fixable-on-our-surface as a documented workaround (item 2 below) | `python3 -c '<script, single-quoted, no heredoc>'` — verified this session (JSON printed, no refusal) |

## What is out of scope

- Patching or configuring the harness's own command-approval analyzer —
  not this repo's surface (candidate 1, rejected above).
- Any change to `on-the-record/hooks/` or `gates/` — neither refused
  command reached or was caused by our own gates; changing them would
  not fix anything and risks weakening a gate for no reason (operator
  principle 5).
- Re-litigating #476's `false_reject` remediation — #623's record
  already opened that action item; this proposal only adds the
  documentation fix available without waiting on it.

## How we'll know it worked

Both blocked-command shapes, re-run through a fresh session using the
documented workaround pattern, complete without refusal — reproduced
and confirmed in this same session (survey.md, "Reproduction, this
session", items 3-4). The classification table above is the
step-1 acceptance artifact named by issue #637's Acceptance section.

## Evidence format

Every claim above cites `docs/issue-637/reports/technical-feasibility/survey.md`
(this session's reproduction transcript), `spawn.py:<line>` (source),
or issue #623's/#232's own committed records, per the citation format
`<claim> — <source: URL | path:line | check-name score>`.
