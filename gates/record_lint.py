"""issue-517 — aggregate, single-pass record lint.

Authoring a record today costs one model turn per gate refusal:
`record_wellformed`/`record_checked_claims`/... in `gates.py` and the four checks
mirrored inline in `on-the-record/hooks/record-claim-guard.sh` each
report only their own first failure, and there is no single command an
author can run before writing to see every violation at once (a
7-refusal loop was observed on issue-512 phase 2).

`lint_record(path)` is a thin aggregator: it calls the existing
`gates.py` check functions (unchanged — this module adds no new rule
logic for anything they already cover) plus four checks lifted here
from `record-claim-guard.sh`'s inline regexes, and unions every
violation into one list. `record-claim-guard.sh` and `gates/ci.py` call
back into this module's functions instead of carrying their own copies,
so each rule's logic lives in exactly one place.

  python3 -m gates.record_lint <record-path>
  python3 -m gates.record_lint            # scans the whole repo
"""
from __future__ import annotations
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# issue #2226: under `python3 -m gates.record_lint`, Python has already
# bound `sys.modules["gates"]` to the implicit namespace package for this
# directory (no `gates/__init__.py`) before this line runs — a namespace
# package has no `__file__`. A bare `import gates` below would then hit
# that cache and silently resolve to the namespace package instead of the
# sibling `gates/gates.py` module (AttributeError on `gates.RECORD_PATH`).
# Evicting `sys.modules["gates"]` to force re-resolution was tried and
# rejected: it fixes this file's own import but leaves "gates" bound to a
# flat module with no `__path__`, so a LATER `gates.<other-submodule>`
# dotted resolution in the same process then breaks instead — reproduced
# via `runpy.run_module("gates.claims")` right after
# `runpy.run_module("gates.record_lint")` in one interpreter. Load the
# sibling file directly by path instead, so neither `sys.modules["gates"]`
# nor `sys.path` resolution is ever disturbed; cache it under a private
# key so every gates/*.py file using this same shape shares one instance
# rather than re-executing gates.py per file.
import importlib.util as _importlib_util
_GATES_IMPL_KEY = "_on_the_record_gates_sibling_impl"
if _GATES_IMPL_KEY not in sys.modules:
    _spec = _importlib_util.spec_from_file_location(
        _GATES_IMPL_KEY, str(Path(__file__).parent / "gates.py"))
    _impl = _importlib_util.module_from_spec(_spec)
    sys.modules[_GATES_IMPL_KEY] = _impl
    _spec.loader.exec_module(_impl)
gates = sys.modules[_GATES_IMPL_KEY]

RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md

# Issue #2241 stage 1: the closed record-kind vocabulary this module's
# advisory-only kind check reads against.
RECORD_KIND_VOCABULARY_PATH = "docs/specs/record-kind-vocabulary.md"

# Re-exported, not reimplemented: `gates/ci.py` and `record-claim-guard.sh`
# call these names on this module instead of holding their own copies —
# single source of truth means the same function object, not a mirror.
record_wellformed_in = gates.record_wellformed_in
record_no_tool_residue_in = gates.record_no_tool_residue_in
record_checked_claims = gates.record_checked_claims


def _repo_root(start: Path) -> Path:
    """Walk up from `start` to the nearest `.git` — the target repo's
    root, not this plugin's own checkout (`gates.ON_THE_RECORD_ROOT`)."""
    p = start.resolve()
    if p.is_file():
        p = p.parent
    for cand in (p, *p.parents):
        if (cand / ".git").exists():
            return cand
    return start.resolve() if start.is_dir() else start.resolve().parent


# ---------------------------------------------------------------------------
# Checks lifted from record-claim-guard.sh's inline mirror (issue #457 Group
# A/B) — the hook used to carry these as a write-time-fragment approximation.
# Here they run against a record's full text, the shape issue #517 requires.
# ---------------------------------------------------------------------------

_UNVERIFIABLE_LINE = re.compile(r"(?im)^\s*[-*]?\s*unverifiable\s*:\s*(.*)$")
_CHECKED_CLAIM_LINE = re.compile(
    r"^\s*[-*]\s*.+—\s*checked:\s*(\S+)\s*—\s*"
    r"result:\s*(pass|fail|unverifiable)(?::\s*(.+))?\s*$")
# issue #1599 misfire class (d): a hyphenated compound like "layer-2/3"
# is not a ratio claim — a ratio's leading digit is never itself part of
# a hyphenated word (`(?<!-)`).
_COUNT_RATIO = re.compile(r"(?<!-)\d+\s*(?:of|/)\s*\d+")
_COUNT_NOUN = re.compile(
    r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?|tests?)\b")
# issue #2219 — a `derived:` citation does not require backtick-wrapping
# to be genuine evidence any more than `canonical:` does (that
# inconsistency was itself part of the false-rejection defect: a bare
# paragraph-lead-in "derived: per the two fenced runs above, ..." is the
# same citation shape as `` `derived: pytest -q` ``, just unquoted).
_CLAIM_DERIVED_TAG = re.compile(r"`?derived:\s*\S")
_PATH_REF = re.compile(
    r"`((?:src|test|tests|docs|gates|on-the-record)/[^`\s]+)`")
# issue #1599 fix 1 — `_PATH_REF` captures a trailing `:line` or
# `:start-end` suffix (e.g. `docs/specs/approvers.md:2`) as part of the
# path; strip it before any filesystem/git existence check.
# issue #1620 misfire class 1 — also strip a comma-separated line list
# (`:60,137`) and a `:name()`/`::name()` function/method locator suffix
# (`::scan_text()`, `:_phase2_record_evidence()`) — both name a real
# file plus a within-file locator, not a broken path.
_LINE_SUFFIX = re.compile(r":\d+(?:[-,]\d+)*$")
_FUNC_SUFFIX = re.compile(r":{1,2}\w+\(\)$")

# issue #1599 fix 4 — a commit-pinned citation (`e7a13db:file/path:151`)
# is itself evidence, independent of a literal `canonical:`/`derived:`
# prefix — a 7-40 char hex commit sha followed by a `path:line` pointer.
_COMMIT_PINNED_CITE = re.compile(
    r"\b[0-9a-f]{7,40}:[\w./\-]+:\d+(?:-\d+)?\b")


def _strip_line_suffix(ref: str) -> str:
    ref = _FUNC_SUFFIX.sub("", ref)
    return _LINE_SUFFIX.sub("", ref)


# issue #2219 — evidence-resolution fix: a `canonical:`/`derived:`-tagged
# check used to require the tag within a fixed 3-8 PHYSICAL line window
# of the claim. Two false-rejection shapes that window misses, both
# reproduced verbatim from a live session (docs/issue-2219 record):
#   (1) the record's own evidence lives further away in the same
#       record — under an earlier `### N. <item>` subsection heading,
#       still describing the same claim, just not within a few lines.
#   (2) markdown soft-wraps one prose sentence across several physical
#       lines ("derived: per the two fenced runs directly above, ...
#       \n...with the full suite still passing 9/9." spans 4 lines) —
#       a same-line-anchored regex never sees the label and the count
#       claim it introduces as connected.
# Fix: (1) scope the evidence search to the claim's enclosing markdown
# section (bounded by the nearest headings, not a fixed line count) —
# still narrower than "the whole record" (PR #1622 already found that
# too permissive for bare fences), and (2) dewrap the window before
# running any label regex against it, so a soft-wrapped sentence reads
# as one line for matching purposes.
_HEADING_LINE = re.compile(r"^\s{0,3}#{1,6}\s")


def _section_bounds(lines: list[str], i: int) -> tuple[int, int]:
    """[lo, hi) bounding the markdown section claim-line `i` sits in:
    from the nearest heading at-or-above `i` (or the top of the record)
    to the next heading after `i` (or the end of the record)."""
    lo = 0
    for j in range(i, -1, -1):
        if _HEADING_LINE.match(lines[j]):
            lo = j
            break
    hi = len(lines)
    for j in range(i + 1, len(lines)):
        if _HEADING_LINE.match(lines[j]):
            hi = j
            break
    return lo, hi


def _dewrap(text: str) -> str:
    """Collapse markdown soft-wrap line breaks so a `canonical:`/
    `derived:`/`acceptance: ... result:` label and the sentence it
    introduces match a single-line-oriented regex even when the
    record's own prose wraps that sentence across several physical
    lines (see the #2219 note above)."""
    return re.sub(r"\n+", " ", text)


def _prose_window(lines: list[str], in_fence: list[bool], lo: int, hi: int) -> str:
    """Dewrapped [lo, hi) text with fenced lines (delimiters and their
    content) excluded — a widened section-scope search must not let a
    `canonical:`/`derived:` string that appears only as illustrative
    example text inside a fenced code block (e.g. documentation of the
    tag format itself) count as a real citation for an unrelated claim
    elsewhere in the section. Only the author's own live prose, never
    quoted/pasted fence content, is evidence."""
    prose = [line for j, line in enumerate(lines[lo:hi]) if not in_fence[lo + j]]
    return _dewrap("\n".join(prose))


