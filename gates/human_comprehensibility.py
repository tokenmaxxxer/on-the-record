"""issue #1165 (technical-writing, step 2): `human_comprehensibility` tier-1
structure checks — pure, network-free, `quality_bar`-adjacent classifier
module.

Implements the structural prose-shape rules from
`docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md`,
`docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md`,
and `docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md`:

  1. `lead_paragraph_present` — whole-document scope (the one exception to
     the addendum's changed-content-only scoping decision for the other
     rules): a non-empty prose paragraph must exist before the first
     heading/list/step block in the body.
  2. `citation_trailing_placement` — whole-document scope, same reasoning
     as (1): a `canonical:`-style or link-shaped citation inside the lead
     paragraph must sit as a trailing clause or its own line, never split
     the point-stating sentence (content-design PR #1616 items 1&4).
  3. `section_size_bound` — no prose section exceeds ~150 lines without a
     sub-heading break, unless it is a single indivisible fenced code
     block (escape hatch: >=90% fenced-code-block lines).
  4. `no_raw_dump` — a prose section may not be a raw fenced code/log block
     with no surrounding explanatory prose.
  5. `enumeration_cap` — no more than 12 consecutive unstructured list
     items with no sub-heading break.

Rules 3-5 are changed-content-only scoped (addendum point 1): when
`check_record` is given `changed_ranges` (1-indexed inclusive line ranges,
in `text`'s own line numbering, of lines touched by the diff being
checked), a section that carries none of those lines is skipped for rules
3-5. Rules 1-2 stay whole-document (no "changed" sub-unit to scope to —
a lead paragraph either exists/is well-formed or it does not). When
`changed_ranges` is None (default), rules 3-5 run over the whole document,
same as before this scoping was added — this preserves every existing
caller's behavior.

`convention_family_named` (amendment 2, the metadata-slot rule) is
explicitly out of scope for this pass per the issue's delivery-order note.
"""
from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)

SECTION_SIZE_BOUND = 150
ENUMERATION_CAP = 12
FENCE_ESCAPE_HATCH_RATIO = 0.90


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1)


def _strip_leading_blank_lines(text: str) -> str:
    lines = text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    return "\n".join(lines[i:])


def _strip_leading_headings(text: str) -> str:
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (_HEADING_RE.match(lines[i]) or lines[i].strip() == ""):
        i += 1
    return "\n".join(lines[i:])


def _first_paragraph(text: str) -> str:
    """First blank-line-delimited paragraph, after leading blank lines are
    consumed."""
    text = _strip_leading_blank_lines(text)
    lines = text.splitlines()
    para_lines: list[str] = []
    for line in lines:
        if line.strip() == "":
            break
        para_lines.append(line)
    return "\n".join(para_lines)


_TRAILER_LINE_RE = re.compile(
    r"^\s*(part of|advances|closes?|fixe?[sd]?|resolves?)\s+#\d+\s*$", re.IGNORECASE
)


def first_paragraph_is_prose(text: str) -> bool:
    """True iff the first blank-line-delimited paragraph of `text` is
    non-empty prose (not solely trailer/frontmatter lines like
    `Part of #123`, `Closes #123`, a YAML frontmatter block, or a
    markdown heading line). Strips a leading YAML frontmatter block
    (---...---) and leading blank lines first, then leading heading lines
    (`# ...`) before taking the first paragraph."""
    text = text or ""
    text = _strip_frontmatter(text)
    text = _strip_leading_blank_lines(text)
    text = _strip_leading_headings(text)
    para = _first_paragraph(text)
    if not para.strip():
        return False
    # Every non-blank line in the paragraph must be a trailer line for it
    # to be considered non-prose.
    lines = [l for l in para.splitlines() if l.strip()]
    if not lines:
        return False
    if all(_TRAILER_LINE_RE.match(l) for l in lines):
        return False
    if _HEADING_RE.match(lines[0]):
        return False
    if _LIST_ITEM_RE.match(lines[0]):
        return False
    if _FENCE_RE.match(lines[0]):
        return False
    return True


_CITATION_RE = re.compile(
    r"(canonical:\s*\S+|derived:\s*\S+|\[[^\]]+\]\([^)]+\)|https?://\S+)"
)
_TRAILING_PUNCT_RE = re.compile(r"^[)\].,;:]*$")


