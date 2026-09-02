#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3134 (repair round).

Builds a synthetic tree modeled on the issue's own live repro
(study-companion PR #11: code lands, one section of its record --
"Limitation" -- is materially wrong, and `supersedes:` cannot correct
just that section without marking the whole, mostly-correct record
non-authoritative). Record A stays authoritative; record B amends one
of A's sections.

**What changed from the first delivery (PR #3143).** That version's
probe asserted the amendment was reachable by "consulting the generated
index" -- the independent verification (docs/issue-3134/reports/
independent-verification (PR #3146)) graded that Absent: a reader who
does not already know the index convention exists never consults it,
and opening A directly gave zero signal. This probe instead tests the
routes a real reader actually takes, against the real files a landed
correction would produce:

  - Route 1: open A directly (read the file, nothing else) and confirm
    the amendment is unmissable in its own content.
  - Route 2: grep the wrong claim's own text in A and confirm the
    correction is adjacent, in the same grep-scale read.
  - Route 3: follow an inbound link into A (as if arriving from another
    document that links `A#limitation`) and confirm what's waiting there
    still carries the marker -- landing mid-document changes nothing.

Every route must surface the amendment, using ONLY the merged tree (no
PR body, no issue comments) -- and using ONLY what a correcting session
is actually allowed to produce: it cannot write into A itself
(board-gate's write-set isolation), so the fixture below builds A the
way it would really land -- corrector's PR merges first (A unchanged),
then the LANDING step applies the backlink
(`gates/amends_index.py::write_backlinks()` / `amends_backlink.py`) --
and every reader-route assertion runs against A's POST-LANDING content,
which is what a reader who opens the merged tree actually sees.

This probe fails against the branch as it stood before this repair
round: `amends_backlink` did not exist, so the import below raised
`ModuleNotFoundError` before any assertion ran (verified live before
writing the assertions below).

Run as `python3 gates/probe_amends_is_discoverable.py` from the repo
root, no arguments. Exits 0 on success, non-zero with a message on
stderr otherwise.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
import amends  # noqa: E402
import amends_backlink  # noqa: E402
import amends_index  # noqa: E402

TARGET_PATH = "docs/issue-10/reports/research-evidence-discipline+silent-failure-audit-3b9228ee.md"
CORRECTOR_PATH = "docs/issue-15/reports/verification.md"

WRONG_CLAIM = ("The harder untested case is multi-turn context drift; "
               "single-section degradation was exercised and the scoring "
               "function is confirmed to read the generated question when "
               "computing its 1.00 baseline.")

TARGET_CONTENT = f"""---
issue: 10
role: research-evidence-discipline+silent-failure-audit
loop_state: landed
---

# issue-10 -- research-evidence-discipline+silent-failure-audit record

## What was done

Delivered a question-generation and scoring pipeline; all five
acceptance checks pass.

## Limitation

{WRONG_CLAIM}
"""

REASON = ("wrong axis named as the untested harder case; the scoring "
          "function never reads the generated question (1.00 measures "
          "token survival, not comprehension), and a two-section "
          "degradation cannot be represented by a single integer output")
MARKER = amends.render_amends_field(TARGET_PATH, "Limitation", REASON)

CORRECTOR_CONTENT = f"""---
issue: 15
role: verification
loop_state: landed
{MARKER}
---

# issue-15 -- verification record

## What was done

Re-derived the Limitation section against issue #10's own acceptance
checks: the scoring function never reads the generated question, so the
reported 1.00 measures token survival, not comprehension; a two-section
degradation cannot be represented at all, since the output is a single
integer.
"""

# A third, unrelated record that links INTO A's amended section, the way
# a reader following a cross-reference (not consulting the index, not
# starting from A) would arrive there -- e.g. a later session citing the
# original Limitation claim.
LINKING_CONTENT = f"""---
issue: 20
role: unrelated-follow-up
loop_state: landed
---

# issue-20 record

See `{TARGET_PATH}#limitation` for the original scoring discussion.
"""


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    pre_landing_tree = {TARGET_PATH: TARGET_CONTENT,
                         CORRECTOR_PATH: CORRECTOR_CONTENT,
                         "docs/issue-20/reports/follow-up.md": LINKING_CONTENT}

    print("-- pre-landing tree (corrector's own PR merged; A untouched, "
          "exactly what board-gate's write-set isolation allows) --")
    for path in sorted(pre_landing_tree):
        print(f"  {path}")

    parsed = amends.parse_amends(CORRECTOR_CONTENT)
    if parsed != (TARGET_PATH, "limitation"):
        _fail(f"parse_amends on the corrector's own content returned "
              f"{parsed!r}, expected {(TARGET_PATH, 'limitation')!r}.")

    verdict = amends.resolve_amendments(pre_landing_tree)
    if verdict["amended"] != {TARGET_PATH: {"limitation": CORRECTOR_PATH}}:
        _fail(f"expected {TARGET_PATH!r}'s 'limitation' section amended by "
              f"{CORRECTOR_PATH!r}; got {verdict['amended']!r}")
    if verdict["broken"] or verdict["missing_section"] or verdict["conflicts"] or verdict["cycles"]:
        _fail(f"demonstrated tree should resolve cleanly; got {verdict!r}")

    # Pre-landing: confirm the crux the issue names -- A's raw content, on
    # its own, before the landing step runs, carries no signal. This is
    # not a design flaw to leave standing; it is exactly why a LANDING
    # step (not the correcting session) must run before the tree counts
    # as "merged" for a reader's purposes.
    if amends_backlink.has_backlink(TARGET_CONTENT, CORRECTOR_PATH, REASON):
        _fail("test fixture is invalid: TARGET_CONTENT must not already "
              "carry the backlink pre-landing.")

    # The landing step: apply_backlinks() is what gates/amends_index.py's
    # --apply-backlinks CLI mode calls against the real tree. Run it here
    # exactly as the landing operator would, then treat its output as
    # what "the merged tree" actually contains from this point on.
    updated = amends_backlink.apply_backlinks(pre_landing_tree)
    if TARGET_PATH not in updated:
        _fail(f"apply_backlinks() did not update {TARGET_PATH!r} despite "
              f"a resolved amendment against it: {updated!r}")
    merged_tree = dict(pre_landing_tree)
    merged_tree[TARGET_PATH] = updated[TARGET_PATH]
    landed_target = merged_tree[TARGET_PATH]

    print("-- landing step applied (gates/amends_index.py::write_backlinks, "
          "run by the landing/orchestrator identity, never the correcting "
          "session) --")

    # Route 1: open A directly. No index, no other file, no filesystem
    # walk -- just this string.
    if "amends_index" in landed_target.lower():
        _fail("landed target content must not itself reference the index "
              "-- the backlink must stand on its own, not point a reader "
              "at a second file.")
    if CORRECTOR_PATH not in landed_target:
        _fail(f"Route 1 (open A directly) failed: {CORRECTOR_PATH!r} does "
              f"not appear anywhere in A's landed content:\n{landed_target}")
    if "Amended" not in landed_target:
        _fail("Route 1 (open A directly) failed: no greppable amendment "
              "marker in A's landed content.")
    print("-- confirmed Route 1: opening A directly surfaces the "
          f"amendment (found {CORRECTOR_PATH!r} and a marker in A's own "
          "content, no other file consulted) --")

    # Route 2: a reader grep's the WRONG claim's own text (the thing they
    # actually have -- e.g. they're citing "the scoring function is
    # confirmed to read the generated question") and must land within a
    # few lines of the correction, not have to know to look elsewhere.
    lines = landed_target.splitlines()
    claim_line_idx = next(i for i, ln in enumerate(lines) if "1.00 baseline" in ln)
    marker_idx = next((i for i, ln in enumerate(lines) if "Amended" in ln), None)
    if marker_idx is None:
        _fail("Route 2 (grep a claim in A) failed: no marker line found "
              "at all.")
    if abs(marker_idx - claim_line_idx) > 4:
        _fail(f"Route 2 (grep a claim in A) failed: the wrong claim is at "
              f"line {claim_line_idx}, the marker is at line {marker_idx} "
              f"-- too far apart for a reader who grepped the claim to "
              f"notice the correction in the same view:\n{landed_target}")
    print(f"-- confirmed Route 2: grepping the wrong claim's own text "
          f"(line {claim_line_idx}) lands within {abs(marker_idx - claim_line_idx)} "
          f"line(s) of the amendment marker (line {marker_idx}) --")

    # Route 3: follow a link INTO A from an unrelated third record (not
    # via the index, not starting from A) and confirm what's there still
    # carries the marker -- arriving mid-document changes nothing.
    linking_doc = merged_tree["docs/issue-20/reports/follow-up.md"]
    if f"{TARGET_PATH}#limitation" not in linking_doc:
        _fail("test fixture is invalid: the linking record must cite "
              "A#limitation for Route 3 to mean anything.")
    # Simulate "follow the link": the reader ends up reading TARGET_PATH's
    # content at (or near) the `limitation` anchor -- same landed_target
    # string, confirming the marker travels with the section regardless
    # of entry point.
    anchor_heading_idx = next(i for i, ln in enumerate(lines)
                               if amends.section_anchor(ln.lstrip("# ").strip()) == "limitation")
    if not any("Amended" in ln for ln in lines[anchor_heading_idx:anchor_heading_idx + 3]):
        _fail("Route 3 (follow a link into A) failed: landing at the "
              "`limitation` anchor does not show the marker within the "
              "first few lines of that section.")
    print("-- confirmed Route 3: following a link into A's `limitation` "
          "anchor (from an unrelated third record, not the index) still "
          "surfaces the marker immediately --")

    # The index is still generated and still useful as a supplementary
    # cross-cutting view -- but it is no longer load-bearing for any of
    # the three routes above, which is the point.
    index_content = amends_index.render_index(merged_tree)
    expected_row = f"| `{TARGET_PATH}#limitation` | `{CORRECTOR_PATH}` |"
    if expected_row not in index_content:
        _fail(f"generated index does not surface the amendment either -- "
              f"expected a row starting {expected_row!r} in:\n{index_content}")
    print(f"-- confirmed: {amends_index.INDEX_PATH} also carries the "
          "amendment as a supplementary cross-cutting view --")

    # And the gate must fail closed BOTH on a stale/missing index AND on
    # a missing backlink -- an amendment cannot land unlinked either way.
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        for rel, content in pre_landing_tree.items():
            full = repo / rel
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")

        bad = amends_index.check(repo)
        if not bad:
            _fail("check() passed with no index and no backlink committed "
                  "at all, despite a live amendment in the tree.")
        if not any("backlink" in b for b in bad):
            _fail(f"check() did not flag the missing backlink as its own "
                  f"blocking reason: {bad!r}")
        print(f"-- confirmed: check() refuses an unlinked amendment on "
              f"BOTH axes (index + backlink) -- {bad!r} --")

        (repo / amends_index.INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
        amends_index.update(repo)
        bad_after_index_only = amends_index.check(repo)
        if not bad_after_index_only or not any("backlink" in b for b in bad_after_index_only):
            _fail("check() must still refuse after ONLY the index was "
                  f"regenerated -- the backlink is still missing: "
                  f"{bad_after_index_only!r}")
        print("-- confirmed: regenerating the index alone is NOT enough "
              "-- check() still refuses on the missing backlink --")

        written = amends_index.write_backlinks(repo)
        if written != [TARGET_PATH]:
            _fail(f"write_backlinks() should have updated exactly "
                  f"[{TARGET_PATH!r}]; got {written!r}")
        landed_on_disk = (repo / TARGET_PATH).read_text(encoding="utf-8")
        if CORRECTOR_PATH not in landed_on_disk:
            _fail("write_backlinks() wrote a file that does not actually "
                  "contain the backlink.")
        bad_after_backlink = amends_index.check(repo)
        if bad_after_backlink:
            _fail(f"check() still refuses after both the index and the "
                  f"backlink were landed: {bad_after_backlink!r}")
        print("-- confirmed: check() passes once BOTH the index and the "
              "backlink are landed --")

    print("-- shape decision --")
    print("  A required backlink in the target, written in the SAME "
          "commit as the correcting session's own record, was rejected: "
          "the target is outside that session's write set by "
          "construction (board-gate's write-set isolation). The fix is "
          "not to skip the backlink -- it is to move WHO writes it: the "
          "landing step (gates/amends_index.py::write_backlinks(), run "
          "by the orchestrator/operator identity against the merged "
          "tree, never a spawned session) applies it after the "
          "correcting PR lands, and the gate refuses to call an "
          "amendment linked until that has happened. The generated "
          f"index ({amends_index.INDEX_PATH!r}) is kept as a "
          "supplementary cross-cutting view, not the primary "
          "discoverability mechanism.")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