# issue #2219 — the project's own documented executed-live convention
# (on-the-record/directive/acceptance-format.md: "acceptance: <command>
# — result: ...") is grounding in its own right when paired with an
# actual fenced raw-output block, independent of any `canonical:`
# wrapper — the record corpus overwhelmingly writes evidence this way,
# not by wrapping every citation in a literal `canonical:` tag.
# Deliberately narrower than "any acceptance: line": `result:` must be
# the last thing on the (dewrapped) line — inline content after
# `result:` is #870's own stricter PASS/FAIL/UNMEASURED path instead
# (t_outcome_claim_with_unbacked_acceptance_prose_is_still_reported
# pins that unbacked "acceptance: ... — result: <prose>" must NOT pass
# through this looser path).
_ACCEPTANCE_RESULT_LEADIN = re.compile(
    r"(?i)\bacceptance:\s*\S.*\bresult:\s*$")


def _prose_paragraphs(lines: list[str], in_fence: list[bool],
                       structural: list[bool]) -> list[tuple[int, int]]:
    """[start, end) index pairs for each maximal run of consecutive
    prose lines — outside a fence, not a fence delimiter itself, not
    blank, not structural (heading/frontmatter/blockquote) — the unit a
    single markdown-wrapped sentence occupies."""
    paras = []
    start = None
    for i, line in enumerate(lines):
        is_prose = (not in_fence[i] and not structural[i]
                    and line.strip() != ""
                    and not line.strip().startswith("```"))
        if is_prose:
            if start is None:
                start = i
        elif start is not None:
            paras.append((start, i))
            start = None
    if start is not None:
        paras.append((start, len(lines)))
    return paras


def _acceptance_evidence_lines(lines: list[str], in_fence: list[bool],
                                structural: list[bool]) -> set[int]:
    """Line indices belonging to a prose paragraph that ends in an
    `acceptance: ... result:` lead-in AND is immediately followed by a
    fenced block — the raw-output pairing this project's acceptance
    convention actually uses."""
    out: set[int] = set()
    for start, end in _prose_paragraphs(lines, in_fence, structural):
        joined = " ".join(lines[start:end])
        if not _ACCEPTANCE_RESULT_LEADIN.search(joined):
            continue
        if end < len(lines) and lines[end].strip().startswith("```"):
            out.update(range(start, end))
    return out

# issue #793 — verify-before-claim: a state/defect-claim marker vocabulary,
# deliberately narrow (known bypassable by synonym choice, same tradeoff
# `_COUNT_RATIO`/`_COUNT_NOUN` already accept — widen from real record
# corpus usage in a later pass, not a closed set assumed complete here).
# issue #1599 misfire class (a)/(e): `(?<![-\w])`/`(?![-\w])` around the
# alternation excludes a marker word that is actually part of a hyphenated
# structural token (`phase-2-complete`, `--pass-through`) rather than a
# standalone claim word.
_STATE_CLAIM_MARKER = re.compile(
    r"(?i)(?<![-\w])(halted|merged|closed|found|confirms?|confirmed|"
    r"is\s+running|is\s+gone|is\s+stale)(?![-\w])")
_CANONICAL_TAG = re.compile(r"`?canonical:\s*(\S.*?)`?\s*$", re.MULTILINE)

# issue #870 — generalized fake-success detection, candidate (a): an
# OUTCOME claim ("requirement met", "done", "PASS", "complete") needs a
# citation that is itself an EXECUTED-LIVE reference, not just any
# `canonical:` tag — #793's own check only requires the tag be non-empty,
# never inspects what kind of source it names (a prior transcript read
# passes identically to a command actually run this turn). Deliberately
# narrow, same known-bypassable-by-synonym tradeoff `_STATE_CLAIM_MARKER`
# already accepts — widen from real record-corpus usage later, not a
# closed set assumed complete here.
_OUTCOME_CLAIM_MARKER = re.compile(
    r"(?i)(?<![-\w])(requirement(?:s)?\s+met|done|PASS(?:es|ed)?|"
    r"complete[ds]?)(?![-\w])")

# issue #1599 misfire class (f) / issue #1614 misfire class 6: a
# counterfactual/conditional/negated sentence ("had this round found...",
# "if it had been merged", "cannot detect", "would still pass") states a
# hypothetical or negation, not an actual outcome/state claim.
_COUNTERFACTUAL_LEADIN = re.compile(
    r"(?i)\bhad\b[^.?!]{0,60}\b(found|confirmed?|merged|closed|halted|"
    r"done|pass(?:es|ed)?|complete[ds]?)\b|\bif\b[^.?!]{0,60}\bhad\b")

# issue #1614 misfire class 6: negated/hypothetical markers not already
# covered by _COUNTERFACTUAL_LEADIN's "had"/"if...had" shape — "cannot",
# "would still", "would not", "never", "might not" etc. preceding a
# claim marker on the same line negate or hedge it into a non-claim.
_NEGATED_HYPOTHETICAL = re.compile(
    r"(?i)\b(cannot|can't|could\s+not|couldn't|would\s+(?:still|not|"
    r"never)|wouldn't|won't|will\s+not|might\s+not|may\s+not|never)\b")


def _is_hypothetical_or_negated(line: str) -> bool:
    return bool(_COUNTERFACTUAL_LEADIN.search(line)
                or _NEGATED_HYPOTHETICAL.search(line))


# issue #1620 misfire class 3: an absence/negation statement ("no
# decisions/ entry needed", "not yet measurable (0/30)") states that a
# path or count does NOT apply / isn't required — not a live claim that
# the path is reachable or the count is asserted fact. Distinct from
# `_NEGATED_HYPOTHETICAL` (negates a claim MARKER like "found"/"merged")
# — this negates the NEED for the path/count itself.
_ABSENCE_NEGATION = re.compile(
    r"(?i)\bno\b.{0,60}?\b(needed|required)\b|"
    r"\bnot\s+(?:yet\s+)?(?:needed|required|applicable|measurable)\b")


def _is_absence_negated(line: str) -> bool:
    return bool(_ABSENCE_NEGATION.search(line))


# issue #1620 misfire class 2: a record explicitly narrating that a path
# was renamed away from, moved from, or deliberately not used is
# describing history/a deviation, not asserting the old path is
# currently reachable.
_PATH_RENAME_NARRATION = re.compile(
    r"(?i)\brenamed\s+(?:away\s+)?(?:from|to)\b|"
    r"\bmoved\s+(?:away\s+)?(?:from|to)\b|"
    r"\bdeliberately\s+not\s+used\b|"
    r"\bno\s+longer\s+(?:used|exists?|at\b)")


def _is_path_rename_narration(line: str) -> bool:
    return bool(_PATH_RENAME_NARRATION.search(line))


# issue #1628 misfire class: a record explicitly narrating that a cited
# path is untracked / out-of-scope / not-in-repo is describing the
# path's state, not asserting it currently resolves on disk — it may
# legitimately no longer exist by the time the record is read back.
_UNTRACKED_OUT_OF_SCOPE_NARRATION = re.compile(
    r"(?i)\buntracked\b|\bout[- ]of[- ]scope\b|\bnot[- ]in[- ]repo\b")


def _is_untracked_out_of_scope_narration(line: str) -> bool:
    return bool(_UNTRACKED_OUT_OF_SCOPE_NARRATION.search(line))


# issue #1614 misfire class 4: historical narration / already-fixed
# interim defects / prior-round results — a claim embedded in a sentence
# that is explicitly narrating the past, not asserting the record's own
# current outcome/state/defect.
_HISTORICAL_LEADIN = re.compile(
    r"(?i)\b(previously|historically|prior\s+round|earlier\s+round|"
    r"used\s+to\s+be|no\s+longer|was\s+once|in\s+an\s+earlier\s+pass|"
    r"in\s+a\s+prior\s+(?:pass|round|session)|at\s+the\s+time|"
    r"back\s+then|before\s+the\s+fix|pre-fix|already[- ]fixed|"
    r"since\s+fixed|has\s+since\s+been\s+fixed)\b")


def _is_historical_narration(line: str) -> bool:
    return bool(_HISTORICAL_LEADIN.search(line))


# issue #1614 misfire class 2: quoted/headed section titles ("What will
# be done" / "What was done") mentioned in prose (e.g. "as documented
# under the '## What was done' section") are literal section-name
# references, not completion claims — even outside a markdown heading
# line or blockquote (those are already masked by
# `_structural_skip_mask`).
_SECTION_TITLE_MENTION = re.compile(
    r"(?i)#*\s*what\s+(?:will\s+be|was)\s+done\b")

