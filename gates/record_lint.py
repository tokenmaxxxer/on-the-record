"""issue-517 — aggregate, single-pass record lint.

Authoring a role record today costs one model turn per gate refusal:
`record_enums`/`record_wellformed`/... in `gates.py` and the four checks
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
import gates

RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md

# Re-exported, not reimplemented: `gates/ci.py` and `record-claim-guard.sh`
# call these names on this module instead of holding their own copies —
# single source of truth means the same function object, not a mirror.
record_enums = gates.record_enums
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
_CLAIM_DERIVED_TAG = re.compile(r"`derived:\s*\S.*?`")
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
    "PASS(es/ed)", "complete(d)") needs a `canonical:` tag within 3 lines
    above it whose cited source is itself an executed-live reference (a
    command string, an `acceptance: <command> — result: ...` line, or —
    issue #923 — a citation naming the transcript/measurement an
    observation/verdict record's own live run produced) — not a bare
    file-read/summary citation, which satisfies #793's own state-claim
    check but does not prove the claimed outcome was actually re-run (or,
    for an observation record, actually measured) against the current
    state. Fail-closed: no qualifying citation -> refused."""
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
    for i, line in enumerate(lines):
        if in_fence[i] or structural[i]:
            continue
        matches = [m for m in _OUTCOME_CLAIM_MARKER.finditer(line)
                   if not _outcome_marker_word_sense_exempt(line, m)]
        if not matches:
            continue
        if _is_hypothetical_or_negated(line) or _is_historical_narration(line):
            continue
        # issue #1614 misfire class 3: evidence adjacency was above-only —
        # a citation on the SAME line (already covered by ending at `i`)
        # or up to 3 lines BELOW the claim now also counts.
        window = "\n".join(lines[max(0, i - 3):min(len(lines), i + 4)])
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
        if not (has_executed_live or has_derived or has_observation_live
                or has_pinned):
            bad.append(
                "레코드에 실행-근거 없는 OUTCOME 주장 (issue #870): "
                f"{line.strip()!r} — 'requirement met/done/PASS/complete' "
                "류의 결과 주장을 하면서 3줄 이내에 실행-라이브 인용"
                "(`gh ...`/`pytest ...`/`python3 ...`/"
                "`acceptance: <command> — result: ...`로 시작하는 "
                "`canonical:` 태그, 또는 관측/verdict 레코드라면 자신이 "
                "이번 턴에 만든 transcript/measurement를 지칭하는 "
                "`canonical:` 태그)이 없다 — 파일을 읽었다는 인용만으로는 "
                "부족하다.")
    return bad


def unverifiable_reason_check(text: str) -> list[str]:
    """#310/#331 mirror: an `unverifiable:` escape line needs a reason."""
    bad = []
    for m in _UNVERIFIABLE_LINE.finditer(text):
        if not m.group(1).strip():
            bad.append(
                "`unverifiable:` 줄에 이유가 없다 (issue #310) — "
                "`unverifiable: <이유>` 형태로 왜 기계 검사가 불가능한지 "
                "적어야 한다.")
    return bad


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
                f"없다 (issue #331): {ln.strip()!r}")
    return bad


# issue #1620 misfire class 4: a tally whose computation is spelled out
# inline right next to it — a percentage shown alongside the raw
# fraction (e.g. "33.3% precision (4 TP / 12)"), or an explicit
# multiplication/sum shown with an `=` (e.g. "9 keywords x
# (lower/capitalize/upper) = 27 cases") — is self-evidencing: the reader
# can see how the number was derived without a separate
# `derived:`/fence citation.
_INLINE_COMPUTED_LEADIN = re.compile(r"\d+(?:\.\d+)?%|=")


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
    fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            fence = not fence
            fence_flags[i] = True
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
                if _INLINE_COMPUTED_LEADIN.search(evidence_window):
                    continue
                # "backed by a fenced raw-output block above" (issue
                # #1620 class 4) — a fenced block anywhere earlier in
                # the same record's prose (not just the immediate
                # window) is deliberate evidentiary output, not
                # incidental code quoted right next to an unrelated
                # count.
                if any(fence_flags[:i]):
                    continue
                bad.append(
                    "레코드에 근거 없는 개수 주장 (issue #333): "
                    f"{line.strip()!r} — 숫자가 코드펜스 재현이나 "
                    "`derived: ...` 인용 없이 그냥 타이핑되어 있다.")
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
        if _is_path_rename_narration(window) or _is_absence_negated(window):
            continue
        ref = _strip_line_suffix(m.group(1))
        if any(ch in ref for ch in ("*", "?", "<", ">")):
            continue
        if not (root / ref).exists():
            bad.append(
                "레코드가 존재하지 않는 경로를 참조한다 (issue #330): "
                f"`{ref}` — 리치(reach)가 끊긴 참조다.")
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
    """issue #793 mirror: a state/defect-claim line (role output "found",
    session/PR/board state "halted|merged|closed|is running|is gone|is
    stale", or a bare count claim) needs a `canonical: <what was read>`
    tag within 3 lines above it, citing the actual role record/diff, raw
    ground-truth command output, or file:line-context read — not a
    summary/grep/watcher signal with nothing named."""
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
        # issue #1614 misfire class 3: symmetric evidence-adjacency window.
        window = "\n".join(lines[max(0, i - 3):min(len(lines), i + 4)])
        m = _CANONICAL_TAG.search(window)
        has_canonical = bool(m and m.group(1).strip())
        # A count claim already satisfying #333's `derived:` requirement
        # names its source too — `canonical:` is a sibling tag, not a
        # second mandatory citation for the same already-cited count.
        has_derived = count_claim and bool(_CLAIM_DERIVED_TAG.search(window))
        # issue #1599 fix 4 — a commit-pinned citation is evidence in its
        # own right, independent of a literal `canonical:` prefix.
        has_pinned = bool(_COMMIT_PINNED_CITE.search(window))
        if not (has_canonical or has_derived or has_pinned):
            bad.append(
                "레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): "
                f"{line.strip()!r} — role output / session·PR·board 상태 / "
                "결함을 주장하면서 3줄 이내에 `canonical: <읽은 소스>` 태그가 "
                "없다 — 요약이나 grep/watcher 신호가 아니라 실제 레코드/diff, "
                "raw ground truth, 또는 file:line 컨텍스트를 인용해야 한다.")
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
                "grep/키워드 히트 하나만으로는 근거가 되지 않는다.")
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
        diff_scoped += gates.record_enums(root, {})
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
    (default on, matching this function's only callers: `main()`'s
    directory mode and `patrol_queue`'s sweep-lane scanner) skips a
    record last authored before `SWEEP_CUTOFF_DATE` — the linter cannot
    grade a record frozen before the rules it's graded against existed."""
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
