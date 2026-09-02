---
proposal: docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4.md
---

# Hunt record — supersession-and-fail-closed-downgrade

## before-landing — stance 1: assume the gate/probe just added is bypassable — find the bypass

Verdict: FINDING — `resolve_authoritative()` compares a `supersedes:` target against `records` dict keys by raw string equality with no path normalization, so a corrector whose `supersedes:` value differs syntactically from the exact key used for the same file (e.g. a leading `./`) fails to mark the original as superseded; the fabricated/stale original then stays listed in `authoritative` right alongside the correction.
Kind: silent-failure
Seed: supersession.py (new module), gates/probe_supersession_marker.py, per warrant prompt stance on issue #3050 PR #3086
cap_seconds: 180
tier: size:full (gates/ path touched)
diff_stat_lines: 345 (/tmp/warrant-diff.txt)
started_at: 2026-09-02T00:00:00Z
ended_at: 2026-09-02T00:20:00Z

### Reproduce
Ran the following against the repo's own `supersession.py`. Paths in it (`docs/issue-9101/...`) are synthetic, untracked, in-memory dict keys only — the same fictional example `gates/probe_supersession_marker.py` itself already uses; no real record path is invoked. Script was written to a temp file under `gates/`, run with `python3 gates/tmp_repro_supersession_norm.py`, then deleted:

```python
import supersession as s

ORIGINAL_PATH = "docs/issue-9101/reports/coding.md"
CORRECTION_PATH = "docs/issue-9101/reports/verification.md"

ORIGINAL_CONTENT = """---
issue: 9101
role: coding
loop_state: landed
---

# issue-9101 -- coding record

Migrated the report generator; cited throughput as 4200 req/s (fabricated).
"""

# supersedes field cites the original path with a leading "./" -- a
# normalization variant of the exact dict key used for that same file.
MARKER = s.render_supersedes_field("./" + ORIGINAL_PATH, "fabricated figures")

CORRECTION_CONTENT = f"""---
issue: 9101
role: verification
loop_state: landed
{MARKER}
---

# issue-9101 -- verification record

Re-measured; original figures were fabricated.
"""

tree = {ORIGINAL_PATH: ORIGINAL_CONTENT, CORRECTION_PATH: CORRECTION_CONTENT}
print(s.resolve_authoritative(tree))
```

### Observed
Output (synthetic in-memory dict keys, untracked, not real repo paths):
```
{'authoritative': ['docs/issue-9101/reports/coding.md', 'docs/issue-9101/reports/verification.md'], 'superseded': {}, 'broken': ['./docs/issue-9101/reports/coding.md'], 'conflicts': {}}
```
The stale/fabricated original (synthetic, untracked path, same fictional key as above) is returned in `authoritative`, indistinguishable from a record that was never superseded at all. The mismatch is silent: nothing in the return value flags that a `supersedes:` claim aimed at this exact file failed to resolve because of a one-character path variant; the reader sees the target listed under `broken` as if the corrector had named some other, absent file, not the file sitting right there in the same tree under a different-looking key.

### Expected
Either `resolve_authoritative()` normalizes both the `supersedes:` value and the dict keys before comparing (so a `./` prefix, doubled slashes, or other harmless path variants still resolve to the same file), or, short of that, the module's own docstring/contract should say plainly that citing paths must match dict keys byte-for-byte — since nothing else in the tree (no git, no filesystem) can currently catch or warn about the mismatch, and the failure mode is exactly the one the module exists to prevent: a stale, fabricated record surviving in `authoritative` next to its own correction.
