---
proposal: docs/issue-547/proposals/2026-08-09-accumulation-claim-authoring-time.md
---

# Hunt record — accumulation-claim-authoring-time

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned .md branch reuses the existing hook's fragment-only content-reading pattern (Write `content` / Edit `new_string` / MultiEdit `edits[].new_string`), which never contains the full file; an `Edit` that only appends a new item to an already-open YAML `files:` list (without re-supplying the `files:` key line itself) produces a `new_string` fragment that parses as a bare list, not a mapping with a `files` key — so the planned "read the write's own new content for a YAML `files:` list" step finds no `files:` key and the branch treats the write as touching no `files:` list at all, exiting 0 without ever running the shape-1/shape-5 detectors, even though the resulting on-disk proposal now lists an accumulation-shaped path (e.g. `roles/x.json`) with no `## Accumulation` section filled.
Kind: design-error
Seed: docs/issue-547/proposals/2026-08-09-accumulation-claim-authoring-time.md ("What will be done" section: "on-the-record/hooks/accumulation-claim-guard.sh: add a branch ... It parses the write's own new content for a YAML files: list")
cap_seconds: 120
tier: default
diff_stat_lines: 2 new files (proposal + survey), no code changed yet
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:05:00Z

### Reproduce
Demonstrated the underlying mechanism the proposal explicitly commits to reusing — the existing hook's "join tool_input content fragments" pattern (seen in `accumulation-claim-guard.sh`'s `content_parts` construction from `ti.get("content")` / `ti.get("new_string")` / `edits[].new_string`, never a read of the resulting full file):

```
cd /tmp && python3 << 'PY'
import yaml
# Simulates an Edit tool_input.new_string that only appends one item to an
# already-open `files:` YAML list in a proposal, without re-including the
# `files:` key line itself:
new_string = "  - foo.py\n  - roles/x.json"
doc = yaml.safe_load(new_string)
print("parsed:", doc)
print("has 'files' key:", isinstance(doc, dict) and "files" in doc)
PY
```

### Observed
```
parsed: ['foo.py', 'roles/x.json']
has 'files' key: False
```
The fragment parses as a plain list, never a mapping with a `files:` key — so any parser matching the proposal's described approach ("reading the write's own new content for a YAML files: list") sees no `files:` list in this Edit and the branch would exit 0, skipping shape-1/shape-5 detection entirely for this write.

### Expected
An `Edit` that adds `roles/x.json` (shape 5) to a proposal's `files:` list — via an old_string/new_string pair scoped to the list body rather than the full frontmatter block — should still trigger the shape-5 check and deny if `## Accumulation` is missing, since the resulting proposal file on disk does contain the shape-5 path in its `files:` list. The proposal's plan, by parsing only the write's own fragment content (mirroring the current hook's `.py`-branch pattern) rather than the resulting full on-disk file, leaves this Edit shape unseen — a way to grow a proposal's `files:` list into an accumulation shape across multiple small edits that individually never surface a `files:` key to parse.