def citation_trailing_placement(text: str) -> tuple[bool, str]:
    """True (with no reason) iff every `canonical:`/`derived:`-style or
    link-shaped citation inside `text`'s lead paragraph (frontmatter and
    leading headings stripped, same as `first_paragraph_is_prose`) sits as
    a trailing clause of its line or on its own line -- never splits the
    point-stating sentence with prose after it (content-design PR #1616
    items 1&4). A citation with no other content on its line ("own line")
    always passes regardless of what precedes it."""
    text = text or ""
    text = _strip_frontmatter(text)
    text = _strip_leading_blank_lines(text)
    text = _strip_leading_headings(text)
    para = _first_paragraph(text)
    for line in para.splitlines():
        for m in _CITATION_RE.finditer(line):
            before = line[:m.start()].strip()
            after = line[m.end():].strip()
            if not before:
                continue  # citation opens the line -> "its own line" shape
            if after and not _TRAILING_PUNCT_RE.match(after):
                return False, f"citation splits the point-stating sentence: '{line.strip()}'"
    return True, ""


def _sections_with_offsets(body: str) -> list[tuple[int, list[str]]]:
    """Split `body` into sections by heading lines. Each section is
    `(start_index, lines)` where `start_index` is the 0-based index (into
    `body.splitlines()`) of the section's first line, and `lines` is the
    list of lines from (and not including) a heading up to the next
    heading (or end of text). A leading section with no heading is
    included as-is."""
    lines = body.splitlines()
    sections: list[tuple[int, list[str]]] = []
    current: list[str] = []
    current_start = 0
    for i, line in enumerate(lines):
        if _HEADING_RE.match(line):
            sections.append((current_start, current))
            current = []
            current_start = i + 1
        else:
            current.append(line)
    sections.append((current_start, current))
    return sections


def _sections(body: str) -> list[list[str]]:
    """Split `body` into sections by heading lines (line-number-agnostic
    view of `_sections_with_offsets`)."""
    return [lines for _, lines in _sections_with_offsets(body)]


def _section_touches_changes(
    start_index: int, length: int, offset: int,
    changed_ranges: list[tuple[int, int]] | None,
) -> bool:
    """True iff the section starting at `start_index` (0-based, within the
    frontmatter-stripped body) for `length` lines overlaps any
    `changed_ranges` range, translated back to `text`'s own 1-indexed line
    numbering via `offset` (the count of lines `_strip_frontmatter`
    removed from the front). `changed_ranges is None` means "no scoping
    requested" -- always touches."""
    if changed_ranges is None:
        return True
    if length == 0:
        return False
    sec_start = start_index + offset + 1
    sec_end = sec_start + length - 1
    return any(c_start <= sec_end and c_end >= sec_start for c_start, c_end in changed_ranges)


def _fenced_line_ratio(lines: list[str]) -> float:
    non_blank = [l for l in lines if l.strip() != ""]
    if not non_blank:
        return 0.0
    in_fence = False
    fenced_lines = 0
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            fenced_lines += 1
            continue
        if in_fence:
            fenced_lines += 1
    return fenced_lines / len(non_blank)


def _has_fenced_block(lines: list[str]) -> bool:
    return any(_FENCE_RE.match(l) for l in lines)


def _non_fenced_prose_line_count(lines: list[str]) -> int:
    in_fence = False
    count = 0
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if _HEADING_RE.match(line):
            continue
        if line.strip() == "":
            continue
        count += 1
    return count


def _max_consecutive_list_items(lines: list[str]) -> int:
    in_fence = False
    run = 0
    best = 0
    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            run = 0
            continue
        if in_fence:
            continue
        if _LIST_ITEM_RE.match(line):
            run += 1
            best = max(best, run)
        elif line.strip() == "":
            # blank lines between list items don't break the run
            continue
        else:
            run = 0
    return best


def _has_any_prose(body: str) -> bool:
    """True iff `body` has any human-facing prose paragraph anywhere
    (used to decide exemption)."""
    stripped = _strip_frontmatter(body or "")
    for section in _sections(stripped):
        text = "\n".join(section)
        para = _first_paragraph(_strip_leading_blank_lines(text))
        if para.strip():
            lines = [l for l in para.splitlines() if l.strip()]
            if lines and not all(_TRAILER_LINE_RE.match(l) for l in lines):
                if not _HEADING_RE.match(lines[0]) and not _LIST_ITEM_RE.match(lines[0]) \
                        and not _FENCE_RE.match(lines[0]):
                    return True
    return False