# issue #1614 misfire class 1: "pass"/"passed"/"passes" used as a noun
# ("scout pass") or in the argument-passing sense ("passed a dict",
# "pass the result to") is not an outcome claim.
_PASS_NOUN_COMPOUND_LEADIN = re.compile(
    r"(?i)\b(scout|sweep|review|judge|deepening|search|lint|verify)\s*$")
_PASS_ARGUMENT_OBJECT = re.compile(
    r"(?i)\bpass(?:es|ed)?\s+(?:a|an|the|it|this|that|data|dict|object|"
    r"value|values|args?|arguments?|params?|parameters?|control|"
    r"results?|ownership|along)\b")

# issue #1614 misfire class 1: "done" used as a participle attached to a
# following noun ("done work", "the already-done setup") or introduced by
# a temporal lead-in ("once done", "when done", "after done") is not a
# standalone completion claim.
_DONE_ATTRIBUTIVE_LEADIN = re.compile(
    r"(?i)\b(once|when|after|before)\s+(?:it(?:'s|\s+is)\s+)?done\b")
# A small, deliberately closed noun list (same bypassable-by-synonym
# tradeoff the other marker vocabularies in this module accept) — wide
# enough to catch "done work"/"done deal" without treating an ordinary
# continuation ("done and ready to ship") as attributive.
_DONE_FOLLOWED_BY_NOUN = re.compile(
    r"(?i)^\s+(work|deal|setup|task|job|list|stage|thing|item|step)\b")


def _outcome_marker_word_sense_exempt(line: str, m: re.Match) -> bool:
    """Per-occurrence word-sense filter for an `_OUTCOME_CLAIM_MARKER`
    match — distinct from the line-level hedges above because a single
    line can carry both an exempt occurrence and a genuine claim."""
    word = m.group(0).lower()
    start, end = m.span()
    if _SECTION_TITLE_MENTION.search(line[max(0, start - 20):end]):
        return True
    if word.startswith("pass"):
        # Compound-noun sense ("scout pass") — a noun modifier immediately
        # before this occurrence.
        if _PASS_NOUN_COMPOUND_LEADIN.search(line[max(0, start - 20):start]):
            return True
        if _PASS_ARGUMENT_OBJECT.match(line[start:]):
            return True
        return False
    if word == "done":
        lead = line[max(0, start - 20):start]
        if _DONE_ATTRIBUTIVE_LEADIN.search(lead + line[start:end]):
            return True
        if _DONE_FOLLOWED_BY_NOUN.match(line[end:end + 12]):
            return True
        return False
    return False
_EXECUTED_LIVE_CANONICAL = re.compile(
    r"(?i)^(?:gh\s|git\s|pytest\b|python3?\s|npm\s|npx\s|bash\s|sh\s|\./|"
    r"acceptance:\s*\S.*\bresult:\s*(?:PASS|FAIL|UNMEASURED)\b|"
    r"live-fire:\s*\S.*\bresult:\s*(?:allow|deny|log)\b)")

# issue #923 — third executed-live shape, additive to the two above: an
# OBSERVATION/verdict record's own measurement citation. Neither prior
# shape is reachable in an observation role's natural prose — it did not
# run a command *this* turn (path 1) and the record-authoring convention
# this session is given never instructs writing a stand-alone
# backtick-quoted `derived:` tag (path 2, gates/record_lint.py Finding 3
# of docs/issue-923/reports/defect-verification/current-state.md).
# Deliberately narrow vocabulary, same known-bypassable-by-synonym
# tradeoff `_STATE_CLAIM_MARKER`/`_OUTCOME_CLAIM_MARKER` already accept —
# a bare file-read citation ("read this session") must NOT match this,
# only a citation naming the transcript/measurement the observation
# itself produced.
_OBSERVATION_LIVE_CANONICAL = re.compile(
    r"(?i)\b(execution\s+)?(transcript|measurement)\b")

# issue #791 — read-before-claim grounding: a defect/root-cause assertion
# pattern, deliberately narrow (causal/assertive shape, not a bare noun
# mention) so "no bugs found" / "bug tracker" do not trigger — same
# known-bypassable-by-synonym tradeoff the other trigger vocabularies in
# this module already accept.
_DEFECT_CLAIM_MARKER = re.compile(
    r"(?i)\b(is|was|are|were)\s+(a\s+)?(bug|defect|broken)\b"
    r"|\broot\s+cause\s+is\b"
    r"|\bthe\s+(bug|issue|cause)\s+is\b"
    r"|원인은\s*\S*\s*(이다|입니다)"
    r"|문제는\s*\S*\s*(이다|입니다)")

# A `path:line` or `path:start-end` citation, optionally backtick-quoted.
_CITE_FILE_LINE = re.compile(r"`?([\w./\-]+\.\w+):(\d+)(?:-(\d+))?`?")


def _structural_skip_mask(lines: list[str]) -> list[bool]:
    """issue #1599 misfire classes (a)/(b)/(c): a line inside YAML
    frontmatter, a markdown heading, or a blockquote (`>`, quoting
    another document's claim) is structure or quotation, not the
    author's own prose claim — mask it out of every claim-marker check."""
    mask = [False] * len(lines)
    in_frontmatter = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_frontmatter = True
            mask[i] = True
            continue
        if in_frontmatter:
            mask[i] = True
            if stripped == "---":
                in_frontmatter = False
            continue
        if line.lstrip().startswith("#") or line.lstrip().startswith(">"):
            mask[i] = True
    return mask


def outcome_claim_citation_check(text: str) -> list[str]:
    """issue #870 mirror: an OUTCOME claim ("requirement(s) met", "done",
    "PASS(es/ed)", "complete(d)") needs, somewhere in its enclosing
    markdown section (issue #2219 — was a fixed 3-line window; see the
    module note above `_section_bounds`), a `canonical:`/`derived:` tag
    whose cited source is itself an executed-live reference (a command
    string, an `acceptance: <command> — result: ...` line, or — issue
    #923 — a citation naming the transcript/measurement an
    observation/verdict record's own live run produced), or an
    `acceptance: ... — result:` lead-in immediately followed by a fenced
    block (issue #2219 — the project's own acceptance-format convention
    is executed-live evidence in its own right) — not a bare file-read/
    summary citation, which satisfies #793's own state-claim check but
    does not prove the claimed outcome was actually re-run (or, for an
    observation record, actually measured) against the current state.
    Fail-closed: no qualifying citation -> refused."""
    bad = []
    lines = text.splitlines()
    in_fence = [False] * len(lines)
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
    structural = _structural_skip_mask(lines)
    acceptance_evidence = _acceptance_evidence_lines(lines, in_fence, structural)
    for i, line in enumerate(lines):
        if in_fence[i] or structural[i]:
            continue
        matches = [m for m in _OUTCOME_CLAIM_MARKER.finditer(line)
                   if not _outcome_marker_word_sense_exempt(line, m)]
        if not matches:
            continue
        if _is_hypothetical_or_negated(line) or _is_historical_narration(line):
            continue
        # issue #2219: the evidence search scope is the claim's whole
        # enclosing section, not a fixed line count — see module note.
        lo, hi = _section_bounds(lines, i)
        window = _prose_window(lines, in_fence, lo, hi)
        m = _CANONICAL_TAG.search(window)
        cited = m.group(1).strip().strip("`") if m and m.group(1).strip() else ""
        has_executed_live = bool(cited) and bool(
            _EXECUTED_LIVE_CANONICAL.search(cited))
        # A `derived: <command>` tag (#333's own citation for a count
        # claim) is itself a command reference — accept it as a sibling
        # executed-live source, same "don't double-demand a citation for
        # what's already cited" treatment `canonical_source_claim_check`
        # gives count claims.
        has_derived = bool(_CLAIM_DERIVED_TAG.search(window))
        has_observation_live = bool(cited) and bool(
            _OBSERVATION_LIVE_CANONICAL.search(cited))
        # issue #1599 fix 4 — a commit-pinned citation is evidence in its
        # own right, independent of a literal `canonical:`/`derived:` tag.
        has_pinned = bool(_COMMIT_PINNED_CITE.search(window))
        # issue #2219 — an `acceptance: ... — result:` lead-in paired
        # with an immediately-following fence, anywhere in this section.
        has_acceptance_result = any(
            lo <= j < hi for j in acceptance_evidence)
        if not (has_executed_live or has_derived or has_observation_live
                or has_pinned or has_acceptance_result):
            bad.append(
                "레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): "
                f"{line.strip()!r} — 'requirement met/done/PASS/complete' "
                "류의 결과 주장을 하면서 같은 섹션 안에 실행-라이브 인용"
                "(`gh ...`/`pytest ...`/`python3 ...`/"
                "`acceptance: <command> — result: ...`로 시작하는 "
                "`canonical:` 태그, 또는 관측/verdict 레코드라면 자신이 "
                "이번 턴에 만든 transcript/measurement를 지칭하는 "
                "`canonical:` 태그)이 없다 — 파일을 읽었다는 인용만으로는 "
                "부족하다. 통과하려면 같은 섹션(가장 가까운 헤딩 사이) 안에 "
                "실행-라이브 `canonical:`/`derived:` 태그, `acceptance: "
                "<command> — result:` 바로 다음의 코드펜스, 또는 커밋-고정 "
                "인용(`<sha>:<path>:<line>`)을 두면 된다.")
    return bad


