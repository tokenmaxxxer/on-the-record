---
proposal: docs/issue-1726/proposals/2026-08-17-stop-bootstrapping-product-capture-doc-files.md
---

# Hunt record — stop-bootstrapping-product-capture-doc-files

## after-proposal — stance 1: does any other file assume the product-capture doc file exists once a category is flagged?

Verdict: FINDING — gates/test_product_capture_vs_deliverable_guard.py::t_empty_state_bootstrap_still_works is a permanent regression guard for the exact behavior #1726 deleted, marked xfail(strict=False) with a stale reason (blames issue #1619 "investigation tracked separately", i.e. implies a pending fix that would restore bootstrapping) — so the suite will keep reporting "passed"/"xfailed" forever with no signal that the guarded behavior is now permanently gone by design, not merely broken.
Kind: design-error
Seed: on-the-record/hooks/product-capture-stopgate.sh (bootstrap-on-first-flag block removed), on-the-record/hooks/test_product_capture_stopgate.py
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: 2 files changed, 19 insertions(+), 13 deletions(-) (per `git diff --stat`)
started_at: 2026-08-17T00:00:00Z
ended_at: 2026-08-17T00:35:00Z

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-1726-implementation
python3 -m pytest -o addopts="" gates/test_product_capture_vs_deliverable_guard.py -v -rx
```
then isolate the guarded assertion directly, bypassing the file's own
session-id/state-dir caching artifact (the same fixed session_id
`sess-1118-d` is reused by every run in this file, so the *first* run on a
box masks the real issue behind a stale-state JSONDecodeError — use a fresh
session_id/state_dir to see what the test is actually asserting now):
```
python3 -c "
import sys, tempfile, json
from pathlib import Path
sys.path.insert(0, 'gates')
from test_product_capture_vs_deliverable_guard import _init_repo, _write_transcript, _run_stopgate

with tempfile.TemporaryDirectory() as td:
    repo = Path(td)
    _init_repo(repo)
    state_dir = repo / 'state'
    transcript = _write_transcript(repo, ['the project must support offline mode.'])
    r = _run_stopgate(repo, transcript, session_id='sess-fresh', state_dir=state_dir)
    out = json.loads(r.stdout)
    print('flag fired:', 'requirements.md' in out['hookSpecificOutput']['additionalContext'])
    doc = repo / 'docs' / 'issue-123' / 'reports' / 'product' / 'requirements.md'
    print('doc.exists():', doc.exists())
"
```

### Observed
`gates/test_product_capture_vs_deliverable_guard.py::t_empty_state_bootstrap_still_works` is
declared:
```python
@pytest.mark.xfail(
    reason="issue #1619: product-capture-stopgate.sh now exits with empty "
           "stdout for this no-docs/product/ bootstrap scenario instead of "
           "the expected JSON payload, breaking json.loads(r.stdout) -- "
           "pre-existing behavior drift in the hook, needs "
           "product-capture-stopgate.sh investigation tracked separately "
           "from this suite-hygiene pass.",
    strict=False)
def t_empty_state_bootstrap_still_works():
    # (d) regression guard for #566's bootstrap-on-first-flag: no
    # docs/product/ directory at all -> still bootstraps and flags.
    ...
    doc = repo / "docs" / "issue-123" / "reports" / "product" / "requirements.md"
    assert doc.exists()
    assert "Requirements" in doc.read_text()
```
Running the suite: `3 passed, 1 xfailed` (unchanged before/after #1726 — the
xfail machinery absorbs the failure silently either way).

Running the guarded logic directly with a fresh session/state dir (bypassing
the file's own session_id-caching quirk that currently masks this) prints:
```
flag fired: True
doc.exists(): False
```
i.e. the category *is* flagged (confirming the flag path is untouched, per
the proposal), but the file the test calls "regression guard for #566's
bootstrap-on-first-flag" now provably can never come back true: the doc file
is never created, by the explicit and permanent design intent stated in
on-the-record/hooks/product-capture-stopgate.sh's own new comment ("Issue
#1726: dropped bootstrap-on-first-flag. The hook no longer creates the
category doc file just because a category was flagged"). The xfail reason
attached to the test, however, still frames this as an open bug ("needs ...
investigation tracked separately") rather than a closed, intentional design
change — nothing in #1726's diff touched this test or its reason string.

### Expected
Either the test (and its xfail reason) should have been removed/updated in
the same change that permanently deleted bootstrap-on-first-flag — the same
way on-the-record/hooks/test_product_capture_stopgate.py's
`t_bootstrap_creates_missing_file_on_first_flag` was renamed and its
assertions flipped — or, at minimum, the xfail reason should say the
underlying behavior is gone for good, not "tracked separately" as if a future
patch might restore it. As written, the test suite gives identical output
("1 xfailed") whether the hook still has a live, fixable bug (#1619's
framing) or has had the guarded feature permanently deleted by design
(#1726) — the design change is invisible in test output.
