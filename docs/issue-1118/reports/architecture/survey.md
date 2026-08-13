---
code_under_review:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - on-the-record/hooks/test_deliverable_guard.py
type: survey
loop_state: phase-1
---

Subject: issue-1118

## What was done

canonical: read on-the-record/hooks/deliverable-guard.sh and
on-the-record/hooks/product-capture-stopgate.sh in full, and
`git log --oneline -- on-the-record/hooks/deliverable-guard.sh
on-the-record/hooks/product-capture-stopgate.sh` (executed this session).

Current-state survey for issue #1118, three sub-defects claimed by the
issue.

### 1. The guard/stopgate contradiction is already resolved on this branch

Issue #1118's own text describes deliverable-guard.sh as exempting
"only approvers.md, scratch/tmp, .git/plugin-cache". canonical:
on-the-record/hooks/deliverable-guard.sh:99-111 (read this session) —
that is no longer true. `git log --oneline` (executed this session)
shows commit 57acada ("issue-1111 phase-2: resolve product-capture/
deliverable-guard deadlock (#1114)") already on this branch, predating
issue-1118/architecture's branch point at a2da1e9. Reading
deliverable-guard.sh:99-111 today shows an `EXEMPT_SUFFIXES` tuple
covering `docs/reports/product/{requirements,priorities,philosophy,
goals}.md` plus a `PRODUCT_CAPTURE_ISSUE_RE` regex covering
`docs/issue-<n>/reports/product/<cat>.md` — exactly the two write-path
shapes product-capture-stopgate.sh:172-175 targets.

canonical: docs/issue-1111/reports/implementation.md (read this
session) records this exemption as landed in commit 73475d0, with
three new test_deliverable_guard.py cases for it.

canonical: python3 on-the-record/hooks/test_deliverable_guard.py -q (executed live this session) — result: 19 passed
```
...................                                                      [100%]
19 passed in 0.60s
```

Requirement (a) of #1118 ("deliverable-guard exempts the stopgate's
exact capture paths") is therefore already satisfied end-to-end — its
own body was written before #1111 landed (#1118's "Prior evidence"
section cites 2026-08-12 consult attempts predating #1111's 2026-08-13
landing per that commit's timestamp in the log above).

### 2. False-positive: injected directive/hook text scanned as user-authored

canonical: on-the-record/hooks/product-capture-stopgate.sh:144-152
(read this session) — the transcript walk matches every entry with
`type=="user"` and a plain-string or text-block `content`, with no
distinction between an actual user turn and a `UserPromptSubmit` hook's
injected `<system-reminder>`/directive block, which the harness also
delivers as a `type:"user"` entry.

canonical: this conversation's own `<user-prompt-submit-hook>` /
`<system-reminder>` tags (visible earlier in this session's transcript)
— the harness injects these as type:"user" entries too. The issue's own
triggering example, "우선순위는 아래 순서대로 —", is directive text
from the orchestrate skill's own priority-ordering block, not something
the user typed.

derived: grep -rn "system-reminder\|user-prompt-submit-hook\|<command-name>" on-the-record/hooks/*.sh on-the-record/*.py
```
(no output — no existing hook or script in this repo distinguishes
injected-tag text from user-typed text)
```

This hook is therefore the first in the repo needing that distinction.

### 3. No dedup for undischargeable flags across Stops

canonical: on-the-record/hooks/product-capture-stopgate.sh:183-199
(read this session) — the hook has no state file and no memory across
invocations: every Stop re-walks the full transcript from scratch and
re-flags a category whenever its `git diff`/`git log -1 -p` check still
shows zero added lines for that category's doc path. Nothing records
"this category was already surfaced and the orchestrator chose not to
(or could not) discharge it", so an undischargeable flag reproduces on
every subsequent Stop unchanged — matching the issue's reported "~10
consecutive Stop re-fires".

canonical: on-the-record/hooks/retry-loop-bound.sh:57-58,90 (read this
session) — sibling hooks already solve an analogous "remember something
across Stops for this session" problem: a JSON state file keyed by
session_id under `${OTR_<NAME>_STATE_DIR:-${TMPDIR:-/tmp}/otr-<name>}/
<safe_session_id>.json`, with an env-var override for test injection. No
existing hook needs per-category dedup within one state file, but the
state-dir/session-key shape is directly reusable.

## Why

Scoping the actual remaining work correctly matters: two of #1118's
three named defects (the contradiction and its Generator framing) are
already discharged by #1111's landed fix (commit 73475d0, per the
canonical citations above), and re-doing that work would be wasted
effort scored against a stale issue body. The remaining two
(false-positive scan, dedup) are real and unaddressed in the current
code, per the file:line citations above.

## Upstream / basis

- on-the-record/hooks/product-capture-stopgate.sh (current state, read in full)
- on-the-record/hooks/deliverable-guard.sh (current state, read in full)
- docs/issue-1111/reports/implementation.md (landed resolution of the guard/stopgate contradiction)
- on-the-record/hooks/retry-loop-bound.sh:57-58,90 (session-keyed state-file pattern to reuse for dedup)
- issue #1118 body (gh issue view 1118, read this session)

## Open findings

- The issue's acceptance criterion (a), "the capture write path chosen in
  the resolution is actually permitted end-to-end", is already true per
  the canonical citations above; the new
  gates/test_product_capture_vs_deliverable_guard.py the issue asks for
  should assert this as a regression guard composing the two real hooks
  together (not just re-asserting deliverable-guard.sh in isolation, which
  test_deliverable_guard.py already does).
- resolution path: the phase-1 proposal (docs/issue-1118/proposals/) picks
  concrete tag names for the injected-text exclusion and a concrete dedup
  key/TTL; phase-2 implements both plus the new composed test file, gated
  on approval per contract v3 s19.

next steps: open a phase-2 build once a docs/specs/approvers.md account
posts `APPROVE issue-1118/architecture` (single-account mode) or an
approvers.md reviewer submits a PR review Approve (two-account mode) on
the phase-1 PR.

resolution path: same as above — phase-2 build on approval.
