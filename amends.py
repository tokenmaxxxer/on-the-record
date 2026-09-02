"""Issue #3134: a section-scoped correction primitive for the case
`supersedes:` (issue #3050, `supersession.py`) cannot cover.

`supersedes:` only replaces a whole artifact -- see its own module
docstring's "Decision: two artifacts, not one." A correction confined to
one section of a larger, mostly-correct foreign record cannot use it
without marking that entire record non-authoritative (study-companion
PR #11's Limitation section is the live case this closes).

**Why this is harder than `supersedes:`.** `resolve_authoritative()`
works because the target of a `supersedes:` edge stops being
authoritative -- anything that wants the truth is forced through the
resolver, because trusting the raw file is wrong by construction. An
`amends:` target STAYS authoritative. Nothing routes a reader through a
resolver at all; they open the file and read it. The frontmatter field
alone reproduces today's problem with an extra layer (the issue's own
framing, from its `decision-brief` consult) -- discoverability is the
actual deliverable, not the field.

**Discoverability decision -- REVISED in the #3134 repair round.** The
first delivery (PR #3143) shipped only the generated-index shape below
and was independently verified Absent: it redefined "reaching A" as
"consulting the index," not "opening A," and a reader who does not
already know the index convention exists has zero signal from A's own
content. `amends_backlink.py` (new in this round) is the fix -- read its
module docstring for the full "who writes it, when" reasoning; this
section only records the final shape:

  1. Required backlink written into the target record itself, in the
     SAME commit as the correcting session's own record. Rejected: the
     target is by definition outside that session's write set
     (board-gate's write-set isolation -- harness-side, not a file in
     this checkout, exercised live in docs/issue-3050/reports/
     independent-verification-1.md -- pins a session to its own
     `docs/issue-<n>/` tree). This is not a sequencing question; the
     session's own Edit/Write calls against a foreign tree are refused
     before a commit is ever attempted.

  2. A generated, cross-cutting index (this repo's own precedent:
     `docs/specs/reconciled-index.md` + `gates/spec_index.py`). Kept, but
     demoted from sole mechanism to supplementary cross-cutting summary
     -- see `gates/amends_index.py`. Answers "what in this tree has an
     open correction," not "did I just read a wrong section."

  3. A required backlink applied by the LANDING step (not the correcting
     session) once the correcting PR lands, gated so an `amends:` edge
     cannot go unlinked in the merged tree. Adopted --
     `amends_backlink.py::apply_backlinks()`/`missing_backlinks()`
     (pure, domain layer) plus `gates/amends_index.py`'s
     `write_backlinks()`/`--apply-backlinks` (the landing-step CLI) and
     `check()`'s `missing_backlinks` blocking reasons (fails closed on an
     `amended` edge whose target does not yet carry the marker). This is
     what makes "opening A directly" -- not "knowing to check an index"
     -- the route that surfaces the amendment.

This module is the domain layer -- pure functions over `path -> content`
strings, no filesystem or git access, mirroring `supersession.py`'s own
contract. `gates/amends_index.py` is the infrastructure/interface layer
that reads the real tree and writes/checks the generated index and the
backlinks; `amends_backlink.py` is the domain layer for the backlink
half, imported by both.
"""
from __future__ import annotations

import posixpath
import re

_FRONTMATTER_DELIM = "---"
_AMENDS_RE = re.compile(r"(?m)^amends:\s*(\S+)")
_REASON_RE = re.compile(r"(?m)^amends:\s*\S+\s*#\s*(.*)$")
_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9\- ]")
_SLUG_SPACE_RE = re.compile(r"\s+")


def section_anchor(heading_text: str) -> str:
    """Normalize a markdown heading's text into the stable anchor form
    used both when a corrector names a target section and when this
    module checks that section actually exists in the target's own
    headings (GitHub-style slug: lowercase, punctuation stripped, runs
    of whitespace collapsed to a single `-`)."""
    lowered = heading_text.strip().lower()
    stripped = _SLUG_STRIP_RE.sub("", lowered)
    return _SLUG_SPACE_RE.sub("-", stripped.strip())


