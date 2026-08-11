files:
  - on-the-record/hooks/record-tiering-directive.sh
  - on-the-record/hooks/record-tiering-guard.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_record_tiering_directive.py
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
  - docs/issue-760/reports/implementation.md

## Request

Issue #760 asks to implement `docs/issue-745/proposals/product-discovery.md`
Item 2 candidate 1 (citation-informed section tiering): sections whose
cross-issue citation is actually measured (verdicts, RICE tables,
root-cause findings) stay in their current form; named boilerplate
sections with a zero-citation track record default to a one-line terse
form unless the author has real content for them. The pre-registered
metric package (`boilerplate_output_token_share`, 30% threshold,
`cross_issue_citation_rate` guardrail at 5 points per named category,
independently revertible per category) is copied verbatim from the
issue body and must not change. Two judgment calls are left open by
the issue: where to implement the tiering, and which sections qualify
for the "named low-citation set." Both are resolved in this proposal
from `docs/issue-745/reports/product-discovery/current-state.md`'s
actual measurements, not from preference.

## Constraints

- The pre-registered metric, threshold, guardrail, and decision rule
  are copied verbatim from the issue body — no wording or numeric
  change.
- Only the section(s) `current-state.md` actually measured at zero
  citation are in scope for tiering — not a broader guess.
- No removal of any section a gate already requires to exist (the
  issue's own "범위 밖" — this changes a section's *default content*
  when empty, not whether the heading exists).
- This session's write set stays inside `on-the-record` (this repo) —
  `record-shape-gate.sh`/`record-shape-directive.sh`, which mandate
  `## What did not work`'s presence, ship from a separate plugin repo
  (`tokenmaxxxer/implementation-rulebook`) outside this branch.
- Any new `on-the-record/hooks/*.sh` file needs matching rows in
  `docs/specs/enforcement-boundary.md` and `docs/specs/generated-paths.md`
  in the same commit (`gate-registration-guard.sh`, confirmed in the
  survey).
- Phase-1 only in this PR: this document and the survey it is built on
  are the only writes this session makes; no code lands until a human
  approver approves phase 2 (contract v3 s19).

## Rationale

**Revised after the after-proposal hunt finding
(`docs/issue-760/reports/implementation/hunt-2026-08-11-citation-informed-section-tiering.md`):
a directive-only design was the first draft here and is rejected.** The
hunt found that a directive-only norm for this *exact* section already
exists today — `runs/rulebooks/tokenmaxxxer-implementation/record-shape/hooks/directive.sh`
(the injected, always-on directive from the separate
`implementation-rulebook` plugin) already states "present even when
empty means... explicit content such as `None.`" — and that this
existing directive is already silently unfollowed with zero mechanical
consequence: this proposal's own survey sample contains two live
records (`docs/issue-759/reports/implementation.md`,
`docs/issue-674/reports/implementation.md`) that ignore it, writing
146–180 char explanatory paragraphs instead. `record-shape-gate.sh`,
the only gate touching this section, checks heading *presence*
(`has_wdnw`) only — it has no body-content check, so a padded "None —
because..." body cannot fail it. Stacking a second, near-identical
directive-only layer on the same section is not new evidence-free
speculation about whether directive-only works here; the first layer's
failure is already recorded in this proposal's own data. A directive
alone is rejected on that concrete basis.

**Chosen: a `UserPromptSubmit` directive paired with a narrowly-scoped
`PreToolUse` gate — matching #730's actual structure (directive +
gate, not directive alone) more closely than the rejected first draft
did.** The gate is not a blanket length cap: it fires *only* on the
self-declared-empty branch, not on section content in general. It
parses the `## What did not work` body; if the trimmed body starts
with "none" (case-insensitive — the author's own signal that nothing
failed), the gate requires the body to be the bare marker
(`None.`/`None`, no trailing explanation) and denies otherwise. If the
body does not start with "none," the gate does not touch it at all —
a real failure narrative of any length passes untouched, exactly as
`docs/issue-659/reports/implementation.md`'s 1665-char entry should.
This sidesteps the reason "blanket record-length cap" was rejected in
`product-discovery.md`'s Item 2 RICE table (candidate 2: "can't
distinguish a terse-but-load-bearing RICE table from terse
boilerplate") — that candidate applied one length rule across
*different kinds* of content with no author-supplied signal to key
off; this gate applies no length rule to content at all, only a
shape rule to the one branch the author has already self-classified as
"nothing to report" by writing "None" first. A real, load-bearing
entry is never in this gate's scope regardless of length, so it cannot
reproduce the undifferentiated cut the rejected candidate would have
caused.

