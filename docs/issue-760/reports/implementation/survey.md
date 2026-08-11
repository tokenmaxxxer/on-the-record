# Current-state survey — issue #760: citation-informed record section tiering

## Background

Issue #760 asks to implement `docs/issue-745/proposals/product-discovery.md`'s
Item 2 candidate 1 (citation-informed section tiering), the operator's
first pick among #745's three deferred cost-reduction items. The
pre-registered metric/threshold/guardrail package lives verbatim in the
issue body and must not change: primary metric
`boilerplate_output_token_share`, threshold 30% relative reduction,
guardrail `cross_issue_citation_rate` with a 5-point tolerance per
named high-citation category (independently revertible per category).

Two judgment calls are explicitly left to this implementation: (a)
where to implement the tiering (record scaffold, authoring-point
directive, or a gate) and (b) which sections belong in the "named
low-citation set." Both are resolved below from evidence, not
preference.

## Where "write-time enforcement" precedent actually lives

The issue points at `core#195` and `#730` as this repo's precedent for
enforcing at authoring time. Checked both directly:

- `tokenmaxxxer-core#195` (referenced from
  `docs/issue-670/proposals/2026-08-10-acceptance-format-in-directive.md`
  and its survey) added a short ACCEPTANCE FORMAT paragraph to the
  always-injected `[orchestrate]` directive heredoc in
  `on-the-record/hooks/directive.sh`, so `check:`/`empty state:`/
  `provenance:` field-shape is known *before* the issue is drafted, not
  discovered after `gates/acceptance_gate.py` rejects it post-hoc. That
  proposal explicitly kept `acceptance_gate.py`'s post-hoc rejection in
  place as backstop and added **no new gate** — the fix was
  directive-only, because a real mechanical backstop (the gate) already
  existed and the round-trip was purely an authoring-time information
  gap.
