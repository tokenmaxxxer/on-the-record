# Implementation proposal — issue-597: framing-snapshot comments at flow transitions

files:
  - on-the-record/hooks/delegated-judgment-gate.sh
  - on-the-record/hooks/test_delegated_judgment_gate.py

## Request

Extend `delegated-judgment-gate.sh` with a sixth firing condition that
posts a four-element framing snapshot (resolved problem / prior cost /
newly possible / still broken) as an issue comment at three flow
transitions — delivery PR merged, issue reopened, issue closed —
synthesized only from cited, mechanically-resolvable records (reusing
`record-claim-guard.sh`'s path-resolvability check, ported inline), with
an explicit stated baseline when no prior records exist. Tests cover all
three transitions.

## Constraints

- Per architecture.md section 1: extend the existing
  `delegated-judgment-gate.sh` writer; no new hook, no new transport.
- Per architecture.md section 3-4: every element's sentence is assembled
  from cited record text, never freely composed; every `Citation:` line
  must resolve (existing path, or a 7-40 char hex commit sha) before the
  comment posts — a citation that doesn't resolve fails the comment
  closed (does not post), not open.
- Per architecture.md section 5: a transition with no prior
  role/decision records states the baseline explicitly per element,
  citing the issue itself, not a fabricated record path.
- Zero-install: no `gates`-package import, no on-the-record checkout
  resolution (matches this file's existing header constraint) — the
  citation-resolvability check is a ported-inline function, the same
  pattern the impact axis already uses for `risk_report.py`'s logic.
- `docs/issue-573/proposals/implementation.md`'s component boundary
  applies here too: no change to `spawn.py`, `impact-guard.sh`, or
  `gates/risk_report.py` — all read-only or out-of-scope dependencies.

## Rationale

**Delivery-merged detection**: architecture.md's trigger table (row 1)
says this transition reuses `spawn.py`'s watch/session-end signal. The
survey found that signal does not exist in a merge-distinguishable form —
`_post_session_end_comment()` posts `"PR #<n> opened"` for both open and
merged states, with no separate merge marker. Building on it would mean
adding merge-detection logic to `spawn.py` (a 3900+ line file, the
highest reversibility-impact tier this hook's own axis table assigns to
contract-root files) — out of this component's boundary, and out of
proportion to a docs-comment feature.

Rejected alternative: extend `spawn.py`'s `_post_session_end_comment()`
(or a sibling) to detect and mark PR-merge specifically, matching
architecture.md's literal row-1 text. Rejected because it widens the
write set to a file explicitly out of scope for every hook in this
family, for a signal architecture.md itself concedes ("reuses ... a
`session-end`/merge-watching mechanism already used elsewhere") is
aspirational rather than already built (confirmed: issue-573 scoped the
same wiring out of its own delivery, and it was never added since).

Chosen instead: detect `gh pr merge` as a `Bash` command via the same
`PreToolUse` vantage point this hook already uses for `gh pr create` and
will use for `gh issue reopen`/`gh issue close`. This matches
architecture.md's own general detection-mechanism sentence ("by
pattern-matching the `gh` command about to run, at the same `PreToolUse`
point") more faithfully than the row-1 cell does, keeps the entire write
set inside `on-the-record/hooks/`, and needs no new detection channel —
the hook already fires on every outgoing `Bash` command. A merge command
running from *any* session on the delivery branch is the trigger; the
hook does not need to distinguish which session issued it, matching how
`gh pr create` detection already works today (any session's `gh pr
create` on an `issue-<n>/<role>` branch fires the existing "Judgment
opened" event, regardless of which session runs it).

**Citation-resolvability, inline port vs. `gates` import**:
`record-claim-guard.sh` already has this exact check
(`orphaned_path_reference_check`) but reaches it via `sys.path.insert` +
`import record_lint` from the `gates/` directory. `delegated-judgment-gate.sh`'s
own header explicitly rejects that pattern for zero-install reasons.

Rejected alternative: import `record_lint` the same way
`record-claim-guard.sh` does, accepting a zero-install regression for
this one hook. Rejected because it breaks a constraint this exact file
states for itself in its own header, and because the impact axis already
demonstrates the inline-port pattern works for logic of comparable size
(a ~30-line function) — no new precedent needed, just following the one
already set in the same file.

## Accumulation

This adds three more `_gh()`-calling dispatch arms to a script that
already has five (the `gh pr create` panel-synthesis path). If N more
transitions are added later the same way, `delegated-judgment-gate.sh`'s
Python payload grows linearly in dispatch arms but not in shared-helper
count — `_gh()`, `resolve_citation()`, and `gather_citable_records()`
are already the shared helpers every new transition arm reuses rather
than re-implementing its own `subprocess.run(["gh", ...])` call, so N
more transitions add N more `re.search` + `build_framing_snapshot()`
call sites, not N more copies of the posting/citation logic. If this
pattern grows past roughly ten dispatch arms total, the dispatch table
itself (currently an implicit `if`/`re.search` chain) should become an
explicit `TRANSITION_PATTERNS` list of `(regex, transition_label,
issue_extractor)` tuples processed in one loop — flagged here, not built
now, since five existing arms plus three new ones (eight total) is still
below that threshold.

## What will be done

1. Add three new `re.search` dispatch checks ahead of/alongside the
   existing `gh pr create` check in the embedded Python payload: `gh pr
   merge` (delivery-merged, only fires on branches matching
   `issue-<n>/<role>` the same way `gh pr create` detection does), `gh
   issue reopen <n>`, `gh issue close <n>` — each producing a
   `transition` label (`delivery-merged` / `issue-reopened` /
   `issue-closed`) and the target `issue` number parsed from the
   command's own `<n>` argument (reopen/close) or from
   `git rev-parse --abbrev-ref HEAD` (merge, same branch-parse the
   existing code already does).
2. Add `resolve_citation(target, value)`: a ported-inline function
   (same convention as `reversibility_of`) taking the `TARGET` repo root
   and a citation value; returns `True` if `(TARGET / value).exists()`
   or if `value` matches a 7-40 char hex string; `False` otherwise. No
   `gates` import.
3. Add `gather_citable_records(target, issue)`: lists
   `docs/issue-<issue>/reports/*.md` (role records),
   `docs/issue-<issue>/decisions/*.md` (audit/remediation records the
   gate itself already writes), and fetches the issue body via `gh
   issue view <issue> --json body,title` (best-effort — falls back to
   "issue body unavailable" text on `gh` failure, never blocks the
   framing post itself, matching the existing fail-open `_gh()`
   posture for posting, though the citation-resolvability check itself
   still fails the *comment* closed per architecture.md section 4 if a
   picked citation doesn't resolve).
4. Add `build_framing_snapshot(target, issue, transition, pr_ref)`: for
   each of the four elements, picks a sentence source in priority order
   — a `decision:`/`status:` field from the most recent
   `docs/issue-<issue>/decisions/*.md` record for "resolved
   problem"/"still broken", the role record's own prose (matched via a
   `## What was done`/`## Rationale`-style heading scan reusing the
   existing record vocabulary this plugin's role records already use)
   for "prior cost"/"newly possible" — and if no record exists at all
   for the issue (`gather_citable_records` returns nothing beyond the
   issue body), emits the section-5 baseline sentence per element,
   citing the issue number as `<issue-#> (no prior record; issue body
   is the baseline)`. Every emitted `Citation:` line is checked through
   `resolve_citation()` before the function returns; if any fails, the
   whole framing post is skipped (fail-closed, matching
   architecture.md section 4 exactly — "if a citation path does not
   exist ... the gate fails closed and does not post").
5. Wire the three new dispatch arms to call
   `build_framing_snapshot()` and post via `_gh()` with the exact
   `## Framing snapshot — <transition label> (<issue-#> / <PR-# if
   applicable>)` header format from architecture.md section 3, using
   `gh issue comment <issue> --body-file -` (stdin, matching how other
   multi-line bodies in this file are already posted, avoiding
   shell-escaping the four-section body through `--body`).
6. Extend `on-the-record/hooks/test_delegated_judgment_gate.py` with one
   test per transition (`gh pr merge`, `gh issue reopen`, `gh issue
   close`) plus one for the section-5 baseline (no prior
   decisions/reports for the fixture issue) and one for the section-4
   fail-closed path (a synthetic unresolvable citation), using the
   same `_init_target()`/`_stub_gh()` fixture pattern the existing tests
   already use.
7. Run the extended test file once and fix what breaks before the PR,
   per the no-mock directive's single confirmation run.

## Out of scope

- Rewiring `spawn.py`'s session-end mechanism for merge-specific
  detection — superseded by the `gh pr merge` detection chosen above
  (see Rationale); this proposal does not touch `spawn.py`.
- The "Remediation PR merged" section-12 event architecture.md's table
  lists as a separate row — not part of #597's three named transitions;
  left exactly as-is (unimplemented, per issue-573's own scoping).
- Assigning `judgment_axes` to additional roles, widening the depth-axis
  matcher, or any other change to the existing five firing conditions —
  untouched by this proposal.
- Any change to `record-claim-guard.sh` itself — the inline port is a
  new, separate function in `delegated-judgment-gate.sh`, not a
  refactor of the existing hook.
- Step 3 (conformance-review) named in the issue's 실행 계획 — the
  orchestrator reopens the issue for that step once this delivery PR
  merges.

## How you'll know it worked

- The extended `test_delegated_judgment_gate.py` passes locally
  (`python3 on-the-record/hooks/test_delegated_judgment_gate.py`),
  covering: a framing snapshot posts on `gh pr merge` matching an
  `issue-<n>/<role>` branch; on `gh issue reopen <n>`; on `gh issue
  close <n>`; each with all four labeled sections and a resolvable
  `Citation:` line per section; the baseline case states "no prior
  record" explicitly per empty element when the fixture issue has no
  `docs/issue-<n>/reports/*.md` or `docs/issue-<n>/decisions/*.md`
  files; a fixture with a deliberately unresolvable citation source
  results in NO comment being posted (fail-closed verified by
  asserting the stubbed `gh` log has no matching invocation).
- No `import gates` or `sys.path` addition targeting the checkout
  appears anywhere in the diff (grep check, matching the existing
  "How you'll know it worked" bar from issue-573's implementation
  proposal).
- `hooks.json` is unchanged — the new dispatch arms live inside the
  already-registered script, confirmed by `git diff --stat` showing no
  edit to `on-the-record/hooks/hooks.json`.

## What did not work
(none yet — phase 1, no build attempted)

## loop_state
kind: proposal
loop_state: scope-proposed

## Open findings
None at phase 1. The exact heading-scan pattern for pulling
"prior cost"/"newly possible" prose out of a role record's free text
(step 4) may need one iteration against a real record during the build —
flagged for build-time discovery, not resolved here, since it depends on
reading actual role-record content the survey did not exhaustively
catalogue.

## Next steps
Await approval (`APPROVE issue-597/implementation` per contract v3 s19,
single-account mode). On approval: implement steps 1-7 above in
`delegated-judgment-gate.sh` and its test file, run the tests once, open
the delivery PR with `Closes #597` (step 3 conformance-review remains;
the orchestrator reopens the issue for it).

## Resolution path
The one open finding above resolves by reading 1-2 real
`docs/issue-<n>/reports/<role>.md` files during the build and adjusting
the heading-scan pattern to their actual prose shape before finalizing
`build_framing_snapshot()`.
