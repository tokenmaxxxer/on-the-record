---
status: proposed
files:
  - on-the-record/hooks/product-capture-stopgate.sh
  - gates/test_product_capture_vs_deliverable_guard.py
  - docs/issue-1118/decisions/generator-choice.md
---

## Intent

Issue #1118 names three defects across product-capture-stopgate.sh
(#566/#956) and deliverable-guard.sh (#787): a write-path contradiction
between the two hooks, a false-positive in the stopgate's transcript
scan (injected directive text read as user-authored), and unbounded
re-firing of an undischargeable flag on every Stop. This proposal
covers all three, but the first is already closed on this branch (see
docs/issue-1118/reports/architecture/survey.md) — it fixes only the
remaining two, in the one generator (the hook pair, not a single
instance), and adds the acceptance test the issue names.

## Constraints

- No product-facing behavior change to the stopgate's advisory-only
  contract: it must still never emit `decision:"block"` (survey cites
  product-capture-stopgate.sh header comment, architecture's own #566
  design).
- The dedup mechanism must reuse the existing session-keyed state-file
  shape (retry-loop-bound.sh pattern, see survey) rather than invent a
  new persistence convention.
- Bootstrap-on-first-flag (creating the empty docs/.../<cat>.md with its
  header) must keep working even with no docs/product/ directory present
  — acceptance scenario named by the issue.
- Both fixes stay inside product-capture-stopgate.sh; deliverable-guard.sh
  is untouched (its own #1118-named defect is already resolved).

## What will be done

### ## Generator

This removes the generator — the hook pair's shared failure mode of
"stopgate demands an action the current state cannot safely evaluate or
never lets go of" — not one instance of it. Sub-defect 1 (guard/stopgate
path contradiction) was one instance, already fixed by #1111's write-path
alignment. Sub-defects 2 (false-positive) and 3 (unbounded re-fire) are
the other two instances of the same generator class: the stopgate
computing its flag from a mis-scoped signal (untrusted transcript text)
and never bounding how long an unresolved flag persists. Both fixes below
close the generator at the stopgate's transcript-walk and flag-emission
points, not by special-casing #1118's own trigger phrase.

Record: docs/issue-1118/decisions/generator-choice.md — one-paragraph ADR
capturing this framing (context: hook-pair contradiction reports recur
under different trigger phrases; decision: fix at the two generator
points, not the instance; consequences: future trigger phrases in
injected text or future undischargeable categories are covered without a
new patch; alternatives considered: patching only the reported phrase —
rejected, reproduces per #1118's own note that the same class was lost
twice before on 2026-08-12).

### Fix 2 — exclude injected directive/hook text from the transcript scan

product-capture-stopgate.sh's CHECK python body (stopgate.sh:118-129,
`flat_text`) will strip any text block that is wrapped by one of a
closed set of harness/hook-injected wrapper tags before running the
category regexes over it. Concretely: after extracting `text` from a
`type:"user"` entry, before sentence-splitting, drop any substring
matched by `<system-reminder>...</system-reminder>` and
`<user-prompt-submit-hook>...</user-prompt-submit-hook>` (both observed
this session as the harness's own injection wrappers — see survey
sub-defect 2), then run the existing CATEGORIES regexes only against
what remains. If stripping empties a sentence, it is skipped exactly
like today's empty-sentence guard already does (stopgate.sh:155-156). No
change to CATEGORIES, no change to the git-diff cross-check, no change to
the output shape.

### Fix 3 — dedup undischargeable flags across consecutive Stops

Add a session-keyed state file, reusing the retry-loop-bound.sh shape
(survey citation: retry-loop-bound.sh:57-58,90):
`${OTR_PRODUCT_CAPTURE_STATE_DIR:-${TMPDIR:-/tmp}/otr-product-capture}/
<safe_session_id>.json`, holding `{"flagged": {"<cat>": "<excerpt-hash>"}}`.
Before emitting `unrecorded` in the final additionalContext block
(stopgate.sh:201-220), the hook compares each `(cat, excerpt)` pair
against the state file: if the same category was already flagged with
the same excerpt hash on this session's immediately preceding recorded
Stop, suppress it from `parts` this time (dedup, not silence-forever —
a category that gets its doc write and later regresses can re-flag).
After computing `unrecorded`, the hook writes the new `flagged` map back
to the state file. If suppressing every category empties `parts`, the
hook exits 0 with no output, same as the existing empty-`unrecorded`
path (stopgate.sh:201-202). session_id is read from the same Stop
payload (`e.get("session_id")`) the role-bind snapshot lookup elsewhere
in this repo already relies on.

### Acceptance test

New gates/test_product_capture_vs_deliverable_guard.py, composing both
real hook scripts (subprocess, same pattern test_product_capture_stopgate.py
already uses) rather than re-testing either hook in isolation:
(a) an orchestrator-session capture write to both
`docs/reports/product/<cat>.md` and `docs/issue-<n>/reports/product/<cat>.md`
is denied by neither hook's logic — assert deliverable-guard.sh exits 0
for a Write tool_input at those paths (regression guard for the already-
landed #1111 fix, not a re-derivation of it);
(b) a transcript whose only category-matching text sits inside a
`<system-reminder>`/`<user-prompt-submit-hook>` block and nowhere else
does not flag (Fix 2);
(c) two consecutive stopgate invocations against the same session_id and
an unchanged (no new doc lines) transcript produce a flag on the first
call and no flag (or a suppressed one) on the second (Fix 3);
(d) empty-state scenario: a repo with no docs/product/ directory at all
still bootstraps the category file and flags on first sight (regression
guard for #566's existing bootstrap-on-first-flag, unaffected by both
fixes).

## Out of scope

- Redesigning product capture as role work (option (b) from the issue's
  requirements) — not needed, since option (a) is already the landed
  direction per #1111 and the survey.
- Any change to deliverable-guard.sh.
- Any change to the CATEGORIES vocabulary or regex set.
- Persisting dedup state beyond one session (cross-session dedup is not
  asked for by the issue and would need a different key than session_id).

## How you'll know it worked

`python3 gates/test_product_capture_vs_deliverable_guard.py` (or pytest
collection of it) passes all four named scenarios, plus the existing
test_product_capture_stopgate.py and test_deliverable_guard.py suites
stay green (no regression to the already-landed #1111 exemption or the
existing bootstrap/git-diff cross-check behavior).

## What did not work

None.