- `#730` (`docs/issue-730/proposals/2026-08-11-proactive-claim-citation-shape-directive.md`,
  landed at `docs/issue-730/reports/implementation.md`) added
  `on-the-record/hooks/record-claim-shape-directive.sh`, a
  `UserPromptSubmit` hook that states `record-claim-guard.sh`'s
  citation shape proactively, generated at hook-run time from
  `gates/record_lint.py`'s own check-function docstrings (no
  hand-typed second copy). This too is a directive paired with an
  **already-existing** gate (`record-claim-guard.sh`, from #457) — #730
  did not modify the gate's rule logic, only added the proactive
  statement.

Both precedents share the same shape: state the contract at the
authoring point (an always-injected directive), keep any existing
mechanical backstop unchanged, and generate directive text from the
single source of truth rather than hand-typing a second copy that can
drift. Neither precedent invents a *new* mechanical gate where none
already fits.

`record-shape-gate.sh`/`record-shape-directive.sh` (which already
require `docs/issue-<n>/reports/implementation.md`'s `## What did not
work` heading to be present "even when empty," with explicit content
such as `None.`) are **not** part of this repo's tree — they ship from
a separate plugin repo (`tokenmaxxxer/implementation-rulebook`, per
`.claude-plugin/marketplace.json`), outside this session's branch and
write set. This session's write set is `on-the-record` only, matching
`record-claim-guard.sh`/`record-claim-shape-directive.sh`'s own
precedent of adding a **second, repo-local layer** on top of whatever
the injected role directive already states, rather than editing the
role-directive plugin itself.

## Does a mechanical (gate) backstop already exist for this rule, the way it did for #195/#730?

No. `record-shape-gate.sh` (implementation-rulebook, out of this
session's reach) enforces *presence* of `## What did not work` even
when empty — it does not enforce *brevity*. No gate anywhere in this
repo checks section length or content-vs-padding. `product-discovery.md`
Item 2's own RICE table (candidate 2, "Blanket record-length cap")
was scored and explicitly rejected as a candidate to pre-register,
specifically because "a length cap can't distinguish a terse-but-load-bearing
RICE table from terse boilerplate." Any gate design for #760 that
amounts to a length threshold would reproduce exactly the
undifferentiated-cut failure the pre-registered package already
rejected — this constrains the mechanism choice materially (see
proposal Rationale).

## Which sections current-state.md actually measured at zero citation

`docs/issue-745/reports/product-discovery/current-state.md` §2 performs
one section-level citation measurement, not a general one:

> `derived: grep -c "^## What did not work" across docs/issue-*/reports,
> cross-checked against the citation script's per-file citer list for
> any hit whose citing snippet quotes that section` — 227 occurrences,
> quoted/referenced by zero other files repo-wide.

No other H2 section name is measured at the section level anywhere in
current-state.md. The other numbers current-state.md reports
(`survey.md` 56.1% cited, `scout-brief*.md` 62.3%, `reports/<role>.md`
64.1%, repo-wide `docs/reports/*.md` 65.8%, `current-state*.md` 75.0%,
`proposals/*.md` 93.8%) are **file-level** citation rates, not
section-level, and none of them is zero — they sit well above the "0
인용 이력" bar the issue's Problem section and product-discovery.md's
own metric-set both name for this candidate ("인용 이력이 0인 이름붙은
보일러플레이트 절"). The pre-registered metric's numerator definition
does additionally name "current-state/scout-brief-equivalent scratch
content once a phase's next step has consumed it" as in-scope — but
current-state.md provides no section-level breakdown of *that*
content's citation rate, and the whole-file rates for those categories
(56–75%) directly contradict "citation history of 0." Scoping this
implementation to that second clause now, with no zero-citation
evidence behind it, would risk cutting content current-state.md's own
data shows is still frequently read — the exact harm the guardrail
exists to catch, just not caught by the guardrail because `survey.md`/
`scout-brief.md` aren't in its five named categories.

Conclusion: the only section this repo has actual zero-citation
evidence for is `## What did not work` in `docs/issue-<n>/reports/
implementation.md`. That is the list confirmed for phase 2. The
scratch-content clause stays named in the pre-registered metric text
(unchanged, per the issue's instruction) but is not actioned — flagged
as a follow-up for the metric's own pivot rule ("토큰 감소가 부족하면
저인용 절 집합을 좁게 그린 것이므로 ... 넓혀서 재시도") once a future
citation round produces section-level evidence for it.

## Does the "empty" case in practice already look terse, or padded?

Sampled the 20 most-recently-touched `docs/issue-<n>/reports/<role>.md`
files that still exist on disk (`derived: git log --name-only
--pretty=format:"__COMMIT__ %H %ad" --date=iso-strict`, take each
record path's first/most-recent commit date, sort descending, keep the
top 20 that still resolve on disk):

```
docs/issue-742/reports/implementation.md 2026-08-11T15:42:40+09:00
docs/issue-759/reports/implementation.md 2026-08-11T15:28:45+09:00
docs/issue-743/reports/implementation.md 2026-08-11T15:04:47+09:00
docs/issue-749/reports/conformance-review.md 2026-08-11T14:50:52+09:00
docs/issue-741/reports/implementation.md 2026-08-11T14:23:29+09:00
docs/issue-729/reports/implementation.md 2026-08-11T14:18:52+09:00
docs/issue-731/reports/implementation.md 2026-08-11T13:20:56+09:00
docs/issue-730/reports/implementation.md 2026-08-11T13:20:32+09:00
docs/issue-732/reports/implementation.md 2026-08-11T13:13:08+09:00
docs/issue-726/reports/conformance-review.md 2026-08-11T12:57:29+09:00
docs/issue-719/reports/implementation.md 2026-08-11T12:35:54+09:00
docs/issue-659/reports/execution-observation.md 2026-08-11T12:28:25+09:00
docs/issue-674/reports/implementation.md 2026-08-11T12:16:37+09:00
docs/issue-706/reports/implementation.md 2026-08-11T11:45:52+09:00
docs/issue-711/reports/implementation.md 2026-08-11T11:31:10+09:00
docs/issue-659/reports/implementation.md 2026-08-11T11:25:45+09:00
docs/issue-699/reports/implementation.md 2026-08-11T11:02:45+09:00
docs/issue-698/reports/implementation.md 2026-08-11T10:45:43+09:00
docs/issue-695/reports/implementation.md 2026-08-11T10:04:09+09:00
docs/issue-692/reports/implementation.md 2026-08-11T09:26:29+09:00
```

Of these 20, 3 (both `conformance-review.md` samples and the
`execution-observation.md` sample) carry no `## What did not work`
heading at all — that heading is mandated only for
`docs/issue-<n>/reports/implementation.md`, per the injected
`record-shape-directive` text this very session already carries
("every phase-2 record (`docs/issue-<n>/reports/implementation.md`)
carries ... a `## What did not work` heading present even when
empty"). Of the remaining `implementation.md` records, classifying
each section body as empty (body starts with "None", case-insensitive,
or is blank) vs. real content (`derived:` extraction script matching
`^## What did not work\s*\n(.*?)(?=\n## |\Z)` per file, classification
by regex `^(?i)none\b` on the trimmed body):

```
$ python3 - <<'PY'
import re
from pathlib import Path
files = [ ... the 20 paths listed above ... ]
SECTION_RE = re.compile(r"(?m)^## What did not work\s*\n(.*?)(?=\n## |\Z)", re.S)
total_chars_all = 0
empty_section_chars_all = 0
n_empty = n_real = n_missing = 0
for f in files:
    text = Path(f).read_text(encoding="utf-8-sig", errors="replace")
    total_chars_all += len(text)
    m = SECTION_RE.search(text)
    if not m:
        n_missing += 1; continue
    body = m.group(1).strip()
    if re.match(r"(?i)^none\b", body) or not body:
        n_empty += 1; empty_section_chars_all += len(m.group(0))
    else:
        n_real += 1
print(n_empty, n_real, n_missing, total_chars_all, empty_section_chars_all)
print(empty_section_chars_all / total_chars_all * 100)
PY
9 8 3 159159 522
0.328...  # boilerplate_output_token_share, char-length proxy, this
          # survey's method (see caveat below on divergence from
          # current-state.md's own ledger-log method)
```

Sample of what "empty" currently looks like — not uniformly terse:

```
docs/issue-759/reports/implementation.md (180 chars):
## What did not work

None — no attempted approach was written then undone during this
build; the two hunt findings below were gaps in the approved design,
not abandoned attempts.

docs/issue-674/reports/implementation.md (146 chars):
## What did not work

None — the change matched the approved proposal's "What will be done"
section without needing an approach change mid-build.
```

vs. the floor already in use elsewhere in the same sample (28 chars —
already the floor for a majority of the heading-carrying records,
`derived: see the classification counts above: empty-classified=9 of
17 heading-carrying records`):

```
## What did not work

None.
```

and a genuine real-content case that must stay untouched (`docs/issue-659/
reports/implementation.md`, 1665 chars, a real bypass finding + fix
narrative) — confirms the empty/real-content split is not just
theoretical, both shapes coexist in the current 20-record sample.

This gives a concrete, reproducible pre-tiering baseline
(`boilerplate_output_token_share` ≈ 0.33% by this char-proxy method,
over this specific 20-record window and section set) and shows the
30%-relative-reduction threshold is reachable: collapsing all 9
empty-classified instances to the already-in-use 28-char floor would
take `empty_section_chars_all` from 522 to 252 (9 × 28), a 51.7%
relative reduction — comfortably past the 30% bar, using only the
one-line form records in this same sample already produce today.
Caveat: current-state.md's own methodology measures *Write-call
content* from session logs (`content` field length / 4), not committed
file content — this survey's number is a same-spirit but not
byte-identical proxy (committed-file chars, no /4 divisor since it is
not being compared against an output-token count directly, only used
internally as a relative before/after share). A future measurement
round should use current-state.md's own ledger-log method for the
official post-tiering 20-record comparison, not this survey's git-log
proxy, to stay consistent with the pre-registered baseline's own
measurement method.

## Existing directive+gate pairing precedent in this repo (structural template for phase 2)

`on-the-record/hooks/record-claim-guard.sh` (gate, PreToolUse on
`Write|Edit|MultiEdit`, scoped to `docs/issue-*/reports/**`) +
`on-the-record/hooks/record-claim-shape-directive.sh` (directive,
`UserPromptSubmit`, role-session-only via `CLAUDE_ROLE`, fails open,
`ORCHESTRATE_OFF` kill switch, generates its text from the gate's own
check functions) is registered in `on-the-record/hooks/hooks.json` and
has rows in `docs/specs/enforcement-boundary.md` (verdict `contract`)
and `docs/specs/generated-paths.md` (`n/a`, "reads/validates only, no
write call"). `on-the-record/hooks/gate-registration-guard.sh` refuses
a commit that stages a new `gates/*.py`/`on-the-record/hooks/*.sh`
mechanism file with no matching row in those two spec files —
confirmed by reading the hook's own header comment and matching rows
for `record-claim-guard.sh`/`record-claim-shape-directive.sh` in both
spec files. This is the concrete template phase 2 will follow for any
new directive file.

## Test baseline (main, pre-#760)

`derived: python3 -m pytest -q`:

```
1114 passed, 2 skipped in 167.78s (0:02:47)
```

This does not match the operator's cited 915-passed baseline from
commit `7ae6e7c` (issue-759 landing) — `main` has since advanced past
that commit (merges for #772/issue-742, #771/issue-759 restated, and
others already visible in `git log`), so the suite grew. This survey
stages no code changes, so the current-HEAD count above (0 failed) is
the correct pre-#760 baseline to compare phase-2 results against, not
the older cited figure.

## Unknowns / risk

- The pre-tiering baseline computed above uses this survey's git-log
  proxy method, not current-state.md's ledger-log method — a future
  measurement round re-deriving the official pre/post comparison
  should use the ledger method for consistency with the pre-registered
  package's own stated measurement (`over the next 20 records written
  under the tiered format` implies session-log-based counting, matching
  how the primary metric itself will be measured going forward).
- Because the current empty-case baseline is already small in absolute
  terms (0.33% of a record's own chars, and `## What did not work` is
  a single section within one record type), the total output-token
  impact of this candidate is modest even at the full 30% threshold —
  consistent with `docs/issue-745/proposals/product-discovery.md`'s own
  RICE table scoring this candidate's Impact field at 3, one point
  below Item 1 candidate 1's Impact field of 4 (`derived: docs/issue-745/proposals/product-discovery.md`,
  Item 1's RICE table row 1 vs Item 2's RICE table row 1, Impact
  column).
