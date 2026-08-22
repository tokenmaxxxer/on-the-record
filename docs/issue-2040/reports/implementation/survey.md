---
subject: issue-2040
role: implementation
phase: 1-survey
---

# Survey: cross-family skill selection scorer, ahead of the BM25-first proposal

Scope per the operator's direction-amendment comment on #2040: evaluate a
pure-python BM25 ranker as a replacement for the raw token-overlap
prefilter FIRST, replay it over the existing >=10-issue corpus, and only
propose the consult-judge stage if BM25 replay still shows
condition-mismatch picks.

## Current surface: `_cross_family_skill_matches`

canonical: spawn.py:7976-8012, read directly.

`derived:`
```
$ grep -n "_TOKEN_RE\|_STOPWORDS\|_CROSS_FAMILY_MIN_OVERLAP\|def _tokenize\|def _cross_family_skill_matches" spawn.py
7976:_TOKEN_RE = re.compile(r"[a-z0-9]+")
7977:_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})
7978:_CROSS_FAMILY_MIN_OVERLAP = 2
7981:def _tokenize(text: str) -> set[str]:
7988:def _cross_family_skill_matches(task_text: str, role: str,
```

spawn.py:7988-8012 implements the scorer landed under issue #2001: it
tokenizes `task_text` and every candidate skill's "Use when ..." trigger
sentence into lowercase alnum token sets (7-word stopword list only), scores
each cross-family skill directory by raw `set` intersection size
(`len(task_tokens & _tokenize(trigger))`), keeps anything `>=
_CROSS_FAMILY_MIN_OVERLAP` (2), and returns the top-K=2 by descending
overlap, name as tiebreak. It is called once, at spawn.py:8160, with the
raw pre-annotation task text (`_cross_family_task_text`, pinned before
later prompt-building appends skill-list text into `task`, per the
issue-#2001 comment at spawn.py:8027-8030 — determinism guard already in
place, not something this issue needs to touch).

