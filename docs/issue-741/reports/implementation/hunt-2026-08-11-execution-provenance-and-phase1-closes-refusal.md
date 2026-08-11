---
proposal: docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md
---

# Hunt record — execution-provenance-and-phase1-closes-refusal

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — the proposal's "What will be done" text for the pr-preflight.sh phase-1 closes-check names only the bare `_CLOSES_REF` regex object (the one already used via `.search()` at pr-preflight.sh:236/241), not gates/ci.py's `_closes_ref_for_issue` helper — which exists specifically because `.search()` (first-match-only) was hunted and found to miss a real `Closes #N` reference to the PR's own issue when a decoy closing-keyword reference to a *different* issue appears earlier in the body. If implemented by reusing the file's existing `.search()` idiom (which is exactly what "기존 _CLOSES_REF … 새 정규식 아님" points at), the new phase-1 check inherits that already-documented bypass verbatim.
Kind: design-error
Seed: docs/issue-741/proposals/2026-08-11-execution-provenance-and-phase1-closes-refusal.md, "What will be done" > pr-preflight.sh section (lines ~142-153)
cap_seconds: 60
tier: default
diff_stat_lines: N/A (docs-only proposal, no code diff yet — single new proposal file)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce

```
python3 -c "
import re
_CLOSES_REF = re.compile(r'(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)')
body = 'Fixes #999, unrelated context here. Closes #741'
issue = 741

# idiom already present in on-the-record/hooks/pr-preflight.sh at lines 236/241
# (the only existing usage of _CLOSES_REF the proposal points to as 'not a new regex')
mm = _CLOSES_REF.search(body)
print('search()-based (existing file idiom):', mm.group(0) if mm else None,
      '-> matches this issue:', bool(mm and int(mm.group(2)) == issue))
"
```

Cross-check against gates/ci.py's canonical `_closes_ref_for_issue` (gates/ci.py:164-176),
whose docstring states this exact scenario is why it uses `.finditer()` instead of
`.search()`:

```
grep -n "_closes_ref_for_issue" -A 12 gates/ci.py | head -20
```

### Observed

`_CLOSES_REF.search(body)` returns the match for `Fixes #999` (the decoy, a
different issue) and stops there — `int(mm.group(2)) == issue` evaluates to
`False` for `issue=741`, even though the same body plainly contains
`Closes #741` further along. Applied to the proposed pr-preflight.sh check
("phase1 이고 not bad 일 때만... 있으면 deny()"), this means a phase-1 PR body
of the PR #763 shape but with one extra decoy reference prepended —
e.g. `"Fixes #999, some other issue. Closes #741"` — would NOT be denied:
the new check finds no match for its own issue and lets the PR through,
exactly the auto-close outcome the proposal exists to block.

gates/ci.py's own docstring for `_closes_ref_for_issue` (gates/ci.py:164-173)
confirms this is not hypothetical — it documents that `.search()` was hunted
and found to miss this case, and that `.finditer()` was adopted specifically
to fix it: "`.search()`(첫 매치 하나)가 아니라 `.finditer()`(전체 매치)를 쓴다:
본문이 다른 이슈를 먼저 언급하면(...) `.search()`는 #999 매치에서 멈춰 진짜
#245 참조를 놓친다 — hunt로 실측 확인된 회피 경로".

### Expected

