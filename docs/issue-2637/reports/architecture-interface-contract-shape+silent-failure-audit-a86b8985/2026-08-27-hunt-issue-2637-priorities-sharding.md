---
proposal: (build-now — no proposal file; issue #2637, CORE_BUILD_NOW=1)
---

# Hunt record — issue-2637-priorities-sharding

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `PRODUCT_CAPTURE_PRIORITIES_DIR_RE` in deliverable-guard.sh is unanchored (uses `re.search`, no `^`), so any deliverable-shaped path that merely *ends with* the priorities-shard suffix is exempted, even when it is not actually inside `docs/reports/product/priorities/`.
Kind: composition
Seed: staged diff to on-the-record/hooks/deliverable-guard.sh, on-the-record/hooks/product-capture-stopgate.sh, on-the-record/hooks/skill-verdict-guard.sh (git diff --cached -- on-the-record/hooks/deliverable-guard.sh on-the-record/hooks/product-capture-stopgate.sh on-the-record/hooks/skill-verdict-guard.sh)
cap_seconds: 180
tier: size:hooks-touch
diff_stat_lines: 3 files changed, 61 insertions(+), 6 deletions(-)
started_at: 2026-08-27T18:04:00+09:00
ended_at: 2026-08-27T18:10:00+09:00

### Reproduce
```
mkdir -p /tmp/fake_target_repo && cd /tmp/fake_target_repo && git init -q
mkdir -p docs/specs && touch docs/specs/approvers.md

# control: a plain src/ deliverable write is correctly denied
python3 -c "
import json
print(json.dumps({
    'session_id': 'ctrl',
    'tool_name': 'Write',
    'tool_input': {'file_path': 'src/hack.md'},
    'cwd': '/tmp/fake_target_repo',
}))" > /tmp/payload_control.json
unset TOKENMAXXXER_SPAWNED
cat /tmp/payload_control.json | bash on-the-record/hooks/deliverable-guard.sh; echo "control exit=$?"

# exploit: same src/ deliverable write, but the path also contains the
# priorities-shard suffix as a nested subpath, not as the actual location
python3 -c "
import json
print(json.dumps({
    'session_id': 'exploit',
    'tool_name': 'Write',
    'tool_input': {'file_path': 'src/docs/reports/product/priorities/hack.md'},
    'cwd': '/tmp/fake_target_repo',
}))" > /tmp/payload_exploit.json
cat /tmp/payload_exploit.json | bash on-the-record/hooks/deliverable-guard.sh; echo "exploit exit=$?"
```

### Observed
Control (`src/hack.md`): exit 2, denied — "this is an orchestrator session and src/hack.md is a deliverable path in a board repo."
Exploit (`src/docs/reports/product/priorities/hack.md`): exit 0, silently ALLOWED — the guard exits clean with no stderr message, letting an orchestrator-session write land inside `src/` (deliverable territory) as long as the tail of the path happens to spell out the priorities-shard suffix. Confirmed the regex itself matches via unanchored `re.search`:
```python
import re
R = re.compile(r"docs/reports/product/priorities/[^/]+\.md$"
                r"|docs/issue-\d+/reports/product/priorities/[^/]+\.md$")
bool(R.search("src/docs/reports/product/priorities/hack.md"))  # -> True
```

### Expected
The exploit path is not inside `docs/reports/product/priorities/` at all — it is inside `src/docs/reports/product/priorities/`, an arbitrary deliverable-shaped location under `src/`. It should be denied identically to the control case (exit 2, "deliverable path in a board repo"), the same way `PRODUCT_CAPTURE_ISSUE_RE`'s sibling case would need `^` anchoring too. The new regex needs `^` (or `posixpath.dirname(n) == "docs/reports/product/priorities"` / equivalent exact-parent check) so a match requires the priorities-shard segment to start the path, not merely end it.
