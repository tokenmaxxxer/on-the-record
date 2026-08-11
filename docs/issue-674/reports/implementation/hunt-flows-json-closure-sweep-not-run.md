---
proposal: docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md
---

# Hunt record — flows-json-closure-sweep-not-run

Note: the warrant directive specifies a different record path directly
under `docs/issue-674/reports/`, but writing there was refused by this
session's `board-gate.sh` R5 ownership rule (`CLAUDE_ROLE=implementation`
on branch `issue-674/implementation`; error: "belongs to another role.
implementation writes only implementation.md, implementation/** — never
a foreign record"). Every existing `hunt-*.md` record under
`docs/issue-*/reports/` in this repo lives under a role subtree
(`reports/<role>/hunt-*.md`), never directly under `reports/`, which
matches R5 but not the directive's naming rule for issue-scoped
proposals. Filing this record under `reports/implementation/` instead
so it lands somewhere at all.

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — accumulation-claim-guard's "filled" check on `## Accumulation` accepts any non-blank line, so a one-character placeholder body satisfies the gate exactly as well as a real accumulation-cost claim.
Kind: silent-failure
Seed: docs/issue-674/reports/implementation/survey.md, docs/issue-674/proposals/2026-08-11-flows-json-closure-sweep-not-run.md (two new docs-only files; the proposal's own `## Accumulation` section, added to satisfy on-the-record/hooks/accumulation-claim-guard.sh, was the named candidate)
cap_seconds: 60
tier: default (size:docs-only)
diff_stat_lines: 2 files changed (docs-only, no code diff vs main)
started_at: 2026-08-11T02:52:19Z
ended_at: 2026-08-11T02:56:30Z

### Reproduce
```
cd /tmp && rm -rf acg_test && mkdir -p acg_test/docs/issue-674/proposals && cd acg_test && git init -q
PAYLOAD=$(python3 -c '
import json
content = "# Proposal\n\nfiles:\n  - roles/example.json\n\n## Accumulation\nx\n"
print(json.dumps({"tool_name":"Write","tool_input":{"file_path":"docs/issue-674/proposals/2026-08-11-x.md","content":content},"cwd":"/tmp/acg_test"}))
')
export ACG_PAYLOAD="$PAYLOAD"
export ORCHESTRATE_OFF=0
bash /Users/jk/.tokenmaxxxer/work/on-the-record-issue-674-implementation/on-the-record/hooks/accumulation-claim-guard.sh <<< "$PAYLOAD"
echo "exit=$?"
```

### Observed
`exit=0` — the guard allows the write. The `files:` list names
`roles/example.json`, which trips shape 5
(`_touches_shape_5`/`re.match(r"^roles/[^/]+\.json$", ...)`), so the
guard's own logic requires a filled `## Accumulation` section before it
will pass. It passes anyway, because `_has_filled_accumulation` is:
```python
def _has_filled_accumulation(body):
    m = _ACCUMULATION_HEADING.search(body or "")
    if not m:
        return False
    return any(line.strip() for line in m.group(1).splitlines())
```
— `x` is a non-blank line, so the check is satisfied. Nothing about the
body content is checked: it need not mention accumulation, cost, N-more
occurrences, or the touched shape at all. (The guard's own header
comment names this as deliberate: "field-presence strengthening ...
content is never interpreted, contract section 14" — the check is
documented as shallow by design, but the pass/fail outcome an author or
reviewer sees is identical to a real, substantive claim, which is
exactly the "looks like success" shape this hunt is chartered to flag.)
The actual proposal on this branch has a genuine, specific
`## Accumulation` section (not hollow), so this run found the guard's
enforced condition generally bypassable, not a hollow instance already
present in this proposal.

### Expected
A gate whose stated purpose is to force authors to "specify what happens
if this change comes N more times" should not be satisfiable by a
single placeholder character; at minimum a length/word-count floor or a
check for one of a small set of required tokens (e.g. a number, "no
new", "N more") would make a one-character body fail the same way an
empty body already does.
