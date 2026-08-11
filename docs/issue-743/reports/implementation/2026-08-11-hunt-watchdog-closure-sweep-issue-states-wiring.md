---
proposal: docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md
---

# Hunt record — watchdog-closure-sweep-issue-states-wiring

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `record_no_tool_residue` (and its `_changed_records`/`RECORD_PATH`-scoped siblings `record_derived_counts`, `record_wellformed`, `record_enums`, `record_checked_claims`) never inspect nested-shape record files (`docs/issue-<n>/reports/<role>/*.md`, e.g. the `survey.md` just written for this issue) — only flat `docs/issue-<n>/reports/<role>.md` — even though `_always_writable()` in the same `gates.py` explicitly grants roles write permission to `docs/issue-*/reports/{role}/**`, and the repo's own tree uses that nested shape as the dominant convention (`implementation/` nested dirs outnumber flat `implementation.md` files in a repo-wide count). The write-time hook `record-claim-guard.sh` has no tool-residue check at all (it mirrors only the count/unverifiable/checked-claim/orphaned-path checks), so a leaked tool-transcript tag (e.g. `<function_results>`) landing in a nested-shape record file such as this very hunt record or the sibling `survey.md` is invisible at both write time and CI time.

Kind: silent-failure
Seed: docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md, docs/issue-743/reports/implementation/survey.md
cap_seconds: 60
tier: default (size:docs-only)
diff_stat_lines: 2 new files (docs-only)
started_at: 2026-08-11T05:33:00Z
ended_at: 2026-08-11T05:40:30Z

### Reproduce
```
GATES_DIR=/Users/jk/.tokenmaxxxer/work/on-the-record-issue-743-implementation/gates
SCRATCH=$(mktemp -d)
cd "$SCRATCH" && git init -q && git checkout -q -b main \
  && git config user.email t@t.com && git config user.name t
python3 - << 'PYEOF'
import os
base = os.path.join("docs", "issue-1", "reports")
os.makedirs(os.path.join(base, "implementation"), exist_ok=True)
open("README.md", "w").write("# seed\n")
with open(os.path.join(base, "implementation.md"), "w") as f:
    f.write("---\nloop_state: done\n---\nSome record body.\n<function_results>\nmore text\n")
with open(os.path.join(base, "implementation", "survey.md"), "w") as f:
    f.write("# Survey\nSome survey body.\n<function_results>\nmore text\n")
PYEOF
git add README.md && git commit -q -m seed && git update-ref refs/remotes/origin/main HEAD
python3 - << PYEOF
import sys; sys.path.insert(0, "$GATES_DIR")
import gates
from pathlib import Path
root = Path("$SCRATCH")
print("changed_files:", gates.changed_files(root))
print("record_no_tool_residue_in:", gates.record_no_tool_residue_in(root))
PYEOF
```

### Observed
```
changed_files: ['docs/issue-1/reports/implementation.md', 'docs/issue-1/reports/implementation/survey.md']
record_no_tool_residue_in: ["레코드에 툴 태그 잔여물: docs/issue-1/reports/implementation.md:5 — '<function_results>'. 에이전트 툴 출력이 레코드 본문에 새어들어왔다."]
```
Both files carry the identical `<function_results>` leaked tag on the same relative line, and `changed_files()` reports both as changed, but `record_no_tool_residue_in` (backed by `RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")` in both `gates/gates.py` and `on-the-record/gates/gates.py`) flags only the flat-path file. The nested-path file's identical residue is silently passed. `tests/test_gates.py`'s `t_record_no_tool_residue_*` tests only ever construct flat-path records (`_record_repo(td, "issue-9", "coding", ...)` → `coding.md`), so this gap is untested, not a deliberately-scoped exclusion — and `_always_writable()` (same file, `gates/gates.py` and `on-the-record/gates/gates.py`) explicitly lists `docs/issue-*/reports/{role}/**` as always-permitted role write territory, so the permission side and the content-check side disagree about which paths count as "the record."

### Expected
Either `record_no_tool_residue`/`record_derived_counts`/`record_wellformed`/etc. scope to the same path set `_always_writable()` grants (flat `<role>.md` **and** nested `<role>/**`), or `RECORD_PATH` documents why nested-shape files are deliberately exempt from tool-residue/count-claim/frontmatter scanning — currently neither is true, so a leaked tool-transcript tag or an unbacked count claim in any nested-shape report (survey.md, scout-brief.md, hunt records, etc. — the majority shape in this repo, including the two files this proposal's implementation phase just added) passes silently through every existing gate.
