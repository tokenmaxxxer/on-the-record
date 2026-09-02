"""Issue #3134 repair round: the backlink half of `amends:` discoverability.

The independent verification of the first delivery (PR #3143, landed as
#3146) found `amends.py`'s original discoverability decision Absent: it
shipped only `gates/amends_index.py`'s generated index, and graded
"reaching A" as "consulting the index" rather than "opening A" -- a
reader who does not already know the index convention exists has no path
to the correction. The issue's own text is explicit that this repo's
`docs/issue-<n>/reports/*.md` files are static markdown with no
rendering layer: a reader "opens A" by reading that file directly. So
discoverability has to leave a trace IN A -- this module computes it.

**Who writes it, and why this does not relax write-set isolation.** The
correcting session's own record (the file carrying `amends:`) lives in
its own `docs/issue-<n>/` tree and is the only file that session's write
set covers -- board-gate's write-set isolation (harness-side; not a file
in this checkout, exercised live in docs/issue-3050/reports/
independent-verification-1.md, `git ls-files | grep -i board-gate`
returning no hook script) refuses any Edit/Write a spawned session
attempts against a foreign issue's tree, and that refusal is correct and
load-bearing (`amends.py`'s own docstring; #3050's root-cause comment).
No amount of code in THIS repository changes what a spawned session's
own tool calls are allowed to touch.

What changes is WHO inserts the backlink: never the correcting session.
`write_backlinks()` (`gates/amends_index.py`'s `--apply-backlinks` CLI
mode) is a landing-step operation -- run by the orchestrator/operator
identity that is not bound to any single issue's branch (the same
identity `merge-allow-gate.sh` already distinguishes via
`TOKENMAXXXER_SPAWNED` resolving empty), after the correcting PR lands,
against the merged tree directly. That identity is not inside any
session's write set, so board-gate's isolation has nothing to refuse.

Three shapes were on the table for "who writes it, when":

  1. The correcting session's own commit carries both its record AND the
     target's backlink, in one changeset. Rejected: the target is by
     definition outside that session's write set -- this is not a
     sequencing question, the session's own tool calls are refused
     before a commit is ever attempted.
  2. A landing-time gate refuses to merge an `amends:`-carrying PR until
     the target already carries the backlink, applied by the landing
     step. Adopted -- see `gates/amends_index.py::check()`'s
     `missing_backlinks` reasons and `write_backlinks()`/
     `--apply-backlinks`. This is the shape the issue's own text names as
     the natural one.
  3. An index that A's own rendering is required to consult. This is
     what PR #3143 shipped alone, and it is exactly what this repair
     round found Absent: "reaching A" was redefined as "consulting the
     index," and nothing routes a reader who opens A straight to the
     index. Demoted to a supplementary cross-cutting summary
     (`gates/amends_index.py` keeps generating it) rather than the sole
     discoverability mechanism -- useful for "what in this tree has an
     open correction" as a standing question, insufficient on its own
     for "did I just read a wrong section."

This module is the domain layer -- pure functions over `path -> content`
strings plus the backlink-shaped text they produce, no filesystem or git
access, mirroring `amends.py`'s own contract. `gates/amends_index.py` is
the infrastructure layer that reads/writes the real tree.
"""
from __future__ import annotations

import amends

_MARKER_PREFIX = "> **Amended**"


def render_backlink_marker(corrector_path: str, reason: str) -> str:
    """The exact line inserted into a target record's body, directly
    under the heading it amends -- greppable (`_MARKER_PREFIX`), naming
    the corrector and carrying the same reason text a plain-text reader
    of the corrector's own `amends:` frontmatter comment would see."""
    return f"{_MARKER_PREFIX} by `{corrector_path}`: {reason}"


def has_backlink(target_content: str, corrector_path: str, reason: str) -> bool:
    """Whether `target_content` already carries the exact marker for this
    corrector/reason -- the idempotency check `insert_backlink()` and
    `missing_backlinks()` both use."""
    return render_backlink_marker(corrector_path, reason) in target_content


def insert_backlink(target_content: str, anchor: str, corrector_path: str,
                     reason: str) -> str:
    """`target_content` with the backlink marker inserted as a new line
    directly after the heading matching `anchor`. Idempotent: an
    already-present marker for this exact corrector/reason is left alone
    rather than duplicated. Raises `ValueError` if `anchor` names no
    heading in `target_content` -- callers are expected to have already
    confirmed the anchor exists via `amends.resolve_amendments()` (an
    `amended` edge only exists once the anchor resolved), so this is a
    caller-contract violation, not a data condition to absorb quietly."""
    if has_backlink(target_content, corrector_path, reason):
        return target_content

    marker = render_backlink_marker(corrector_path, reason)
    lines = target_content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = amends._HEADING_RE.match(line.rstrip("\n"))
        if m and amends.section_anchor(m.group(1)) == anchor:
            if line.endswith("\n"):
                insertion = f"\n{marker}\n"
            else:
                insertion = f"\n\n{marker}"
            return "".join(lines[: i + 1]) + insertion + "".join(lines[i + 1:])

    raise ValueError(
        f"insert_backlink: no heading in target_content resolves to "
        f"anchor {anchor!r} -- caller must confirm the anchor exists "
        f"(e.g. via amends.resolve_amendments()) before calling this."
    )


def apply_backlinks(records: dict[str, str]) -> dict[str, str]:
    """`{target_path: updated_content}` for every target with at least
    one unambiguous (`amended`) edge and a not-yet-present backlink --
    targets already fully up to date are omitted. Pure over `records`;
    the caller (the landing step, `gates/amends_index.py::
    write_backlinks()`) is responsible for writing the results back to
    disk."""
    verdict = amends.resolve_amendments(records)
    updated: dict[str, str] = {}
    for target, sections in verdict["amended"].items():
        content = records[target]
        for anchor, corrector in sorted(sections.items()):
            reason = amends.extract_reason(records[corrector])
            content = insert_backlink(content, anchor, corrector, reason)
        if content != records[target]:
            updated[target] = content
    return updated


def missing_backlinks(records: dict[str, str]) -> list[str]:
    """Sorted `"target#anchor (amended by corrector)"` strings for every
    unambiguous `amended` edge whose target does not yet carry the
    backlink -- the fails-closed check `gates/amends_index.py::check()`
    calls. A reader with only the merged tree who opens `target` and
    finds none of these strings' targets amended has, by construction,
    not missed anything: every edge that resolved to `amended` either has
    its marker present or is reported here."""
    verdict = amends.resolve_amendments(records)
    missing = []
    for target, sections in verdict["amended"].items():
        content = records[target]
        for anchor, corrector in sections.items():
            reason = amends.extract_reason(records[corrector])
            if not has_backlink(content, corrector, reason):
                missing.append(f"{target}#{anchor} (amended by {corrector})")
    return sorted(missing)