_SKILL_VERDICT_LINE = re.compile(
    r"(?i)^\s*[-*]?\s*skill-verdict\s*:\s*(.+?)\s*—[ \t]*(.*?)\s*$")


_SKILL_VERDICT_APPLIED = re.compile(r"(?i)^applied\s*:\s*(.*)$")
_SKILL_VERDICT_INVOKED_MARKER = re.compile(r"(?i)^invoked\s*;")


def skill_verdict_reason_check(text: str, mounted: list[str]) -> list[str]:
    """issue #2039 mirror: a record must carry one `skill-verdict: <name>
    — applied: ... | not-applicable: ...` line per name in `mounted`,
    each with non-empty content after the dash. Shape only — never judges
    whether the applied/not-applicable content is actually correct,
    matching #2039's frozen skills-guidance-only boundary. `mounted`
    empty is a no-op (zero-mounted-skill sessions stay byte-unaffected).

    Issue #2153: despite the parameter's name, `skill-verdict-guard.sh`
    (the only session-side caller) now passes the subset of mounted
    skills this session actually invoked via the Skill tool, not every
    mounted name — a mounted-but-never-invoked skill owes no line. This
    function itself stays generic over whatever name list it is given.

    Issue #2062: an `applied:` line must also carry an invocation
    marker — its free text (after the `applied:` label) must start with
    `invoked;` — proving the Skill tool was actually called before the
    skill was applied. `not-applicable:` lines and zero-skill sessions
    are unaffected (shape-only, never judging the marker's truth)."""
    bad: list[str] = []
    if not mounted:
        return bad
    found: dict[str, str] = {}
    for line in text.splitlines():
        m = _SKILL_VERDICT_LINE.match(line)
        if not m:
            continue
        name, content = m.group(1).strip(), m.group(2).strip()
        if name not in found:
            found[name] = content
    for name in mounted:
        if name not in found:
            bad.append(
                "마운트된 스킬에 skill-verdict 줄이 없다 (issue #2039): "
                f"{name!r} — `skill-verdict: {name} — applied: ... | "
                "not-applicable: ...` 줄을 레코드에 남겨야 한다.")
            continue
        content = found[name]
        if not content:
            bad.append(
                "skill-verdict 줄에 이유가 없다 (issue #2039): "
                f"{name!r} — 대시 뒤에 applied/not-applicable 내용이 비어 "
                "있다.")
            continue
        applied_m = _SKILL_VERDICT_APPLIED.match(content)
        if applied_m and not _SKILL_VERDICT_INVOKED_MARKER.match(
                applied_m.group(1).strip()):
            bad.append(
                "applied: 줄에 invoke-before-apply 마커가 없다 (issue "
                f"#2062): {name!r} — Skill 도구로 호출했다는 증거로 "
                "`applied: invoked; ...` 형태로 자유 텍스트 맨 앞에 "
                "`invoked;` 를 붙여야 한다.")
    return bad


_ZERO_INVOCATION_SUMMARY_LINE = re.compile(
    r"(?i)other mounted skills\s*:\s*not triggered")


def zero_invocation_summary_check(text: str, mounted: list[str]) -> list[str]:
    """Issue #2893: when a session mounts >= 1 skill and invokes NONE of
    them, #2153's narrowing means no per-skill `skill-verdict:` line is
    owed for any of them -- but that left "correctly judged none
    applicable" and "never considered the mounted list at all" producing
    the exact same (silent) record, indistinguishable after the fact.
    Requires exactly one summary line (`other mounted skills: not
    triggered`, the convention `_SKILL_VERDICT_PROSE` already documents)
    somewhere in the record when `mounted` is non-empty. Shape only --
    never a judgment of whether the skip itself was correct, mirroring
    `skill_verdict_reason_check`'s own frozen boundary. `mounted` empty is
    a no-op (zero-mounted-skill sessions stay byte-unaffected)."""
    if not mounted:
        return []
    if _ZERO_INVOCATION_SUMMARY_LINE.search(text):
        return []
    return [
        "마운트된 스킬을 하나도 호출하지 않았는데 레코드에 요약 줄이 "
        "없다 (issue #2893): `other mounted skills: not triggered` 한 "
        "줄을 레코드에 남겨야 한다 — 어떤 스킬이 맞았어야 한다는 뜻이 "
        "아니라, 이번 세션이 마운트된 스킬 목록을 실제로 검토했다는 "
        "사실만 기록한다."
    ]


def record_skill_verdicts_in(work: Path, mounted: list[str]) -> list[str]:
    """CI/diff-scoped wrapper around `skill_verdict_reason_check`,
    mirroring `gates.py`'s `(work, cfg)`-shaped checks — used by both
    `gates/ci.py` and `on-the-record/hooks/skill-verdict-guard.sh`. The
    hook is the only caller that derives `mounted` from a transcript
    scan; `mounted` is taken as an explicit argument here because CI has
    no transcript to read it from."""
    if not mounted:
        return []
    root = work / "work" if (work / "work").exists() else work
    try:
        files = gates.changed_files(root)
    except RuntimeError as e:
        return [str(e)]
    bad: list[str] = []
    for f in files:
        if not RECORD_PATH.match(f):
            continue
        record_file = root / f
        text = (record_file.read_text(encoding="utf-8-sig", errors="replace")
                if record_file.exists() else "")
        bad += [f"{f}: {v}" for v in skill_verdict_reason_check(text, mounted)]
    return bad


def unverifiable_reason_check(text: str) -> list[str]:
    """#310/#331 mirror: an `unverifiable:` escape line needs a reason."""
    bad = []
    for m in _UNVERIFIABLE_LINE.finditer(text):
        if not m.group(1).strip():
            bad.append(
                "`unverifiable:` 줄에 이유가 없다 (issue #310) — "
                "`unverifiable: <이유>` 형태로 왜 기계 검사가 불가능한지 "
                "적어야 한다. 통과하려면 콜론 뒤에 구체적인 이유 문구를 "
                "채우면 된다 (예: `unverifiable: 주관적 UX 판단이라 기계로 "
                "검사할 수 없다`).")
    return bad


_FRONTMATTER_KIND_LINE = re.compile(r"(?i)^\s*kind\s*:\s*(\S.*?)\s*$")
_VOCAB_BULLET = re.compile(r"^-\s*`([a-z0-9][a-z0-9-]*)`", re.MULTILINE)


def _load_record_kind_vocabulary(root: Path) -> set[str] | None:
    """Parses the closed vocabulary out of `RECORD_KIND_VOCABULARY_PATH`'s
    own bullet list (`` - `value` — description ``). `None` when the spec
    file itself is absent — an empty state (no vocabulary landed yet),
    never an error; the caller treats `None` the same as "nothing to
    check against"."""
    path = root / RECORD_KIND_VOCABULARY_PATH
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    vocab = {m.group(1) for m in _VOCAB_BULLET.finditer(text)}
    return vocab or None