def check_record(
    text: str, doc_type: str = "tutorial",
    changed_ranges: list[tuple[int, int]] | None = None,
) -> dict:
    """Runs the tier-1 checks and returns:
    {"exempt": bool, "results": [{"rule": str, "passed": bool, "reason": str}, ...]}
    `exempt=True` (results=[]) when `text` has no human-facing prose
    section at all (e.g. empty, or frontmatter-only, or a pure data/config
    file with no paragraph anywhere) -- per issue #1165 acceptance:
    "artifacts with no human-facing prose section are exempt and listed as
    such" (the caller lists exemption; this function just reports
    exempt=True).

    `changed_ranges`: optional 1-indexed inclusive `(start, end)` line
    ranges, in `text`'s own line numbering, of lines touched by the diff
    being checked (addendum point 1, changed-content-only scoping). When
    given, `section_size_bound`/`no_raw_dump`/`enumeration_cap` skip any
    section that carries none of those lines; `lead_paragraph_present`/
    `citation_trailing_placement` stay whole-document regardless (module
    docstring: no "changed" sub-unit to scope a lead paragraph to)."""
    text = text or ""
    stripped_fm = _strip_frontmatter(text)
    offset = len(text.splitlines()) - len(stripped_fm.splitlines())

    if not _has_any_prose(text):
        return {"exempt": True, "results": []}

    results: list[dict] = []

    # 1. lead_paragraph_present — whole-document scope.
    lead_ok = first_paragraph_is_prose(text)
    results.append({
        "rule": "lead_paragraph_present",
        "passed": lead_ok,
        "reason": "" if lead_ok else (
            "본문 첫 문단이 실질적인 산문이 아니다 — 헤딩/리스트/트레일러가 "
            "아니라 산문 문단이 먼저 와야 한다."
        ),
    })

    # 2. citation_trailing_placement — whole-document scope (same reasoning
    # as lead_paragraph_present; applies to the same lead paragraph).
    citation_ok, citation_reason = citation_trailing_placement(text)
    results.append({
        "rule": "citation_trailing_placement",
        "passed": citation_ok,
        "reason": citation_reason,
    })

    sections = _sections_with_offsets(stripped_fm)

    size_reasons: list[str] = []
    dump_reasons: list[str] = []
    enum_reasons: list[str] = []

    for start_index, section in sections:
        non_blank_count = len([l for l in section if l.strip() != ""])
        if non_blank_count == 0:
            continue
        if not _section_touches_changes(start_index, len(section), offset, changed_ranges):
            continue

        # section_size_bound
        if len(section) > SECTION_SIZE_BOUND:
            ratio = _fenced_line_ratio(section)
            if ratio < FENCE_ESCAPE_HATCH_RATIO:
                size_reasons.append(
                    f"섹션이 {len(section)}줄로 {SECTION_SIZE_BOUND}줄 상한을 "
                    f"초과했고 서브헤딩으로 나뉘어 있지 않다."
                )

        # no_raw_dump
        if _has_fenced_block(section):
            prose_lines = _non_fenced_prose_line_count(section)
            if prose_lines < 2:
                dump_reasons.append(
                    "섹션이 설명 산문 없이(또는 2줄 미만) 펜스 코드/로그 블록만 "
                    "붙여넣었다."
                )

        # enumeration_cap
        if doc_type != "reference":
            max_run = _max_consecutive_list_items(section)
            if max_run > ENUMERATION_CAP:
                enum_reasons.append(
                    f"섹션에 서브헤딩 구분 없이 연속된 리스트 항목이 {max_run}개로 "
                    f"{ENUMERATION_CAP}개 상한을 초과했다."
                )

    size_ok = not size_reasons
    results.append({
        "rule": "section_size_bound",
        "passed": size_ok,
        "reason": "" if size_ok else " / ".join(size_reasons),
    })

    dump_ok = not dump_reasons
    results.append({
        "rule": "no_raw_dump",
        "passed": dump_ok,
        "reason": "" if dump_ok else " / ".join(dump_reasons),
    })

    enum_ok = not enum_reasons
    results.append({
        "rule": "enumeration_cap",
        "passed": enum_ok,
        "reason": "" if enum_ok else " / ".join(enum_reasons),
    })

    return {"exempt": False, "results": results}