def render_amends_field(target_path: str, section_heading: str, reason: str) -> str:
    """The exact frontmatter line a correcting session's own record adds
    to mark itself as amending one section of `target_path`. `section_heading`
    is the target's own heading text (e.g. `"Limitation"`), normalized here
    to the anchor a reader/resolver matches against. `reason` travels as a
    YAML comment, visible to a plain-text reader, not parsed back out by
    `parse_amends()`."""
    anchor = section_anchor(section_heading)
    return f"amends: {target_path}#{anchor}  # {reason}"


def _frontmatter_block(content: str) -> str | None:
    lines = content.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_DELIM:
            return "\n".join(lines[1:i])
    return None          # opening delimiter with no close -- not a record


def parse_amends(content: str) -> tuple[str, str] | None:
    """The `(target_path, section_anchor)` this record's own frontmatter
    declares it amends, or `None` when the record carries no such field
    (the common case -- most records amend nothing). A value with no
    `#<section>` is treated as carrying no field at all: `amends:`
    without a section is not a smaller version of this primitive, it is
    `supersedes:`'s job, and silently accepting it here would let a
    whole-record correction hide from `supersession.py`'s resolver."""
    fm = _frontmatter_block(content)
    if fm is None:
        return None
    m = _AMENDS_RE.search(fm)
    if m is None:
        return None
    value = m.group(1)
    if "#" not in value:
        return None
    target, _, anchor = value.partition("#")
    if not target or not anchor:
        return None
    return target, anchor


def extract_reason(content: str) -> str:
    """The free-text reason travelling as a YAML comment on this record's
    own `amends:` line (see `render_amends_field()`), or `""` when the
    line carries no `#`-reason -- shared by `gates/amends_index.py`'s
    generated index rows and `amends_backlink.py`'s backlink marker text
    so a reader sees the same reason whichever route they took."""
    fm = _frontmatter_block(content)
    if fm is None:
        return ""
    m = _REASON_RE.search(fm)
    return m.group(1).strip() if m else ""


def extract_section_anchors(content: str) -> set[str]:
    """Every section anchor a record's own body exposes, derived from its
    markdown headings alone (no frontmatter) -- what a corrector's
    `amends:` target section is checked against."""
    lines = content.splitlines()
    start = 0
    if lines and lines[0].strip() == _FRONTMATTER_DELIM:
        for i in range(1, len(lines)):
            if lines[i].strip() == _FRONTMATTER_DELIM:
                start = i + 1
                break
    body = "\n".join(lines[start:])
    return {section_anchor(m.group(1)) for m in _HEADING_RE.finditer(body)}


