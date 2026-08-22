---
subject: issue-2012
role: implementation
phase: 1-survey
---

# Current-state survey: design-bearing issue classification (artifact-gate phase 1)

## Reusable signal: `_tokenize` / overlap scoring from #2001

`spawn.py:7952-7986` (landed via #2001, PR #2002) already carries the
exact machinery this issue is told to reuse rather than reinvent:

- `_TOKEN_RE = re.compile(r"[a-z0-9]+")` (spawn.py:7952) — lowercase,
  non-alphanumeric-split tokenization.
- `_STOPWORDS` (spawn.py:7953) — an 8-word fixed stopword list.
- `_tokenize(text)` (spawn.py:7957-7961) — applies both, returns a
  token set.
- `_cross_family_skill_matches(task_text, role, repo_root, k=2)`
  (spawn.py:7964-7986) — scores candidate trigger sentences against
  `task_text` by distinct-token overlap, keeps candidates clearing
  `_CROSS_FAMILY_MIN_OVERLAP = 2` (spawn.py:7954), sorts by `(score
  desc, name asc)` for determinism, returns top-k.

`derived:`
```
$ grep -n "_tokenize\|_cross_family_skill_matches\|_STOPWORDS\|_TOKEN_RE\|_CROSS_FAMILY_MIN_OVERLAP" spawn.py
7952:_TOKEN_RE = re.compile(r"[a-z0-9]+")
7953:_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})
7954:_CROSS_FAMILY_MIN_OVERLAP = 2
7957:def _tokenize(text: str) -> set[str]:
7964:def _cross_family_skill_matches(task_text: str, role: str,
7973:        task_tokens = _tokenize(task_text)
7984:        overlap = len(task_tokens & _tokenize(trigger))
7985:        if overlap >= _CROSS_FAMILY_MIN_OVERLAP:
8133:            cross_family_dirs = _cross_family_skill_matches(
```

This is issue text (or trigger-sentence text) scored against a small
fixed vocabulary by deterministic keyword overlap — structurally the
same shape #2012's classifier needs (issue text scored against a
design-bearing-signal vocabulary instead of a skill-trigger
vocabulary). `_tokenize` itself is directly reusable, byte-for-byte,
with no modification. The overlap-scoring loop shape
(`_cross_family_skill_matches`'s body) is reusable as a pattern, not
as a call site — its inputs are skill directories/trigger sentences,
not a fixed keyword list, so the classifier needs its own scoring
function built the same way rather than a call into
`_cross_family_skill_matches` itself.

## Prior art in this repo: #1653's design-research consult gate

canonical: `gates/design_research_consult.py` read in full this
session.

`gates/design_research_consult.py` (issue #1653) already gates on
design-bearing-ness, but by self-declaration, not classification: it
regexes an issue body for either `design-research: <ref>` or the
closed-vocabulary escape `design-research-skip: mechanical`
(`gates/design_research_consult.py:22-27`) and fails if neither tag is
present. It never inspects the issue's actual content to decide
design-bearing-ness — the author (human or role) self-tags. #2012 is
explicitly a different, harder problem: an automatic classifier the
orchestrator can consult before any tag exists, with verdict +
evidence + override — #1653's gate is a downstream consumer this
classifier could feed later (out of this issue's scope; #2013,
already filed as artifact-gate phase 2, is the consumer of a
design-bearing verdict, not this issue).

## Existing gate module conventions to follow

canonical: `gates/design_research_consult.py`,
`gates/requirement_intake_consult.py`, `gates/acceptance_gate.py` read
in full this session.

Every `gates/*.py` classifier module in this repo follows the same
shape: a pure `check_issue_body` / `check_*` function taking
already-fetched text (no network, unit-testable), a `check(repo,
issue)` wrapper that fetches via `gh_rest.fetch_issue_body`, and a
`main()` CLI entry that prints a verdict line and exits accordingly
via `sys.exit`. `gates/gh_rest.py` already exposes
`fetch_issue_body(repo, issue)` (used by `design_research_consult.py`
and others) — reusable directly for the classifier's own `check()`
wrapper, no second gh-fetch mechanism needed.

## No existing design-bearing corpus in this repo

This repository (`on-the-record`) is itself an orchestration/process
tool — its own issue corpus is infra/process-shaped throughout,
searched live this session:

`derived:`
```
$ gh issue list --state all --search "landing page" --limit 10 --json number,title
[{"number":2012,"title":"Design-bearing issue classifier ..."}]
$ gh issue list --state all --search "portfolio" --limit 10 --json number,title
[]
$ gh issue list --state all --search "wireframe" --limit 10 --json number,title
[]
```

No issue in this repo's own tracker is a literal "webfolio landing
page" / "brand SVG" / "k8s platform design" build — the parent issue's
named exemplars describe categories of design-bearing work (a product
UI surface, a visual-identity asset, an architecture/topology diagram),
not literal issue numbers to replay against the way #2001 replayed
against 12+ real spawned sessions of this repo. The classifier's
design-bearing exemplar set therefore has to be constructed as
representative fixture issue bodies (synthetic, but shaped like real
design-decision requests) rather than pulled verbatim from this repo's
own history.

The mechanical side is different: this repo's own corpus already
supplies real, landed, unambiguously mechanical issues usable verbatim
as the zero-false-positive exemplar set:

`derived:`
```
$ gh issue list --state closed --search "wiring" --limit 15 --json number,title
1975 Watcher alive but event-silent: 92min of no watcher-log output ...
1635 record_enums (gates.py) mis-flags valid bucketed loop_state values ...
1596 [patrol:test-authoring] record-lint-violation: docs/issue-831/...
1742 spawn.py: additive --skills mount from skill-repository (skill-axis program phase 1)
```

Each is a same-repo mechanical fix/wiring change with no design
decision in scope (bugfix, flag/CLI wiring, false-positive-detector
correction) — directly usable as real-corpus mechanical exemplars,
rather than inventing synthetic mechanical fixtures when real ones
already exist in this repo's own tracker.

## Precision-first framing: what "zero false positives on mechanical" constrains

Per the parent issue's acceptance line, the corpus check is
asymmetric: the mechanical set must score zero false positives (never
wrongly flagged design-bearing), while the design-bearing set only
needs to be marked design-bearing — no stated false-negative bound.
This mirrors #2001's own chosen threshold philosophy
(`_CROSS_FAMILY_MIN_OVERLAP = 2`, chosen conservatively per that
proposal's Rationale so a single generic shared word cannot alone
trigger a match) — the same conservative-threshold instinct applies
here, but the vocabulary is fixed design-signal keywords (storyboard,
information architecture, flow diagram, user scenario(s), HTML demo,
wireframe, landing page, mockup, visual design, brand identity, UI/UX,
layout, ...) rather than per-skill trigger sentences, so the threshold
and stopword list need their own calibration against the corpus above,
not a copy of #2001's tuned constant.

## Override path: no existing mechanism to reuse

canonical: `gates/design_research_consult.py`,
`gates/requirement_intake_consult.py` read in full this session — no
override/pin mechanism exists in either.

Neither file has a per-issue override/pin mechanism analogous to what
#2012 asks for (orchestrator can override per issue). The
closed-vocabulary escape tag pattern `design-research-skip: mechanical`
from #1653 (`gates/design_research_consult.py:24-27`) is the closest
existing precedent in this repo for a human-authored, closed-vocabulary
per-issue override tag read straight from the issue body — reusable as
the shape of an override (a closed-vocabulary tag line the classifier
checks before/instead of running its own scorer), not as shared code.

## Test fixture pattern to extend

`test/` and `tests/` both hold gate-module unit tests; the nearest
sibling is a `gates/*_consult.py`-style module tested with a plain
`unittest.TestCase` calling `check_issue_body` directly on literal
issue-body strings (no `gh` mock needed, no `_spawn_one` fixture
needed — simpler than #2001's `DirectiveAssemblyBase`, since this
classifier is a standalone gate function, not something wired into
`_spawn_one`'s directive-assembly path in this phase).
