#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3134.

Builds a synthetic tree modeled on the issue's own live repro
(study-companion PR #11: code lands, one section of its record --
"Limitation" -- is materially wrong, and `supersedes:` cannot correct
just that section without marking the whole, mostly-correct record
non-authoritative). Record A stays authoritative; record B amends one
of A's sections. This probe asserts a reader with **only the merged
tree** -- no PR body, no issue comments -- reaching A cannot miss the
amendment.

This probe fails against current main: `amends.py` does not exist
there, so the import below raises ModuleNotFoundError before any
assertion runs -- an honest failure, not a staged one.

**What "reaching A" means here, and why the index is required.** Unlike
`supersedes:`, A's own raw content carries no marker at all -- the
`amends:` field lives only in B's frontmatter, and no write shape
reaches A to put one there (`amends.py`'s module docstring; the same
`board-gate.sh` write-set isolation `supersession.py` already
documents). So this probe demonstrates the crux directly: it shows that
content-only inspection of A in isolation gives zero signal, and then
shows that the generated amends index (`amends_index.INDEX_PATH`,
built by `gates/amends_index.py`) -- a gate-enforced, cross-cutting
index that is not owned by A's
issue and so is not blocked by the same write-set rule -- is where the
amendment is guaranteed to surface. That index is what "reaching A
through the merged tree" is defined to route through for this repo's
tooling; the probe's failure mode if that routing were missing (a stale
or absent index) is exactly what `gates/amends_index.py::check()`
refuses.

Run as `python3 gates/probe_amends_is_discoverable.py` from the repo
root, no arguments. Exits 0 on success, non-zero with a message on
stderr otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
import amends  # noqa: E402
import amends_index  # noqa: E402

TARGET_PATH = "docs/issue-10/reports/research-evidence-discipline+silent-failure-audit-3b9228ee.md"
CORRECTOR_PATH = "docs/issue-15/reports/verification.md"

TARGET_CONTENT = """---
issue: 10
role: research-evidence-discipline+silent-failure-audit
loop_state: landed
---

# issue-10 -- research-evidence-discipline+silent-failure-audit record

## What was done

Delivered a question-generation and scoring pipeline; all five
acceptance checks pass.

## Limitation

The harder untested case is multi-turn context drift; single-section
degradation was exercised and the scoring function is confirmed to read
the generated question when computing its 1.00 baseline.
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


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    tree = {TARGET_PATH: TARGET_CONTENT, CORRECTOR_PATH: CORRECTOR_CONTENT}

    print("-- demonstrated tree (merged, no PR body / issue comments) --")
    for path in sorted(tree):
        print(f"  {path}")
    print(f"-- marker, as written in {CORRECTOR_PATH}'s own frontmatter --")
    print(f"  {MARKER}")

    parsed = amends.parse_amends(CORRECTOR_CONTENT)
    if parsed != (TARGET_PATH, "limitation"):
        _fail(f"parse_amends on the corrector's own content returned "
              f"{parsed!r}, expected {(TARGET_PATH, 'limitation')!r}.")

    verdict = amends.resolve_amendments(tree)
    print(f"-- resolve_amendments() verdict --\n  {verdict}")
    if verdict["amended"] != {TARGET_PATH: {"limitation": CORRECTOR_PATH}}:
        _fail(f"expected {TARGET_PATH!r}'s 'limitation' section amended by "
              f"{CORRECTOR_PATH!r}; got {verdict['amended']!r}")
    if verdict["broken"] or verdict["missing_section"] or verdict["conflicts"] or verdict["cycles"]:
        _fail(f"demonstrated tree should resolve cleanly; got {verdict!r}")

    # The crux: A's own raw content, read in isolation, carries no
    # signal that it has been amended -- proving the field alone is not
    # the fix, exactly as the issue's consult warned.
    if "amends" in TARGET_CONTENT or CORRECTOR_PATH in TARGET_CONTENT:
        _fail("test fixture is invalid: TARGET_CONTENT must not itself "
              "reference the amendment -- the whole point is that no "
              "write shape reaches A to put one there.")
    print("-- confirmed: A's own raw content has zero signal of the "
          "amendment (no write shape reaches it) --")

    # The fix: the generated, gate-enforced index is where "reaching A"
    # is required to route through. Build it purely from tree content
    # (amends_index.render_index takes path->content, no filesystem).
    index_content = amends_index.render_index(tree)
    expected_row = f"| `{TARGET_PATH}#limitation` | `{CORRECTOR_PATH}` |"
    if expected_row not in index_content:
        _fail(f"generated index does not surface the amendment -- a reader "
              f"consulting {amends_index.INDEX_PATH!r} would still miss it. "
              f"Expected a row starting {expected_row!r} in:\n{index_content}")
    print(f"-- confirmed: {amends_index.INDEX_PATH} surfaces the amendment "
          "against A, with the reason, before a reader trusts A's "
          "Limitation section --")

    # And the index cannot be allowed to drift silently: check() must
    # refuse when the checked-in index does not match what the tree's
    # edges resolve to (an "unlinked amendment").
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        for rel, content in tree.items():
            full = repo / rel
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
        bad = amends_index.check(repo)
        if not bad:
            _fail("gates/amends_index.py::check() passed with no index file "
                  "committed at all, despite a live amendment in the tree -- "
                  "an unlinked amendment must be refused, not silently "
                  "treated as 'nothing to check'.")
        print(f"-- confirmed: check() refuses an unlinked amendment -- "
              f"{bad[0]!r} --")

        (repo / amends_index.INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
        amends_index.update(repo)
        bad_after_update = amends_index.check(repo)
        if bad_after_update:
            _fail(f"check() still refuses after --update regenerated the "
                  f"index: {bad_after_update!r}")
        print("-- confirmed: check() passes once the index is regenerated "
              "-- the amendment is now reachable from the merged tree --")

    print("-- shape decision --")
    print("  Required backlink in the target was rejected outright: no "
          "write shape reaches a foreign issue's record "
          "(board-gate.sh write-set isolation, the same boundary "
          "supersedes: already documents). Discoverability is delivered "
          "instead by a generated, cross-cutting index "
          f"({amends_index.INDEX_PATH!r}, outside any single "
          "docs/issue-<n>/ tree so any session may regenerate it) plus "
          "gate refusal when the tree's amends: edges and the checked-in "
          "index disagree -- an amendment can land, but it cannot land "
          "unlinked.")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
