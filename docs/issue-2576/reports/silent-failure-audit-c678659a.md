---
issue: 2576
role: silent-failure-audit-c678659a
author: silent-failure-audit-c678659a
code_under_review:
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/delegation-post-gate.sh
type: fix
breaking: false
canonical: bash /tmp/run_pr_preflight_test.sh (executed this session, both single-skill and multi-skill worktrees) — result: exit 0 in both cases (see fenced output in body)
verdict: pass
loop_state: landed
upstream:
  - path: on-the-record/hooks/approval-gate.sh:275 (pre-fix `_CITE_RE`)
    sha: same-commit
---

# issue-2576 — silent-failure-audit-c678659a record

## What was done

Widened the `_CITE_RE` delegation-citation regex's slug capture group from
`[\w-]+` to `[^/]+` in the three hooks that parse an
`APPROVE issue-<n>/<slug> VIA DELEGATION <scope>` comment:

- `on-the-record/hooks/approval-gate.sh:275`
- `on-the-record/hooks/pr-preflight.sh:191`
- `on-the-record/hooks/delegation-post-gate.sh:84`

This mirrors the branch-name regex (`^issue-(\d+)/([^/]+)$`) already
converted to `[^/]+` in PR #2586 (`approval-gate.sh:140,163`,
`pr-preflight.sh:130`) — a multi-skill `--skills` spawn produces a slug
containing `+` (e.g. `silent-failure-audit+work-in-english-c678659a`),
which `[\w-]+` cannot match. No other regex in these three files needed
the same change: `_DELEGATE_RE`/`_REVOKE_RE`'s scope group is already
`\S+` (permissive), and the downstream cross-check
(`cm.group(2) != role` at `approval-gate.sh:312`,
`pr-preflight.sh:227`) compares the parsed slug against the same
`[^/]+`-derived branch role, so the two now agree on alphabet.

## Why