**Rejected alternative: implement via a record scaffold/template
file.** No such file exists in this repo — checked directly (`find .
-iname "*template*"` under `docs/` returns only an unrelated role-spec
JSON schema, `docs/specs/role-spec-template.schema.json`). Role records
are freeform markdown authored directly by role sessions, shaped only
by injected directive text plus gates; there is no scaffold file this
repo could edit to change a section's default content. This option is
not available, not merely disfavored.

**Rejected alternative: a mechanical gate enforcing brevity via a
length threshold on the "empty" case.** Rejected for the reason
above — it collapses into the already-rejected blanket-length-cap
shape, just scoped to one section instead of the whole record. A
subtler heuristic (e.g. "flag if body lacks bullet points and exceeds
N chars") was considered and rejected too: it still can't reliably
tell a terse-but-real one-paragraph explanation from padding, and a
false positive would block a legitimate short explanation — the exact
harm a length-shaped check causes regardless of where the threshold is
drawn.

**Rejected alternative: widen the low-citation section set now to
include `current-state`/`scout-brief`-equivalent scratch content "once
consumed," per the pre-registered metric's own second clause.**
Rejected for this proposal because `current-state.md` provides no
zero-citation evidence for that content — its actual citation rates
for `survey.md` (56.1%) and `scout-brief*.md` (62.3%) are well above
zero, and neither category is covered by the five named guardrail
categories, so tiering them now would risk cutting content the data
shows is still read, with no guardrail positioned to catch the harm.
The metric text names this clause and this proposal leaves it
unchanged, but defers acting on it to the metric's own pivot rule
("widen using the next citation-rate measurement round") once
section-level evidence exists.

## What will be done

- `on-the-record/hooks/record-tiering-directive.sh`: a new
  `UserPromptSubmit` hook, following `record-claim-shape-directive.sh`'s
  own conventions exactly (role-session-only via `CLAUDE_ROLE`, fails
  open on any resolution gap, `ORCHESTRATE_OFF` kill switch, wrapped in
  the same fail-closed-only-on-genuine-error trap style). States: when
  writing `docs/issue-<n>/reports/implementation.md`'s `## What did not
  work` section and nothing was actually undone/replaced and no
  expectation actually failed during the build, write the section body
  as the bare marker `None.` — no restated summary of what did go to
  plan — and that `record-tiering-guard.sh` enforces this mechanically,
  not just as a norm. Elaborate only when there is a real entry
  (something written then undone, or an expectation that did not
  hold).
- `on-the-record/hooks/record-tiering-guard.sh`: a new `PreToolUse`
  hook on `Write|Edit|MultiEdit`, scoped to
  `docs/issue-*/reports/implementation.md` (same path-scoping approach
  as `record-claim-guard.sh`). Extracts the write's `## What did not
  work` section body from its content fragment; if the trimmed body
  starts with "none" (case-insensitive) and the body is not itself
  just the bare marker (`None.`/`None`, optionally with trailing
  whitespace — no other characters), denies with a message pointing at
  the accepted form. A body that does not start with "none" is never
  inspected further — real content of any length always passes. Fails
  closed on a genuine resolution error, same trap style as
  `record-claim-guard.sh`; `ORCHESTRATE_OFF` kill switch.
- `on-the-record/hooks/hooks.json`: register both new hooks — the
  directive under `UserPromptSubmit` (alongside `directive.sh` and
  `record-claim-shape-directive.sh`), the guard under the existing
  `PreToolUse`/`Write|Edit|MultiEdit` matcher block (alongside
  `record-claim-guard.sh`).
- `on-the-record/hooks/test_record_tiering_directive.py`: tests for
  both new hooks — the directive's rendered text states the
  bare-marker rule and names the real-content exception, is silent
  without `CLAUDE_ROLE`, and fails open under a missing-dependency or
  misconfigured-`ORCHESTRATE_OFF` condition (mirroring
  `test_record_claim_guard.py`); the guard denies a padded "none..."
  body, allows a bare `None.` body, and allows any non-"none"-prefixed
  body regardless of length (the case that must never be denied,
  directly closing the gap the hunt finding raised).
- `docs/specs/enforcement-boundary.md`: new rows for both
  `record-tiering-directive.sh` and `record-tiering-guard.sh` under
  `on-the-record/hooks/*.sh`, verdict `contract` for both, reason text
  mirroring `record-claim-shape-directive.sh`'s/`record-claim-guard.sh`'s
  own row shapes.
- `docs/specs/generated-paths.md`: new rows for both files, `n/a`,
  "reads/validates only, no write call" — matching
  `record-claim-shape-directive.sh`'s/`record-claim-guard.sh`'s own
  rows.
- `docs/issue-760/reports/implementation.md`: the phase-2 record for
  this same work, written per the record-shape contract, including the
  pre-tiering baseline this proposal's survey already establishes
  (`boilerplate_output_token_share` ≈ 0.33% by the survey's git-log
  proxy method), and an explicit `## Next steps` naming who/when the
  official post-tiering 20-record re-measurement runs (the hunt
  finding's second point — the proposal draft it reviewed named no
  owner or trigger for this): the next `product-discovery`-role session
  that revisits `#745`'s tracked items, or any session opening a
  follow-up issue against this one, re-derives
  `boilerplate_output_token_share` with `current-state.md`'s own
  ledger-log method once 20 `docs/issue-<n>/reports/implementation.md`
  records exist with a commit date after this proposal's landing
  commit.

## Out of scope

- Any *length-based* mechanical check — `record-tiering-guard.sh`'s
  check is a content-shape rule on the self-declared-empty branch
  only, never a length threshold applied to section content in
  general (see Rationale for why this distinction matters).
- Widening the tiered section set to `survey.md`/`scout-brief.md`
  scratch content (rejected above; deferred to a future citation
  round).
- Any change to `record-shape-gate.sh`/`record-shape-directive.sh` or
  any other file in `tokenmaxxxer/implementation-rulebook` — out of
  this session's branch and repo entirely.
- The other two deferred #745 items (thinking budget, `execution-observation`
  frequency) — the operator explicitly deferred these; issue #760
  covers Item 2 only.
- Removing any gate-required section's heading — this proposal changes
  a section's default *content* when empty, never whether the heading
  exists.

## How you'll know it worked

Mechanism-level (phase-2's own build check): `test_record_tiering_directive.py`
passes, specifically the three guard cases named above — denies a
padded "none..." body, allows a bare `None.` body, never denies a
non-"none"-prefixed body regardless of length. This is the immediate,
executable answer to the hunt finding's concern that the mechanism
would be unenforced the same way the pre-existing directive already
is.

Outcome-level, per the issue's own pre-registered Acceptance, unchanged:

- `boilerplate_output_token_share` measured over the next 20
  `docs/issue-<n>/reports/implementation.md` records written after the
  directive ships, using `## What did not work` (empty case only) as
  the section set, falls by at least 30% relative to the pre-tiering
  baseline (same measurement, same section set, most recent 20 records
  before the format change ships — this survey's git-log-proxy figure,
  ≈0.33%, is the placeholder baseline; the official comparison should
  re-derive both windows with `current-state.md`'s own ledger-log
  method for methodological consistency).
- empty state: if fewer than 20 post-tiering records exist yet at
  measurement time, record that fact plus the values measured so far
  and leave the window open — do not force a verdict early.
- `cross_issue_citation_rate` for `proposals/*.md`, `reports/<role>.md`,
  and repo-wide `docs/reports/*.md` re-measured and stated next to the
  primary metric, each checked against `current-state.md`'s own
  established baseline (93.8%, 64.1%, 65.8% respectively) with a
  5-point tolerance, independently revertible per category on breach.
- empty state: if no new records have been written yet, record only
  the baselines and hold the verdict.