No IDF/document-frequency weighting exists anywhere in this path today —
every token counts equally regardless of how many candidate skills'
triggers share it, which is the defect the issue names ("lexical token
overlap noise").

## The existing replay corpus (cycle-1/cycle-2, `docs/issue-2001/reports/implementation/replay-table.md`)

canonical: `docs/issue-2001/reports/implementation/replay-table.md`, read
directly.

That table already replayed today's raw-overlap scorer over 16 real
`issue x role` pairs pulled from same-day (2026-08-22) session logs under
`/home/jwjung/.tokenmaxxxer/work/`, fetching each issue's live
title+body via `gh issue view <n> --json title,body` (>= 10 issues,
satisfies the Acceptance's replay-corpus floor; this survey reuses it
rather than inventing a second one — same repo, same fetch method, same
role-mapping, and it already carries a documented open finding this issue
exists to close).

This survey re-ran the same 16 pairs against the *current* skill-repo
state (skill set may have changed since 2026-08-22) with today's
raw-overlap scorer, to check whether the prior table's finding still
holds before spiking BM25 against it.

`derived:`
```
$ python3 - <<'PYEOF'
import subprocess, json, sys
sys.path.insert(0, ".")
import spawn
pairs = [(1745,"implementation"),(1955,"implementation"),(1958,"implementation"),
         (1959,"test-authoring"),(1960,"implementation"),(1966,"implementation"),
         (1969,"implementation"),(1976,"implementation"),(1978,"implementation"),
         (1981,"implementation"),(1982,"implementation"),(1991,"implementation"),
         (1992,"implementation"),(1996,"knowledge-management"),(1999,"implementation"),
         (2001,"implementation")]
repo_root = spawn._skill_repo_root()
sev = mr = 0
for issue, role in pairs:
    out = subprocess.run(["gh","issue","view",str(issue),"--json","title,body"],
                          capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    text = (data.get("title") or "") + "\n" + (data.get("body") or "")
    names = [d.name for d in spawn._cross_family_skill_matches(text, role, repo_root)]
    if "conformance-review-severity-classification" in names: sev += 1
    if "model-routing" in names: mr += 1
print("raw_overlap_severity_count", sev, "of", len(pairs))
print("raw_overlap_model_routing_count", mr, "of", len(pairs))
PYEOF
raw_overlap_severity_count 16 of 16
raw_overlap_model_routing_count 5 of 16
```

canonical: `raw_overlap_severity_count`/`raw_overlap_model_routing_count`
lines of the derived block directly above.

Per that derived output, `conformance-review-severity-classification`
clears threshold on all 16 replayed rows, and `model-routing` on 5 of
them — confirming the prior table's finding is still live: both are
spurious (generic engineering vocabulary in the trigger sentence, not
real domain relevance), the same failure class as the issue's own named
example (kimball/finance-ltv-cac for a REST pagination task).

## BM25 spike, same corpus, same candidate pool

A pure-python BM25 (Okapi BM25, standard k1=1.5/b=0.75, no new
dependency — implementable in ~30 lines against `spawn._skill_trigger_line`
and `spawn._tokenize`'s existing tokenizer) was spiked against the exact
same 16 pairs: corpus = every cross-family candidate's trigger sentence,
query = issue title+body, ranked by BM25 score, top-2 kept (score > 0
only, no fixed min-overlap threshold — BM25 scores aren't raw overlap
counts so the old `_CROSS_FAMILY_MIN_OVERLAP=2` cutoff doesn't transfer
as-is; this survey does not decide its replacement, see proposal).

canonical: the BM25 spike script's own stdout, quoted verbatim in the
derived block directly below.

`derived:`
```
$ python3 /tmp/bm25_spike.py   # ad hoc spike script, BM25 over spawn._skill_trigger_line() corpus
1745 implementation ['user-discovery-verdict-prevalence-reporting', 'customer-support-research-log']
1955 implementation ['market-analysis-mece-proposal', 'observability-phase-trace']
1958 implementation ['conformance-review-sampling-derivation', 'issue-retrospective-timeline-comprehensibility-and-subtraction-rules']
1959 test-authoring ['observability-phase-trace', 'model-routing']
1960 implementation ['conformance-review-severity-classification', 'conformance-review-finding-record']
1966 implementation ['conformance-review-severity-classification', 'test-derivation']
1969 implementation ['model-routing', 'conformance-review-severity-classification']
1976 implementation ['conformance-review-severity-classification', 'model-routing']
1978 implementation ['conformance-review-severity-classification', 'pricing-scope-gate']
1981 implementation ['usability-eval', 'conformance-review-severity-classification']
1982 implementation ['usability-eval', 'test-derivation']
1991 implementation ['test-derivation', 'test-authoring-isolation-and-fixture-strategy']
1992 implementation ['secure-coding-authorization-access-control', 'technical-feasibility-build-vs-buy-dependency-health']
1996 knowledge-management ['brand-design-icon-system-svg', 'kubernetes-workload-requests-limits-decision']
1999 implementation ['model-routing', 'conformance-review-severity-classification']
2001 implementation ['model-routing', 'accessibility-aria-and-contrast-rules']
bm25_severity_count 7 of 16
bm25_model_routing_count 5 of 16
```

canonical: `bm25_severity_count`/`bm25_model_routing_count` lines of the
derived block directly above.

Per that derived output, `conformance-review-severity-classification`
clears threshold on 7 of the 16 rows (down from all 16 under raw
overlap), and `model-routing` still clears on 5 of them (unchanged from
raw overlap).

## Open finding this survey surfaces

canonical: the `raw_overlap_*` and `bm25_*` count lines from the two
derived blocks above, compared directly.

BM25's IDF term measurably reduces `conformance-review-severity-classification`
noise (16-of-16 down to 7-of-16 — a real improvement, IDF correctly
down-weights the token overlap coming from generic words), but does not
clear it: those remaining 7 rows still surface it as a top-2 pick for
tasks with no conformance plausibility (e.g. #1960 "measuring
skill-invocation rate", #1978 "spawn directive assembly" — same
no-verdicts the prior table gave these rows). `model-routing` sits at
5-of-16 in both the raw-overlap and the BM25 derived blocks above — no
improvement — because its trigger sentence ("Use this skill on EVERY
non-trivial task...") is deliberately maximal prose: IDF alone cannot
separate genuine matches from its by-design breadth, since only a
condition-match judgment can tell whether a task is a "non-trivial task"
in `model-routing`'s intended sense, something no lexical/statistical
scoring (overlap or BM25) can express.

Per the issue's own phase order (operator's amendment comment): BM25
replay still shows condition-mismatch picks -> the consult-judge stage
belongs on top, as originally scoped in the issue body, not shipped as
BM25-alone. This is not decided further here; the proposal carries the
build plan.
