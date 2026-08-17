
## after-proposal — stance 1: command-identity mismatch matching gaps

Verdict: FINDING — same-first-token candidate filter lets a differing-interpreter command (e.g. `python` vs `python3`) slip past command-identity check when the artifact string also happens to appear literally elsewhere in the diff, silently leaving `blocked: False`
Kind: silent-failure
Seed: gates/requirement_met.py (_command_identity_mismatch, _provenance_map, _recorded_commands_in_diff), gates/test_requirement_met.py
cap_seconds: n/a
tier: n/a
diff_stat_lines: n/a
started_at: 2026-08-17T00:00:00Z
ended_at: 2026-08-17T00:20:00Z

### Reproduce
```python
import gates.requirement_met as rm

issue_body = """
## Acceptance
- check: `python -m pkg.cli test` passes
  provenance: executed-live
"""

diff = """diff --git a/notes.py b/notes.py
+++ b/notes.py
+CMD = "python -m pkg.cli test"
+acceptance: python3 -m pkg.cli test — result: PASS
"""

res = rm.grade(issue_body, diff, {"`python -m pkg.cli test` passes": "YES"})
print(res["blocked"], res["criteria"][0]["command_identity_mismatch"])
```

### Observed
`False False` — the check is scored YES, the artifact string literally appears in the diff (as an unrelated string constant), and the recorded `acceptance:` line runs `python3 ...` instead of the named `python ...`. Because `_command_identity_mismatch` only considers `recorded_commands` whose first whitespace token matches the artifact's first token, `python3 -m pkg.cli test` is never compared against `python -m pkg.cli test` at all — it's filtered out of `candidates` before the exact-match check runs. `grade()` reports no blocking reasons and `blocked: False`.

### Expected
An executed-live check naming `python -m pkg.cli test` but only provably invoked via `python3 -m pkg.cli test` in the diff should be flagged as a command-identity mismatch (or, at minimum, the artifact-presence path should not consider a bare substring match in unrelated code sufficient to clear the check when a differently-fronted acceptance citation exists). As written, first-token filtering silently excludes the exact class of interpreter-substitution mismatch (`python` vs `python3`, `pip` vs `pip3`, `node` vs `nodejs`, etc.) that the feature's own docstring cites as the motivating fake-success vector.
