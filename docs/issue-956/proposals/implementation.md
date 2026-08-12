---
status: proposed
files:
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - harness/fixture-target/scenario.py
---

# Proposal — issue #956: target-project-repo requirement capture

## Request

Operator requirements/priorities/philosophy/goals stated in conversation must be condensed into a
TARGET project repo's docs by default when on-the-record is installed there as a plugin — hooks
only, no CI/Actions, no explicit skill invocation (northpole req#7 no-band-aid: a capture path that
only works against on-the-record's own repo is a band-aid). Reuse the landed digest machinery
(`gates/requirement_digest.py`, `requirement-digest-preflight.sh`) as substrate; make the capture
path repo-agnostic and default-on in target repos.

## Constraints

- Hooks only — no CI/Actions, no explicit skill call to trigger capture (req#7).
- Must not regress the existing on-the-record-repo behavior: on an `issue-<n>/<role>` branch,
  capture keeps writing to the issue-scoped `docs/issue-<n>/product/<cat>.md` path (#684's
  concurrent-issue collision fix stays intact).
- Empty state: a repo with no stated requirements in the transcript gets no digest/doc writes —
  the hook's existing `if not active: sys.exit(0)` early-return already guarantees this; this
  proposal must not weaken it.
- Observation-loss regression is inviolable: a category flagged in conversation must still surface
  an advisory (or land a write) in every repo shape the hook now covers, not silently drop.

## Rationale

Two ways to make the capture path work outside `issue-<n>/<role>` branches were considered:

- **Rejected**: require target-project users to adopt on-the-record's own `issue-<n>/<role>`
  branch-naming convention as a precondition for capture to activate at all. This is exactly the
  band-aid the issue's title names — it "works" only when the *host* repo happens to mirror
  on-the-record's own internal workflow, which is not something a target-project's ordinary
  `main`/`feature/x` branches will ever do. Rejected because it does not satisfy req#7's no-band-aid
  bar; the issue exists specifically because this was the prior state.
- **Chosen**: keep the existing issue-scoped path when the branch matches `issue-<n>/<role>`
  (preserves #684's fix, needed only inside on-the-record's own multi-role workflow), and fall back
  to a single fixed non-issue-scoped path, `docs/product/<cat>.md`, whenever it doesn't. A
  target-project repo installing on-the-record as a plugin is not expected to run concurrent
  on-the-record role sessions against the same repo the way #684's collision scenario was guarding
  against, so the simpler pre-#684 layout is the right default there — and it is what makes capture
  actually default-on rather than conditional on branch naming.

## What will be done

- `product-capture-stopgate.sh`: when the branch regex does not match `issue-<n>/<role>`, instead
  of exiting 0, fall through with `issue_scope = None` and write to `docs/product/<cat>.md`
  (repo-root, no issue segment) instead of `docs/issue-<n>/product/<cat>.md`; the advisory message
  drops the issue-number segment accordingly. All other logic (category regexes, transcript walk,
  diff-based already-recorded check, empty-state early return) is unchanged — this is a path-choice
  change only, not a rewrite of the flagging logic.
- `test_product_capture_stopgate.py`: add a test asserting capture activates and writes/advises
  against `docs/product/<cat>.md` on a non-`issue-<n>/<role>` branch (e.g. `main`), and a test
  reasserting the existing empty-state guard holds on that branch shape too (no flagged sentence ->
  no write, no advisory).
- `harness/fixture-target/scenario.py` (new, mirrors `fixture-requirement-digest/scenario.py`'s
  no-live-session pattern): seeds a scratch git repo on branch `main` (i.e., not an on-the-record
  issue branch) with a synthetic Stop-event transcript containing one flagged requirement
  sentence, invokes `product-capture-stopgate.sh` against it directly, and asserts (a) the advisory
  fires / the fallback doc path is the one referenced, and (b) a second scenario repo with a
  transcript carrying no flagged sentences produces no `docs/product/*.md` writes at all (the
  empty-state guard).

## Accumulation

`harness/fixture-target/scenario.py` adds one more inline-subprocess scratch-repo scenario file
alongside `harness/fixture-requirement-digest/scenario.py` and the other `harness/fixture-*`
scenarios — each is a standalone script with its own local seed/setup helpers, not a shared
library, matching the existing sibling scenarios' own convention (no shared harness helper module
exists today for this pattern). If N more `harness/fixture-*` scenarios accumulate this way, the
inline per-scenario setup stays local and small (one seeded scratch repo + one subprocess
invocation each) — a shared helper would only be worth extracting if a common setup shape repeats
across 3+ scenarios verbatim, which is not yet the case across the existing fixtures.

## Out of scope

- Any change to `gates/requirement_digest.py` or `requirement-digest-preflight.sh` themselves —
  both are already repo-agnostic per the survey; nothing there needs to change for this issue.
- Auto-writing into `docs/specs/requirements.md` from conversation — not asked for; that registry
  stays role-judgment-populated.
- Any change to on-the-record's own `issue-<n>/<role>` capture path/output shape.

## How you'll know it worked

- `python3 -m pytest on-the-record/hooks/test_product_capture_stopgate.py` — full suite green,
  including the two new tests.
- `python3 harness/fixture-target/scenario.py` — exits 0, prints the capture-fires and
  empty-state-guard rows PASS.