`silent-failure-audit-c678659a`'s (this role's) applicable lens: a hook
whose decision-logic condition stops matching a now-valid identity shape
is a **Silently Absorbed** failure (skill: `silent-failure-audit` —
catalog pattern "condition doesn't match a new valid shape, execution
continues as if there was nothing to check"), not a visible error.

canonical: this session's live pre-fix/post-fix hook runs, quoted verbatim
in `## Verification` below (`delegation-post-gate.sh`,
`approval-gate.sh`, `pr-preflight.sh` transcripts) — confirmed two
distinct blast radii for the `[\w-]+` vs `+`-bearing slug mismatch:

- **`delegation-post-gate.sh` (fail-open direction, the dangerous one):**
  `if not _CITE_RE.match(body.strip()): sys.exit(0)` treats an unparsed
  multi-skill citation as "not a citation — not this hook's target" and
  exits 0, skipping the self-approval check entirely. Pre-fix, a
  spawned, multi-skill role session posting its own delegation citation
  was silently allowed through (`exit: 0`). Post-fix, the same payload is
  denied (`exit: 2`), matching what a single-skill slug already got.
- **`approval-gate.sh` / `pr-preflight.sh` (fail-closed direction, the
  one issue #2576's brief flagged):** an unparsed citation is silently
  skipped in the comment-scan loop (`if not cm or login not in
  approvers: continue`), so a live, correctly-posted delegation grant for
  a multi-skill role is never recognized — pre-fix, `approval-gate.sh`
  denied the write (`exit: 2`), and `pr-preflight.sh` additionally
  misclassified the PR as phase-1 (since `phase2` never flipped true)
  and fired the *phase-1 closing-keyword* refusal against a legitimate
  phase-2 `Closes #<n>` body — a confusing, unrelated-looking denial.
  Post-fix, both `exit: 0`.

`[^/]+` was chosen (not, say, `[\w+-]+`) specifically to stay
byte-identical to the branch regex's own alphabet, since the parsed slug
is cross-checked against the branch-parsed role downstream — widening
past what a legal branch-name segment can contain would let the two
diverge silently. Verified below that they don't.

## What did not work

None.

## Upstream basis

- `on-the-record/hooks/approval-gate.sh:140,163` and
  `on-the-record/hooks/pr-preflight.sh:130` — the branch-regex
  `[^/]+` conversion landed in PR #2586 (commit 96699800), same `+`-root
  cause this fix closes on the citation-regex side.
- issue #2576 (parent), task brief embedded in this session's spawn
  prompt (residual-finding scope: the three files/lines above, non-goals:
  branch regexes, `delegated-judgment-gate.sh`).

## Open findings

None opened by this session. `delegated-judgment-gate.sh` is an explicitly
deferred Open finding on issue #2576, out of this session's scope per the
spawn prompt's non-goals — left untouched.

## Verification

canonical: this session's own live command transcripts below (regex unit
check + three full-process hook runs in throwaway `git worktree`s,
removed after use) — not a summary of a prior run, executed fresh this
session.

Regex-level parse equivalence (both single- and multi-skill slugs):

```
$ python3 -c "
import re
_CITE_RE = re.compile(r'^APPROVE issue-(\d+)/([^/]+) VIA DELEGATION (\S+)\$')
for t in [
    'APPROVE issue-2576/silent-failure-audit-c678659a VIA DELEGATION issue-2576/backup-approver',
    'APPROVE issue-2576/silent-failure-audit+work-in-english-c678659a VIA DELEGATION issue-2576/backup-approver',
]:
    m = _CITE_RE.match(t)
    print(bool(m), m.groups() if m else None)
"
True ('2576', 'silent-failure-audit-c678659a', 'issue-2576/backup-approver')
True ('2576', 'silent-failure-audit+work-in-english-c678659a', 'issue-2576/backup-approver')
```

Live full-process run of all three hooks, real stdin PreToolUse payloads,
single-skill vs. multi-skill role (`skill-a+skill-b-test`), in two
throwaway `git worktree`s (`issue-9999/single-skill-test`,
`issue-9999/skill-a+skill-b-test`, both removed and branches deleted after
the run — never pushed, never issue #2576's own worktree):

**`delegation-post-gate.sh`** — spawned session posting a self-authored
delegation citation, `TOKENMAXXXER_SPAWNED=1`:

```
=== single-skill slug ===
delegation-post-gate: a role-bound session attempted to post a
delegation-citing APPROVE comment (...) — only an orchestrator session
(not spawned) may cite a delegation record as APPROVE provenance...
exit: 2

=== multi-skill slug (with +), POST-fix ===
delegation-post-gate: a role-bound session attempted to post a
delegation-citing APPROVE comment (...) — only an orchestrator session
(not spawned) may cite a delegation record as APPROVE provenance...
exit: 2

=== multi-skill slug (with +), PRE-fix (old [\w-]+ regex) ===
exit: 0        <- silent bypass: citation went unrecognized, gate no-opped
```

**`approval-gate.sh`** — phase-2-shaped `Write` to a synthetic
`src/test-target.py` path (untracked, inside the throwaway worktree only,
never a real repo path — the hook only pattern-matches the path shape,
it does not require the file to exist), fake `gh` serving a live
`DELEGATE ... UNTIL 2099-01-01` grant plus the matching
`APPROVE ... VIA DELEGATION ...` citation from a
`docs/specs/approvers.md`-listed login, `CORE_BUILD_NOW` unset for the
test:

```
=== single-skill slug ===
exit: 0

=== multi-skill slug (with +), POST-fix ===
exit: 0

=== multi-skill slug (with +), PRE-fix (old [\w-]+ regex) ===
approval-gate: no matching 'APPROVE issue-9999/skill-a+skill-b-test'
issue comment ... was found — this phase-2-shaped write ... needs
phase-2 approval first.
exit: 2
```

**`pr-preflight.sh`** — `gh pr create --body "... Closes #9999"`, same
fake-`gh` delegation grant/citation:

```
=== single-skill slug ===
exit: 0

=== multi-skill slug (with +), POST-fix ===
exit: 0

=== multi-skill slug (with +), PRE-fix (old [\w-]+ regex) ===
pr-preflight: phase-1 제안 PR 본문에 closing 키워드(Closes)가 있다 —
phase-1 머지가 이슈 #9999를 자동으로 닫으면 안 된다.
exit: 2        <- misclassified as phase-1 (citation never recognized),
                  then refused for a phase-1 rule that doesn't apply
```

acceptance: `python3 -m pytest test/test_approval_gate_carriers.py test/test_approval_role_field.py test/test_auto_approval_shadow_wiring.py -q` — result:

```
.........................                                                [100%]
25 passed in 1.03s
```

skill-verdict: silent-failure-audit — applied: invoked; used the
Handled/Silently-Absorbed/Unreachable lens to classify the two blast
radii above (`delegation-post-gate.sh` fail-open vs.
`approval-gate.sh`/`pr-preflight.sh` fail-closed) and to justify why
`[^/]+` (matching the branch regex's own alphabet) is the correct fix
rather than a broader class.
skill-verdict: work-in-english — not-applicable: this session's own
prose/commits/PR are already English; the skill's Korean-trigger
condition is about the *user's* language, not this record's.
other mounted skills: not triggered

## Next steps

None — landed in this session's PR.