def resolve_amendments(records: dict[str, str]) -> dict:
    """Decide, from `records` (path -> full file content) alone, the
    status of every `amends:` edge in the tree -- the reader-with-only-
    the-merged-tree test this module exists to satisfy, mirroring
    `supersession.resolve_authoritative()`'s contract one level down (at
    section grain, target-stays-authoritative instead of
    target-becomes-non-authoritative).

    Returns a dict with five keys, each fails-closed on its own
    degenerate case rather than picking a winner:

      - `amended`: {target_path: {section_anchor: corrector_path}} --
        unambiguous edges: target exists, section exists in the
        target's own headings, exactly one record amends it, and the
        edge is not part of a cycle.
      - `broken`: sorted `amends:` targets naming a path absent from
        `records` (after path normalization, matching
        `supersession.py`'s own `./`-variant handling) -- a dangling
        reference the reader cannot verify from the tree alone.
      - `missing_section`: sorted `"target_path#anchor"` strings where
        the target resolves but that section anchor is not among its
        own headings -- the target moved, was renamed, or the anchor
        was never real.
      - `conflicts`: {"target_path#anchor": sorted[corrector_paths]} --
        two or more records both claim to amend the same section of the
        same target with independent (possibly contradictory) text.
        Content alone cannot say which is real, so none of them lands
        in `amended`.
      - `cycles`: sorted list of `"corrector_path->target_path#anchor"`
        edge strings that sit on a directed cycle in the amends graph
        (A amends B, ..., amends A) -- neither end is placed in
        `amended`; a human resolves a mutual-correction loop, content
        alone cannot.

    A `supersedes:`-style rejection of ambiguity: broken and
    missing_section edges are excluded before conflict/cycle detection
    runs (an edge that cannot even resolve to a real target+section is
    not eligible to conflict or cycle), and conflicting edges are
    excluded before cycle detection (two correctors already fighting
    over one section is reported as a conflict, not folded into a
    cycle report even if one of them also happens to close a loop).
    """
    norm_to_key: dict[str, str] = {}
    for path in sorted(records, reverse=True):
        norm_to_key[posixpath.normpath(path)] = path

    edges: list[tuple[str, str, str]] = []   # (corrector, target, anchor)
    broken: set[str] = set()
    missing_section: set[str] = set()
    for path, content in records.items():
        parsed = parse_amends(content)
        if parsed is None:
            continue
        target, anchor = parsed
        resolved_target = norm_to_key.get(posixpath.normpath(target))
        if resolved_target is None:
            broken.add(target)
            continue
        target_anchors = extract_section_anchors(records[resolved_target])
        if anchor not in target_anchors:
            missing_section.add(f"{resolved_target}#{anchor}")
            continue
        edges.append((path, resolved_target, anchor))

    claims: dict[tuple[str, str], list[str]] = {}
    for corrector, target, anchor in edges:
        claims.setdefault((target, anchor), []).append(corrector)

    conflicts: dict[str, list[str]] = {}
    conflicted_keys: set[tuple[str, str]] = set()
    for (target, anchor), correctors in claims.items():
        if len(correctors) > 1:
            conflicts[f"{target}#{anchor}"] = sorted(correctors)
            conflicted_keys.add((target, anchor))

    candidate_edges = [
        (corrector, target, anchor) for corrector, target, anchor in edges
        if (target, anchor) not in conflicted_keys
    ]

    cyclic_paths = _find_cyclic_paths(candidate_edges)

    amended: dict[str, dict[str, str]] = {}
    cycles: list[str] = []
    for corrector, target, anchor in candidate_edges:
        if corrector in cyclic_paths and target in cyclic_paths:
            cycles.append(f"{corrector}->{target}#{anchor}")
            continue
        amended.setdefault(target, {})[anchor] = corrector

    return {
        "amended": amended,
        "broken": sorted(broken),
        "missing_section": sorted(missing_section),
        "conflicts": conflicts,
        "cycles": sorted(cycles),
    }


def _find_cyclic_paths(edges: list[tuple[str, str, str]]) -> set[str]:
    """Record paths that sit on a directed cycle in the corrector->target
    graph built from `edges` (ignoring section anchors -- a cycle is a
    property of which records amend which other records, at any
    section). Plain DFS cycle detection over a small, per-tree graph."""
    graph: dict[str, set[str]] = {}
    for corrector, target, _anchor in edges:
        graph.setdefault(corrector, set()).add(target)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in graph}
    on_stack: list[str] = []
    cyclic: set[str] = set()

    def visit(node: str) -> None:
        color[node] = GRAY
        on_stack.append(node)
        for neighbor in graph.get(node, ()):
            if color.get(neighbor, WHITE) == WHITE:
                visit(neighbor)
            elif color.get(neighbor) == GRAY:
                idx = on_stack.index(neighbor)
                cyclic.update(on_stack[idx:])
        on_stack.pop()
        color[node] = BLACK

    for node in list(graph):
        if color[node] == WHITE:
            visit(node)
    return cyclic