def _frontmatter_kind_value(text: str) -> str | None:
    """The `kind:` value from a record's own leading `---` frontmatter
    block only — never a `kind:`-shaped mention inside the record's
    prose body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = _FRONTMATTER_KIND_LINE.match(line)
        if m:
            return m.group(1).strip().strip("\"'")
    return None


def record_kind_vocabulary_check(root: Path, text: str) -> list[str]:
    """issue #2241 stage 1 — ADVISORY ONLY. Deliberately not called from
    `lint_record()`'s aggregation below (this repo's DEMOTE convention for
    a brand-new check: land it, prove it fires correctly against the
    closed vocabulary, and only a later stage — 3 or 5, per
    `docs/issue-2241/proposals/` — wires it into a blocking path once the
    `kind:` field itself becomes load-bearing for observer verification).
    Flags a `kind:` frontmatter value that is not in the closed vocabulary
    `docs/specs/record-kind-vocabulary.md` formalizes. No vocabulary file,
    or no `kind:` line in this record, is a legitimate empty state (a
    record predating this stage, or the vocabulary spec not yet landed in
    this target repo) — never an advisory, per that spec's additive-only
    constraint."""
    vocab = _load_record_kind_vocabulary(root)
    if vocab is None:
        return []
    value = _frontmatter_kind_value(text)
    if value is None or value in vocab:
        return []
    return [
        "레코드의 kind: 값이 닫힌 어휘 밖이다 (issue #2241 stage 1, advisory "
        f"— 아무것도 막지 않는다): {value!r} — "
        f"{RECORD_KIND_VOCABULARY_PATH} 에 정의된 값 중 하나를 쓰거나 그 "
        "문서에 새 값을 추가하라."
    ]


def checked_claim_reason_check(text: str) -> list[str]:
    """#331 mirror: an Acceptance-verification `unverifiable` result needs
    a reason."""
    bad = []
    for ln in text.splitlines():
        cm = _CHECKED_CLAIM_LINE.match(ln)
        if not cm:
            continue
        result, reason = cm.group(2), cm.group(3)
        if result == "unverifiable" and not (reason and reason.strip()):
            bad.append(
                "Acceptance verification 의 `unverifiable` 항목에 이유가 "
                f"없다 (issue #331): {ln.strip()!r} — 통과하려면 "
                "`— checked: X — result: unverifiable: <이유>` 형태로 "
                "콜론 뒤에 이유를 붙이면 된다.")
    return bad


# issue #1620 misfire class 4: a tally whose computation is spelled out
# inline right next to it — a percentage shown alongside the raw
# fraction (e.g. "33.3% precision (4 TP / 12)"), or an explicit
# multiplication/sum shown with an `=` (e.g. "9 keywords x
# (lower/capitalize/upper) = 27 cases") — is self-evidencing: the reader
# can see how the number was derived without a separate
# `derived:`/fence citation. PR #1622 review: the signal must live on
# the count's own line — a `%` there, or digits directly adjacent to an
# `=` (not any unrelated `=` like "set FOO=bar" or "key=value").
_INLINE_COMPUTED_LEADIN = re.compile(
    r"\d+(?:\.\d+)?%|\d\s*=|=\s*\d")

# PR #1622 review finding 1: a fence exemption must be scoped to a fence
# that CLOSES within a few lines above the count, not "anywhere earlier
# in the file" (that blanket form suppressed every count below the
# first fence in the whole record).
_FENCE_PROXIMITY_LINES = 5


def bare_count_claim_check(text: str) -> list[str]:
    """#333 mirror: a bare "N of M"/"N items" count needs `derived:` or a
    code-fence reproduction — fences are excluded. issue #1620 also
    excludes: a count whose computation is shown inline (a percentage on
    the same line), one backed by a fenced raw-output block shortly
    above it, one carrying a `canonical:` citation on its own evidence
    line, and an absence/negation statement ("not yet measurable
    (0/30)")."""
    bad = []
    lines = text.splitlines()
    structural = _structural_skip_mask(lines)
    fence_flags = [False] * len(lines)
    fence_close_lines = []
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            was_open = fence
            fence = not fence
            fence_flags[i] = True
            if was_open and not fence:
                fence_close_lines.append(i)
            continue
        fence_flags[i] = fence
    for i, line in enumerate(lines):
        if fence_flags[i] or structural[i]:
            continue
        wrap_window = " ".join(lines[max(0, i - 1):min(len(lines), i + 2)])
        if _is_absence_negated(wrap_window):
            continue
        for pat in (_COUNT_RATIO, _COUNT_NOUN):
            for cm in pat.finditer(line):
                tail = line[cm.end():]
                if _CLAIM_DERIVED_TAG.match(tail.lstrip()):
                    continue
                lo = max(0, i - 6)
                evidence_window = "\n".join(lines[lo:i + 1])
                if _CANONICAL_TAG.search(evidence_window):
                    continue
                if _INLINE_COMPUTED_LEADIN.search(line):
                    continue
                # "backed by a fenced raw-output block above" (issue
                # #1620 class 4), scoped per PR #1622 review: the fence
                # must CLOSE within a few lines above the count, not
                # merely appear anywhere earlier in the record.
                if any(
                    0 <= i - j <= _FENCE_PROXIMITY_LINES
                    for j in fence_close_lines if j < i
                ):
                    continue
                bad.append(
                    "레코드에 근거 없는 개수 주장 (issue #333): "
                    f"{line.strip()!r} — 숫자가 코드펜스 재현이나 "
                    "`derived: ...` 인용 없이 그냥 타이핑되어 있다. "
                    "통과하려면 숫자 바로 뒤에 `derived: <command>`(백틱 "
                    "유무 무관)를 붙이거나, 위 5줄 이내에 닫히는 코드펜스를 "
                    "두거나, 같은 줄에 `%`/`=` 계산식을 보이거나, 가까이에 "
                    "`canonical: ...` 태그를 두면 된다.")
                break
    return bad


def orphaned_path_reference_check(root: Path, text: str) -> list[str]:
    """#330 mirror: a backtick-quoted relative path that resolves nowhere
    in the working tree. issue #1620 also excludes: a path cited while
    explicitly narrating that it was renamed/moved away or deliberately
    not used (deviation narration, not a live reachability claim), and
    an absence/negation statement ("no decisions/ entry needed")."""
    bad = []
    lines = text.splitlines()
    structural = _structural_skip_mask(lines)
    line_starts = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1
    for m in _PATH_REF.finditer(text):
        line_idx = 0
        for idx, start in enumerate(line_starts):
            if start <= m.start():
                line_idx = idx
            else:
                break
        if line_idx < len(structural) and structural[line_idx]:
            continue
        window = " ".join(
            lines[max(0, line_idx - 1):min(len(lines), line_idx + 2)])
        if (_is_path_rename_narration(window) or _is_absence_negated(window)
                or _is_untracked_out_of_scope_narration(window)):
            continue
        ref = _strip_line_suffix(m.group(1))
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if not (root / ref).exists():
            bad.append(
                "레코드가 존재하지 않는 경로를 참조한다 (issue #330): "
                f"`{ref}` — 리치(reach)가 끊긴 참조다. 통과하려면 실제로 "
                "존재하는 경로를 인용하거나, 이름이 바뀌었다는 서술(`renamed "
                "from/to`, `moved from/to`, `untracked`)을 근처에 남기면 "
                "된다.")
    return bad


def git_tracked_path_reference_check(root: Path, text: str,
                                      record_rel: str | None = None) -> list[str]:
    """issue #1085 mirror: a backtick-quoted path that IS present in the
    working tree (so #330's `orphaned_path_reference_check` lets it
    through) but was never added in any commit on any branch — a path
    present at write time only because it is an untracked, never-staged
    working-tree artifact. Distinct from #330's "resolves nowhere on
    disk at all" case: this fires only for paths that exist on disk
    right now yet have no `git log --all --diff-filter=A` history.
    Self-citation of the record currently being written is exempt (the
    file being authored this turn cannot yet have history for its own
    write)."""
    bad = []
    seen: set[str] = set()
    for m in _PATH_REF.finditer(text):
        ref = _strip_line_suffix(m.group(1))
        if ref in seen:
            continue
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if record_rel is not None and ref == record_rel:
            continue
        if not (root / ref).exists():
            continue  # #330's job, not this check's
        seen.add(ref)
        try:
            out = subprocess.run(
                ["git", "log", "--all", "--diff-filter=A", "--name-only",
                 "--", ref],
                cwd=str(root), capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue  # no git available — not this check's problem
        if out.returncode != 0:
            continue
        if not out.stdout.strip():
            bad.append(
                "레코드가 git 이력에 한 번도 커밋된 적 없는 경로를 인용한다 "
                f"(issue #1085): `{ref}` — 작업 트리에는 존재하지만 "
                "`git log --all --diff-filter=A` 결과가 비어 있다 — "
                "커밋된 적 없는 임시 워킹트리 파일이다.")
    return bad


def canonical_source_claim_check(text: str) -> list[str]:
    """issue #793 mirror: a state/defect-claim line (session output "found",
    session/PR/board state "halted|merged|closed|is running|is gone|is
    stale", or a bare count claim) needs, somewhere in its enclosing
    markdown section (issue #2219 — was a fixed 3-line window; see the
    module note above `_section_bounds`), a `canonical:`/`derived:
    <what was read>` tag citing the actual record/diff, raw
    ground-truth command output, or file:line-context read, or an
    `acceptance: ... — result:` lead-in immediately followed by a
    fenced block (issue #2219) — not a summary/grep/watcher signal with
    nothing named."""
    bad = []
    lines = text.splitlines()
    in_fence = [False] * len(lines)
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
    structural = _structural_skip_mask(lines)
    acceptance_evidence = _acceptance_evidence_lines(lines, in_fence, structural)
    for i, line in enumerate(lines):
        if in_fence[i] or structural[i]:
            continue
        if _is_hypothetical_or_negated(line) or _is_historical_narration(line):
            continue
        marker_claim = bool(_STATE_CLAIM_MARKER.search(line))
        count_claim = not marker_claim and bool(
            _COUNT_RATIO.search(line) or _COUNT_NOUN.search(line))
        if not (marker_claim or count_claim):
            continue
        # issue #2219: the evidence search scope is the claim's whole
        # enclosing section, not a fixed line count — see module note.
        lo, hi = _section_bounds(lines, i)
        window = _prose_window(lines, in_fence, lo, hi)
        m = _CANONICAL_TAG.search(window)
        has_canonical = bool(m and m.group(1).strip())
        # issue #2219 — `derived:` is now a general sibling tag to
        # `canonical:` for any claim type, not just a count claim's own
        # citation (it was already treated as evidence-equivalent for
        # counts; a state/defect claim citing the same command deserves
        # the same treatment).
        has_derived = bool(_CLAIM_DERIVED_TAG.search(window))
        # issue #1599 fix 4 — a commit-pinned citation is evidence in its
        # own right, independent of a literal `canonical:` prefix.
        has_pinned = bool(_COMMIT_PINNED_CITE.search(window))
        # issue #2219 — an `acceptance: ... — result:` lead-in paired
        # with an immediately-following fence, anywhere in this section.
        has_acceptance_result = any(
            lo <= j < hi for j in acceptance_evidence)
        if not (has_canonical or has_derived or has_pinned
                or has_acceptance_result):
            bad.append(
                "레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): "
                f"{line.strip()!r} — skill output / session·PR·board 상태 / "
                "결함을 주장하면서 같은 섹션 안에 `canonical: <읽은 소스>` "
                "태그가 없다 — 요약이나 grep/watcher 신호가 아니라 실제 "
                "레코드/diff, raw ground truth, 또는 file:line 컨텍스트를 "
                "인용해야 한다. 통과하려면 같은 섹션(가장 가까운 헤딩 사이) "
                "안에 `canonical: ...` 또는 `derived: ...` 태그를 두거나, "
                "`acceptance: <command> — result:` 바로 다음에 코드펜스로 "
                "실행 결과를 붙이면 된다.")
    return bad


def _normalize_ws(s: str) -> str:
    return " ".join(s.split())


def _verbatim_match(file_path: Path, start: int, end: int,
                     quote_lines: list[str]) -> bool:
    """Does `quote_lines` (whitespace-normalized, joined) appear as a
    contiguous substring of `file_path`'s content around lines
    [start, end] (with a small tolerance window)? Catches a fabricated or
    single-line-repeated-to-look-multiline excerpt — those don't appear
    verbatim in the real file."""
    try:
        lines = file_path.read_text(
            encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return False
    lo = max(0, start - 1 - 5)
    hi = min(len(lines), (end or start) + 5)
    window_text = _normalize_ws("\n".join(lines[lo:hi]))
    quote_text = _normalize_ws("\n".join(quote_lines))
    return bool(quote_text) and quote_text in window_text


def defect_claim_grounding_check(root: Path, text: str) -> list[str]:
    """issue #791 mirror: a defect/root-cause claim needs grounded
    evidence, not a bare grep/keyword hit — either (a) a fenced quote of
    >=3 contiguous lines that verbatim-matches (whitespace-normalized)
    the cited `file:line` range in the working tree, or (b) a
    `derived: <command>` fenced reproduction, the same non-file citation
    convention `bare_count_claim_check` already accepts. Grep/keyword
    search stays legal for locating a candidate; it is not itself
    evidence for the claim."""
    bad = []
    lines = text.splitlines()
    n = len(lines)
    in_fence = [False] * n
    fence_id = [-1] * n
    fence_lines: dict[int, list[str]] = {}
    fence = False
    fid = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            if not fence:
                fid += 1
                fence_lines[fid] = []
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
        if fence:
            fence_id[i] = fid
            fence_lines[fid].append(line)

    structural = _structural_skip_mask(lines)
    for i, line in enumerate(lines):
        if in_fence[i] or structural[i]:
            continue
        if not _DEFECT_CLAIM_MARKER.search(line):
            continue
        if _is_hypothetical_or_negated(line) or _is_historical_narration(line):
            continue

        lo = max(0, i - 8)
        hi = i + 1
        window_idx = range(lo, hi)
        window_text = "\n".join(lines[lo:hi])
        fids_in_window = {fence_id[j] for j in window_idx
                           if in_fence[j] and fence_id[j] != -1}

        # (b) derived: command reproduction — a non-file citation, same
        # bar bare_count_claim_check already requires: the tag plus a
        # fenced block, both present in the same window.
        grounded = bool(_CLAIM_DERIVED_TAG.search(window_text)) and bool(
            fids_in_window)

        # (a) verbatim file:line citation
        if not grounded:
            for m in _CITE_FILE_LINE.finditer(window_text):
                path_str, start_s, end_s = m.group(1), m.group(2), m.group(3)
                fpath = root / path_str
                if not fpath.is_file():
                    continue
                start = int(start_s)
                end = int(end_s) if end_s else start
                for fidx in fids_in_window:
                    quote = [l for l in fence_lines.get(fidx, []) if l.strip()]
                    if len(quote) < 3:
                        continue
                    if _verbatim_match(fpath, start, end, quote):
                        grounded = True
                        break
                if grounded:
                    break

        if not grounded:
            bad.append(
                "레코드에 근거 없는 결함/원인 주장 (issue #791): "
                f"{line.strip()!r} — 결함/원인 주장에는 인용된 file:line "
                "범위와 축약없이(whitespace만 정규화) 일치하는 3줄 이상의 "
                "펜스 인용, 또는 `derived: <command>` 재현이 필요하다 — "
                "grep/키워드 히트 하나만으로는 근거가 되지 않는다. 통과하려면 "
                "인용한 file:line 범위와 일치하는 3줄 이상의 코드펜스를 "
                "근처(8줄 이내)에 두거나, `derived: <command>` 태그와 "
                "코드펜스를 함께 두면 된다.")
    return bad


# ---------------------------------------------------------------------------
# issue #2331 — machine-verified derived figures. Four live instances in one
# day (#2207: `wc -l` claim off by 11; #2244: a fenced pytest transcript's
# "N passed" tally wrong by 93-vs-79; #2295: four `path:line` citations all
# shifted +35 lines; the orchestrator's own stale `spawn.py:3930` citation)
# each cost a full observer round to catch a number a session TYPED instead
# of re-deriving. The checks below re-run/re-compute a narrow, explicitly
# hermetic (no side effects, no shell, no arbitrary code execution) subset
# of derived-figure shapes and a path:line citation's bounds/content,
# refusing on mismatch and naming the actual value — never silently, an
# `derived-unverified: <why>` line anywhere in the same markdown section
# (issue #2219's own section-scoping convention, `_section_bounds` above)
# opts a specific claim out.
# ---------------------------------------------------------------------------

def _safe_repo_path(root: Path, path_str: str) -> Path | None:
    """A relative, in-repo path only — never an absolute path or one that
    escapes `root` via `..`. Recomputing a derived figure must stay
    hermetic to the record's own committed working tree, not follow a
    citation out to arbitrary filesystem state (an absolute-path
    `` `wc -l /tmp/...` `` citation would otherwise resolve against
    whatever happens to be at that path on the machine running the gate,
    a real leak this issue's own replay fixture surfaced against a live
    repo record: `/tmp/pr2308-review/branch/spawn.py`, a leftover
    execution-observation worktree, not this repo)."""
    if path_str.startswith("/") or ".." in Path(path_str).parts:
        return None
    candidate = (root / path_str).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


_DERIVED_UNVERIFIED_MARK = re.compile(r"(?i)derived-unverified\s*:\s*\S")


def _is_derived_unverified(lines: list[str], in_fence: list[bool],
                            line_idx: int) -> bool:
    """issue #2331 ask 3: a `derived-unverified: <why>` line anywhere in
    the claim's enclosing markdown section opts that section's figures out
    of recomputation — visible (the reader sees the escape and the reason)
    rather than the check silently never having existed."""
    lo, hi = _section_bounds(lines, line_idx)
    window = _prose_window(lines, in_fence, lo, hi)
    return bool(_DERIVED_UNVERIFIED_MARK.search(window))


def _index_fences(lines: list[str]):
    """Shared fence scan for the two recompute checks below: `in_fence[i]`
    (delimiters included), and `fence_content[fid]` -> that fence's inner
    lines (delimiters excluded), keyed by an id assigned in document
    order. Deliberately not merged into the several near-identical inline
    scans elsewhere in this module (`outcome_claim_citation_check` et al.)
    — those are pre-existing and out of this issue's scope."""
    in_fence = [False] * len(lines)
    fence_content: dict[int, list[str]] = {}
    fence = False
    fid = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            if not fence:
                fid += 1
                fence_content[fid] = []
            fence = not fence
            in_fence[i] = True
            continue
        in_fence[i] = fence
        if fence:
            fence_content[fid].append(line)
    return in_fence, fence_content


def _offset_to_line(line_starts: list[int], offset: int) -> int:
    lo = 0
    for idx, start in enumerate(line_starts):
        if start <= offset:
            lo = idx
        else:
            break
    return lo


# issue #2331 replay 1 (#2207): `derived: \`wc -l spawn.py\` before = 3347,
# after = 2929 ...` — the record's own re-derivable "after" figure (the
# "before" figure names a different git ref's content, not the working
# tree, and is out of this hermetic check's scope) was off by 11 against
# the file actually committed.
_WC_L_CMD = re.compile(r"`wc -l ([\w./\-]+)`")
_WC_L_AFTER = re.compile(r"(?i)after\s*=\s*(\d+)")
_WC_L_BARE_EQ = re.compile(r"=\s*(\d+)")


def wc_l_recompute_check(root: Path, text: str) -> list[str]:
    """issue #2331: a `` `wc -l <path>` `` derived-figure claim is cheap
    and hermetic — re-count the file actually in the working tree and
    refuse if the claimed ("after ="/bare "=") figure disagrees, naming
    the real count. A path this check cannot resolve, or a claim with no
    parseable number nearby, is silently out of scope (not this check's
    finding)."""
    bad = []
    lines = text.splitlines()
    in_fence, _ = _index_fences(lines)
    structural = _structural_skip_mask(lines)
    line_starts, pos = [], 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1
    for m in _WC_L_CMD.finditer(text):
        line_idx = _offset_to_line(line_starts, m.start())
        if in_fence[line_idx] or structural[line_idx]:
            continue
        if _is_derived_unverified(lines, in_fence, line_idx):
            continue
        path_str = m.group(1)
        fpath = _safe_repo_path(root, path_str)
        if fpath is None or not fpath.is_file():
            continue  # #330's job (or an out-of-repo path), not this check's
        # Same physical line only (issue #2331 hunt finding): a wider
        # forward window can cross into a LATER, unrelated sentence — this
        # repo's own docs/issue-2207/reports/execution-observation.md
        # quotes "after = 2929" several lines below an unrelated `wc -l`
        # citation while narrating that PR's own defect, and a 200-char
        # lookahead wrongly paired the two.
        col = m.end() - line_starts[line_idx]
        tail = lines[line_idx][col:]
        num_m = _WC_L_AFTER.search(tail) or _WC_L_BARE_EQ.search(tail)
        if not num_m:
            continue
        claimed = int(num_m.group(1))
        try:
            actual = sum(1 for _ in fpath.open(
                encoding="utf-8-sig", errors="replace"))
        except OSError:
            continue
        if claimed != actual:
            bad.append(
                "레코드의 `wc -l` 파생 수치가 실제와 다르다 (issue #2331): "
                f"`{path_str}` 에 대해 {claimed}로 주장했지만 지금 작업 "
                f"트리를 다시 세면 {actual}이다 — 통과하려면 숫자를 "
                f"{actual}로 고치거나, 같은 섹션에 `derived-unverified: "
                "<이유>` 를 남기면 된다.")
    return bad


# issue #2331 replay 2 (#2244): a fenced `$ ... pytest ...` transcript
# whose "N passed" summary line was typed as 93 when the targeted files
# actually collect 79 tests — reproduced here via the same cheap proxy the
# real observer used (module-level `def test_`/`def t_` count), not a
# live pytest re-run (a full suite run is neither cheap nor within this
# gate's <1s budget). Deliberately narrow: skipped whenever `parametrize`
# or a unittest-style `class ...Test` appears in a named file, since
# either can make the collected count diverge from a flat function count
# — that shape stays ungraded rather than mis-graded.
_FENCE_PYTEST_CMD_LINE = re.compile(
    r"^\$\s*(?:python3?\s+-m\s+)?pytest\s+(.+)$")
_FENCE_PASSED_SUMMARY = re.compile(r"(?:^|\s)(\d+)\s+passed\b")
_PARAMETRIZE_OR_CLASS = re.compile(
    r"@pytest\.mark\.parametrize|^\s*class\s+\w*[Tt]est", re.MULTILINE)
_MODULE_TEST_DEF = re.compile(r"(?m)^def\s+(?:t_|test_)\w*\s*\(")


def pytest_count_recompute_check(root: Path, text: str) -> list[str]:
    """issue #2331: a fenced `$ pytest <files...>` transcript's own
    "N passed" summary is cheap and hermetic to re-derive from the named
    files' module-level test-function count — refuse a mismatch, naming
    the real count."""
    bad = []
    lines = text.splitlines()
    in_fence, fence_content = _index_fences(lines)
    for fid, flines in fence_content.items():
        cmd = None
        for fl in flines:
            m = _FENCE_PYTEST_CMD_LINE.match(fl.strip())
            if m:
                cmd = m.group(1)
                break
        if cmd is None:
            continue
        block_text = "\n".join(flines)
        summary_m = _FENCE_PASSED_SUMMARY.search(block_text)
        if not summary_m:
            continue
        claimed = int(summary_m.group(1))
        targets = [tok for tok in cmd.split() if tok.endswith(".py")]
        if not targets:
            continue
        contents = []
        for tok in targets:
            fp = _safe_repo_path(root, tok)
            if fp is None or not fp.is_file():
                contents = None
                break
            src = fp.read_text(encoding="utf-8-sig", errors="replace")
            if _PARAMETRIZE_OR_CLASS.search(src):
                contents = None
                break
            contents.append(src)
        if not contents:
            continue
        # Scope the derived-unverified exemption to this fence's own
        # opening line, same section-window convention as the other
        # checks in this module.
        open_idx = next(
            (i for i, ln in enumerate(lines)
             if ln.strip().startswith("```") and in_fence[i]
             and i > 0 and not in_fence[i - 1]), 0)
        if _is_derived_unverified(lines, in_fence, open_idx):
            continue
        actual = sum(len(_MODULE_TEST_DEF.findall(c)) for c in contents)
        if actual != claimed:
            bad.append(
                "레코드의 펜스 pytest 결과 수치가 실제와 다르다 (issue "
                f"#2331): `{cmd.strip()}` 결과로 {claimed} passed 를 "
                f"주장했지만, 인용된 파일들의 모듈-레벨 테스트 함수를 다시 "
                f"세면 {actual}개다 — 통과하려면 숫자를 {actual}로 고치거나, "
                "같은 섹션에 `derived-unverified: <이유>` 를 남기면 된다.")
    return bad


# issue #2331 replay 4 (orchestrator's own `spawn.py:3930` citation,
# docs/reports/2026-08-09-hunt-repo-scoped-workspace-index-keys.md: "built
# at spawn.py:3930"): a `path:line`/`path:line-range` citation whose line
# number(s) exceed the file's actual current line count in the working
# tree never resolves to anything — a phantom citation, cheap to catch
# without running the cited command at all.
def citation_line_bounds_check(root: Path, text: str) -> list[str]:
    bad = []
    lines = text.splitlines()
    in_fence, _ = _index_fences(lines)
    structural = _structural_skip_mask(lines)
    line_starts, pos = [], 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1
    for m in _CITE_FILE_LINE.finditer(text):
        line_idx = _offset_to_line(line_starts, m.start())
        if in_fence[line_idx] or structural[line_idx]:
            continue
        if _is_derived_unverified(lines, in_fence, line_idx):
            continue
        path_str, start_s, end_s = m.group(1), m.group(2), m.group(3)
        fpath = _safe_repo_path(root, _strip_line_suffix(path_str))
        if fpath is None or not fpath.is_file():
            continue  # #330's job (or an out-of-repo path), not this check's
        try:
            total = sum(1 for _ in fpath.open(
                encoding="utf-8-sig", errors="replace"))
        except OSError:
            continue
        start, end = int(start_s), int(end_s) if end_s else int(start_s)
        if start > total or end > total:
            cited = f"{path_str}:{start_s}" + (f"-{end_s}" if end_s else "")
            bad.append(
                "레코드가 파일의 실제 줄 수를 넘는 file:line 을 인용한다 "
                f"(issue #2331): `{cited}` — `{path_str}` 는 지금 {total}줄"
                "뿐이라 이 인용은 애초에 존재하지 않는 줄을 가리키는 "
                "phantom citation 이다 — 통과하려면 실제 존재하는 줄 "
                "번호로 고치거나, 같은 섹션에 `derived-unverified: <이유>` "
                "를 남기면 된다.")
    return bad


# issue #2331 replay 3 (#2295): four `gates/check_runner.py:N` citations,
# each paired with a literal backtick-quoted code excerpt, all shifted by
# the same +35 lines against the file actually committed at the cited
# commit — caught here by re-deriving the citation's own quoted content
# against the working tree.
_SINGLE_LINE_CITE = re.compile(r"`?([\w./\-]+\.\w+):(\d+)(?!-)`?")
_BACKTICK_SPAN = re.compile(r"`([^`\n]+)`")
_QUOTE_CODE_CHARS = re.compile(r"[()\[\]{}=+<>\"']")


def _looks_like_bare_path(s: str) -> bool:
    return bool(re.fullmatch(r"[\w./\-]+(:\d+(?:-\d+)?)?", s))


def _nearest_code_quote(text: str, in_fence_at, pos: int,
                         max_dist: int = 100) -> str | None:
    """The nearest (by character distance, either direction) backtick
    span to `pos` that reads as a code excerpt rather than a bare path or
    another `path:line` citation — the "quoted fragment" a `path:line`
    citation is claiming lives at that line."""
    best, best_dist = None, None
    for bm in _BACKTICK_SPAN.finditer(text):
        content = bm.group(1)
        if _looks_like_bare_path(content) or _CITE_FILE_LINE.fullmatch(
                content.strip("`")):
            continue
        if not _QUOTE_CODE_CHARS.search(content):
            continue
        if in_fence_at(bm.start()):
            continue
        dist = min(abs(bm.start() - pos), abs(bm.end() - pos))
        if dist <= max_dist and (best_dist is None or dist < best_dist):
            best, best_dist = content, dist
    return best


def citation_line_content_check(root: Path, text: str) -> list[str]:
    bad = []
    lines = text.splitlines()
    in_fence, _ = _index_fences(lines)
    structural = _structural_skip_mask(lines)
    line_starts, pos = [], 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1

    def _in_fence_at(offset: int) -> bool:
        return in_fence[_offset_to_line(line_starts, offset)]

    for m in _SINGLE_LINE_CITE.finditer(text):
        line_idx = _offset_to_line(line_starts, m.start())
        if in_fence[line_idx] or structural[line_idx]:
            continue
        if _is_derived_unverified(lines, in_fence, line_idx):
            continue
        path_str, line_s = m.group(1), m.group(2)
        fpath = _safe_repo_path(root, path_str)
        if fpath is None or not fpath.is_file():
            continue  # #330's job (or an out-of-repo path), not this check's
        quote = _nearest_code_quote(text, _in_fence_at, m.end())
        if quote is None:
            continue
        try:
            file_lines = fpath.read_text(
                encoding="utf-8-sig", errors="replace").splitlines()
        except OSError:
            continue
        cited_line_no = int(line_s)
        quote_norm = _normalize_ws(quote)
        if not quote_norm:
            continue
        if 1 <= cited_line_no <= len(file_lines) and \
                quote_norm in _normalize_ws(file_lines[cited_line_no - 1]):
            continue  # cited line genuinely contains the quoted fragment
        actual_lines = [i + 1 for i, ln in enumerate(file_lines)
                        if quote_norm in _normalize_ws(ln)]
        if not actual_lines:
            continue  # fragment not found anywhere — not this check's job
        if cited_line_no not in actual_lines:
            bad.append(
                "레코드의 file:line 인용 내용이 실제와 다르다 (issue "
                f"#2331): `{path_str}:{line_s}` 이 인용한 조각 "
                f"`{quote}` 는 실제로 {path_str}의 {actual_lines[0]}번째 "
                f"줄에 있다, {line_s}번째 줄이 아니다 — 통과하려면 인용 "
                f"줄 번호를 {actual_lines[0]}로 고치거나, 같은 섹션에 "
                "`derived-unverified: <이유>` 를 남기면 된다.")
    return bad


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

# issue #1614 misfire class 5: a record documenting one of these rules
# itself (e.g. this very issue's own reports under docs/issue-1614/)
# necessarily quotes the rule's marker vocabulary ("found", "PASS",
# "canonical:") to explain the rule — that quotation is not the record
# author making a live claim. Exempt each rule's own check for records
# filed under the issue(s) that define/discuss it.
_RULE_SELF_QUOTE_EXEMPT_ISSUES = {
    "canonical_source_claim_check": {"793", "1614"},
    "outcome_claim_citation_check": {"870", "1614"},
    "defect_claim_grounding_check": {"791", "1614"},
}
_RECORD_ISSUE_RE = re.compile(r"^docs/issue-(\d+)/")


def _record_issue_number(rel: str) -> str | None:
    m = _RECORD_ISSUE_RE.match(rel)
    return m.group(1) if m else None


def lint_record(path: Path) -> list[str]:
    """Run every record rule against one record file's full text and
    return the complete violation list — no first-failure abort.

    Delegates to `gates.py`'s existing diff-scoped check functions (they
    already accept a repo root and internally scan `changed_files()`,
    which covers uncommitted worktree edits — the common authoring case
    of a record just written/scaffolded), filtered down to violations
    naming this specific file, plus the four full-text checks above.
    """
    path = Path(path).resolve()
    root = _repo_root(path)
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    text = path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""

    bad: list[str] = []
    if not RECORD_PATH.match(rel):
        bad.append(
            f"레코드 경로 형태가 아니다: {rel} — "
            "docs/issue-<n>/reports/<role>.md 형태여야 한다.")
        return bad
    if not path.exists():
        bad.append(f"레코드 파일이 없다: {rel}")
        return bad

    diff_scoped = []
    try:
        diff_scoped += gates.record_refusal_reasoned(root, {})
        diff_scoped += gates.record_wellformed_in(root)
        diff_scoped += gates.record_no_tool_residue_in(root)
        diff_scoped += gates.record_derived_counts_in(root)
        diff_scoped += gates.record_checked_claims(root, {})
        diff_scoped += gates.reach_check(root, text)
        diff_scoped += gates.sibling_mention_check(root, text)
    except RuntimeError as e:
        bad.append(str(e))
    # These functions report against every changed record, not just this
    # one — keep only violations that name this file.
    bad += [b for b in diff_scoped if rel in b]

    issue_no = _record_issue_number(rel)

    def _exempt(check_name: str) -> bool:
        return issue_no is not None and \
            issue_no in _RULE_SELF_QUOTE_EXEMPT_ISSUES.get(check_name, set())

    bad += unverifiable_reason_check(text)
    bad += checked_claim_reason_check(text)
    bad += bare_count_claim_check(text)
    bad += orphaned_path_reference_check(root, text)
    bad += git_tracked_path_reference_check(root, text, record_rel=rel)
    bad += wc_l_recompute_check(root, text)
    bad += pytest_count_recompute_check(root, text)
    bad += citation_line_bounds_check(root, text)
    bad += citation_line_content_check(root, text)
    if not _exempt("canonical_source_claim_check"):
        bad += canonical_source_claim_check(text)
    if not _exempt("outcome_claim_citation_check"):
        bad += outcome_claim_citation_check(text)
    if not _exempt("defect_claim_grounding_check"):
        bad += defect_claim_grounding_check(root, text)
    return bad


# issue #1599 fix 2 — pre-rule cutoff for whole-repo sweep mode. The
# linter itself was born 2026-08-09 (this module's first commit,
# 0dea23a5); a record last substantively authored before that date
# predates every rule it's being graded against — grading it and asking
# for retro-inserted canonical:/derived: tags would fabricate provenance
# on a frozen historical record. One linter-wide cutoff, not a per-rule
# birth date: the checks this module runs have each grown/changed since
# 0dea23a5 and a per-rule date would need tracking per-check, for a
# precision problem a single conservative cutoff already fixes.
SWEEP_CUTOFF_DATE = "2026-08-09"


def _last_authored_date(root: Path, rel: str) -> str | None:
    """The most recent commit's author date (YYYY-MM-DD) touching `rel`
    on any branch, or `None` when the path has no commit history (an
    uncommitted/untracked file is never pre-cutoff — nothing to skip)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short",
             "--", rel],
            cwd=str(root), capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    date = out.stdout.strip()
    return date or None


def find_records(root: Path, sweep_cutoff: bool = True) -> list[Path]:
    """All `docs/issue-*/reports/*.md` record files tracked or present
    under `root` — used by the whole-repo scan mode. `sweep_cutoff`
    (default on, matching this function's only caller: `main()`'s
    directory mode) skips a record last authored before
    `SWEEP_CUTOFF_DATE` — the linter cannot grade a record frozen
    before the rules it's graded against existed."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            full = Path(dirpath) / fn
            rel = full.relative_to(root).as_posix()
            if not RECORD_PATH.match(rel):
                continue
            if sweep_cutoff:
                authored = _last_authored_date(root, rel)
                if authored is not None and authored < SWEEP_CUTOFF_DATE:
                    continue
            out.append(full)
    return out


def main(argv: list[str]) -> int:
    target = Path(argv[0]) if argv else Path(".")
    if target.is_dir():
        records = find_records(target)
        if not records:
            print("record_lint: no records found under "
                  f"{target.resolve()} — 검사할 레코드가 없다.")
            return 0
        exit_code = 0
        for rec in sorted(records):
            violations = lint_record(rec)
            if violations:
                exit_code = 1
                print(f"== {rec} ==")
                for v in violations:
                    print(f"- {v}")
        return exit_code

    violations = lint_record(target)
    if not violations:
        print(f"record_lint: {target} — 위반 없음.")
        return 0
    for v in violations:
        print(f"- {v}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