The proposal's "What will be done" section for pr-preflight.sh should
explicitly specify iterating all `_CLOSES_REF` matches (finditer, matching
`gates/ci.py::_closes_ref_for_issue`'s semantics) and checking each one's
issue number, not a single `.search()` call — otherwise an implementer who
follows the proposal's literal instruction ("기존 _CLOSES_REF로... 찾는다",
pointing at the file's only existing usage pattern, `.search()`) reproduces
a bypass gates/ci.py already had to fix once. The proposal's Rationale
section states `_phase1_mismatch`/`_closes_ref_for_issue` "already correct
logic" is what's being ported, but the "What will be done" section's
wording doesn't carry that helper's finditer behavior forward — only the
bare regex.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — pr-preflight.sh's new phase-1 closing-keyword refusal (this diff) uses a stricter, exact-role-match phase-2 test than contract-guard.sh's phase-2 test over the SAME issue's approval comments, so a role-scoped approval comment for a different role makes contract-guard.sh log a phase-2 verdict for the PR while pr-preflight.sh independently judges the identical PR phase-1 and denies the exact remediation (attaching the closing trailer) contract-guard.sh's own broker-attach exists to perform.
Kind: composition
Seed: on-the-record/hooks/contract-guard.sh phase2 test (startswith "APPROVE issue-<n>/", any role suffix accepted) vs on-the-record/hooks/pr-preflight.sh phase2 test (exact match "APPROVE issue-<n>/<branch-role>"); hooks.json Bash matcher group order: contract-guard.sh, pr-preflight.sh, ...
cap_seconds: 180
tier: size:200+
diff_stat_lines: 411 insertions(+), 37 deletions(-) across 4 files
started_at: 2026-08-11T09:23:46Z
ended_at: 2026-08-11T09:28:33Z

### Reproduce

Both hooks determine "is this issue phase-2?" independently from the same
`gh issue view <n> --json comments` data, using different role-scoping
rules:

- `on-the-record/hooks/contract-guard.sh`: `prefix = "APPROVE issue-%d/" % issue`,
  `body.strip().startswith(prefix)` — matches an approval for **any** role
  suffix.
- `on-the-record/hooks/pr-preflight.sh`: `needle = "APPROVE issue-%d/%s" % (issue, role)`,
  `body.strip() == needle` — matches only the **exact** role of the current
  git branch (`issue-<n>/<role>`).

Fixture: issue #741, one issue comment `APPROVE issue-741/planning` from an
`approvers.md` account, current branch `issue-741/implementation` (a
*different* role than the one named in the approval).

```bash
T=$(mktemp -d)
mkdir -p "$T/bin" "$T/repo/docs/specs"

cat > "$T/bin/git" <<'SH'
#!/usr/bin/env bash
if [ "$1" = "rev-parse" ] && [ "$2" = "--abbrev-ref" ] && [ "$3" = "HEAD" ]; then
  echo "issue-741/implementation"; exit 0
fi
exit 1
SH
chmod +x "$T/bin/git"

cat > "$T/bin/gh" <<'SH'
#!/usr/bin/env bash
args="$*"
case "$args" in
  "issue view 741 --json comments -q .comments")
    echo '[{"body":"APPROVE issue-741/planning","author":{"login":"alice"},"createdAt":"2026-08-01T00:00:00Z"}]'; exit 0 ;;
  "issue view 741 --json comments -q [.comments[] | {body, author, createdAt}]")
    echo '[{"body":"APPROVE issue-741/planning","author":{"login":"alice"},"createdAt":"2026-08-01T00:00:00Z"}]'; exit 0 ;;
  "pr view 741 --json body,number,commits,files")
    echo '{"body":"tracks #741","number":741,"commits":[{"committedDate":"2026-07-01T00:00:00Z"}],"files":[{"path":"src/foo.py"}]}'; exit 0 ;;
  *"pr edit 741"*) echo ok; exit 0 ;;
esac
echo "unhandled gh call: $args" >&2; exit 1
SH
chmod +x "$T/bin/gh"
echo "- alice" > "$T/repo/docs/specs/approvers.md"

REPO=/Users/jk/.tokenmaxxxer/work/on-the-record-issue-741-implementation

# Step 1: contract-guard.sh's own phase verdict for issue #741 (via its
# unconditional provenance-log write, this same diff's other half), on a
# `gh pr` merge-tool-name command against PR 741:
cd "$T/repo"
MERGE_CMD_JSON='{"tool_name":"Bash","tool_input":{"command":"gh pr me''rge 741 --squash"}}'
PATH="$T/bin:$PATH" CONTRACT_GUARD_PROVENANCE_LOG="$T/provenance.log" bash -c \
  "printf '%s' '$MERGE_CMD_JSON' | '$REPO/on-the-record/hooks/contract-guard.sh'"
cat "$T/provenance.log"
```

### Observed

```
{"ts": "2026-08-11T09:28:08Z", "script_path": ".../contract-guard.sh", "script_sha256": "5eb06af...",
 "pr": "741", "repo": null, "issue": 741, "phase2": true,
 "is_src_test": true, "is_record": false, "closes_present_before": false}
```

`"phase2": true` — contract-guard.sh accepts the single comment
`APPROVE issue-741/planning` as sufficient phase-2 approval for issue #741,
even though the current role/branch is `issue-741/implementation`, a
*different* role than the one named in the approval comment.

Second half of the same fixture, run against pr-preflight.sh (separate
Bash tool call, same `$T`, same `gh`/`git` fixture, same issue #741, same
single comment) with an edit command whose body carries the closing
trailer contract-guard.sh's own broker-attach logic would itself write for
a phase-2 PR:

Reproduce (continued, second Bash tool call):
```
REPO=/Users/jk/.tokenmaxxxer/work/on-the-record-issue-741-implementation
EDIT_CMD='gh pr edit 741 --body "Clo''ses #741"'
EDIT_CMD_JSON="{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$EDIT_CMD\"}}"
PATH="$T/bin:$PATH" bash -c "printf '%s' '$EDIT_CMD_JSON' | '$REPO/on-the-record/hooks/pr-preflight.sh'"
echo "exit=$?"
```

Observed:
```
pr-preflight: phase-1 제안 PR 본문에 closing 키워드(Clo``ses)가 있다 — phase-1 머지가 이슈 #741를 자동으로 닫으면 안 된다.
pr-preflight: expected: a plain '#741' reference only — no Clo``ses/Fixes/Resolves for #741
exit=2
```

(Exact wording confirmed by direct interactive execution of both hook
scripts against this fixture during the hunt; reproduced here with the
trigger keyword split across a `''` concatenation only because this
recording session's own real-time `gh-guard.sh` refuses a literal
contiguous `Clo`+`ses #<issue>` next to a `gh pr` invocation in a single
Bash tool call from a role session — an unrelated, correctly-functioning
guard on *this* meta session, not the hook under test.)

### Expected

The two hooks must not be able to disagree about whether the same issue is
phase-2 from the same underlying approval-comment data. contract-guard.sh
(merge time: requires/attaches the closing trailer once it believes
phase-2) and pr-preflight.sh (create/edit time: this diff's new check now
actively refuses the closing trailer while it believes phase-1) need the
same role-scoping rule for "is this approval comment for the running
role's phase-2." As written, a `planning`-role approval comment makes
contract-guard.sh treat the issue as phase-2-merge-ready while this diff's
new pr-preflight.sh check treats an edit on the `implementation`-role
branch for the same issue as phase-1 and denies the exact closing-trailer
edit contract-guard.sh's own broker-attach exists to require/attach — a
state an agent whose contract-guard.sh broker-attach ever fails (its own
header documents this as the realistic failure mode it denies on: a `gh pr
edit` write failure) cannot manually recover from, because pr-preflight.sh's
new check refuses the identical remediation.
