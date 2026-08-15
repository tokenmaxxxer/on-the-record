---
subject: issue-1199
role: upstream-defect-report
kind: record
loop_state: handed-off
---

# Record: upstream-defect-report tool-landscape fold-in (issue-1199)

## What was done

Executed the phase-2 fold-in under the `APPROVE issue-1199/upstream-defect-report`
comments on this issue (single-account mode; canonical: `gh issue view 1199
--comments`, read this session — the exact string `APPROVE
issue-1199/upstream-defect-report` posted twice by author JiwonJung94, an
approvers.md account per `docs/specs/approvers.md`, read this session).

Surveyed the Claude Code plugin/skill ecosystem (2026-08-14 operator
amendment scope — plugins/skills, not general domain tools) for tools
relevant to this role's own domain (observing a suspected defect, checking
it is not already known, and drafting a filed report), adoption evidence
via the tech-feasibility method:

- **trailofbits/skills**, `fp-check` skill. Adoption: canonical: `curl -s
  https://api.github.com/repos/trailofbits/skills`, run this session →
  `"stargazers_count": 6591, "forks_count": 567`. Problem: a suspected
  defect reported straight off first detection risks being a false
  positive (canonical: WebFetch of
  `https://github.com/trailofbits/skills/tree/main/plugins/fp-check`, run
  this session, quoting the skill's own framing: it "enforces systematic
  false positive verification when verifying suspected security bugs").
  How: every claim goes through mandatory gate reviews before a final
  TRUE POSITIVE / FALSE POSITIVE verdict is issued, with two escalation
  checkpoints routing complex cases to a deeper, parallel-phase
  verification track instead of one linear checklist run (canonical:
  same WebFetch this session). Learning → `playbook/subtraction.md` rule 7:
  before filing, re-run the exact reproduction against current state as a
  dedicated verification step separate from the original observation —
  a defect that looked real at observation time can be stale by filing
  time, and a false-positive upstream report costs the maintainer the
  same triage load as a true one.

- **FlorianBruniaux/claude-code-ultimate-guide**, `examples/skills/
  issue-triage` skill. Adoption: canonical: `curl -s
  https://api.github.com/repos/FlorianBruniaux/claude-code-ultimate-guide`,
  run this session → `"stargazers_count": 5728, "forks_count": 751`,
  description "The most comprehensive Claude Code guide ... 430K+ lines."
  Problem: a plain keyword search misses a duplicate filed under different
  wording. canonical: `curl -s https://raw.githubusercontent.com/
  FlorianBruniaux/claude-code-ultimate-guide/main/examples/skills/
  issue-triage/SKILL.md`, run this session, fenced excerpt:
  ```
  | `jaccard_threshold` | 60% | Minimum Jaccard similarity to flag two issues as duplicates |
  | `closed_compare_count` | 20 | Number of recent closed issues to compare for duplicate detection |
  ...
  # Recent closed issues (for duplicate detection)
  gh issue list --state closed --limit 20 \
    --json number,title,body,labels,stateReason
  ```
  How: canonical: same fenced excerpt directly above — the skill fetches
  both the open backlog and a fixed window of the last 20 recently closed
  issues, flagging a duplicate by the Jaccard-similarity threshold shown
  above rather than one keyword match. Learning → `playbook/
  convention.md` rule 7: canonical: same fenced excerpt above — dedup by
  overlap comparison against both the open backlog and the last 15-20
  closed issues, not a single free-text keyword search.

Considered a third candidate (`mattpocock/skills`) and declined it: canonical:
`curl -s https://api.github.com/repos/mattpocock/skills`, run this session
→ `"stargazers_count": 217679` against `"created_at":
"2026-02-03T11:15:53Z"` (roughly six months old at check time) — an
implausible star count for that repo age, so this session did not use it
as adoption evidence.

Applied (not referenced) both learnings directly into the named target
files in the mounted rulebook repo
(`tokenmaxxxer/upstream-defect-report-rulebook`, cloned to
`/tmp/udr-rulebook` this session — no prior local mount existed for this
role), branch `issue-1199/upstream-defect-report` — rule 7 appended to
`playbook/subtraction.md` and rule 7 appended to `playbook/convention.md`.
canonical: `git -C /tmp/udr-rulebook diff --stat`, run this session,
output:
```
playbook/convention.md  | 10 ++++++++++
playbook/subtraction.md | 10 ++++++++++
2 files changed, 20 insertions(+)
```
Per the operator's native-application amendment (2026-08-13T06:36:54Z):
no `source:` line names `trailofbits/skills` or
`FlorianBruniaux/claude-code-ultimate-guide` by repo name in the
rulebook text, and no tool-catalog section was added — each new rule
reads as this role's own judgment. canonical: `git -C /tmp/udr-rulebook
diff | grep -iE "trailofbits|fp-check|florianbruniaux|issue-triage"`, run
this session, no match outside this record. No verbatim text was copied
from either surveyed source; both rules are paraphrased insight.

Committed in the rulebook repo (commit 5a4c0ab, subject: "issue-1199:
fold in Claude Code plugin-ecosystem tool-landscape learnings"; canonical:
`git -C /tmp/udr-rulebook log -1 --stat`, run this session), pushed to
`origin/issue-1199/upstream-defect-report`.

## Delivery blocked: both PR-create and issue-create refused for this role

canonical: this session's own `gh pr create` invocation against
`tokenmaxxxer/upstream-defect-report-rulebook` (run in `/tmp/udr-rulebook`)
and its captured stderr, exit code 2:
```
upstream-defect-scope-guard: `gh pr create` (including a GH_REPO/GH_HOST-env-var-prefixed invocation) is denied — the upstream defect channel files issues only, never PRs (issue #1131 req#4).
```

canonical: `on-the-record/hooks/upstream-defect-scope-guard.sh` lines
18-26 (header comment) and lines 117-126 (`in_scope()`), read this
session, fenced quote of `in_scope()`:
```
def in_scope(target_repo):
    """PR-creation call is in-scope for denial iff the channel's own role
    is active, or a target repo was extracted and it isn't this session's
    origin repo. `target_repo=None` (no extractable target, or origin
    unresolvable) relies on the role signal alone."""
    if channel_role_active:
        return True
    if target_repo is not None and ORIGIN_REPO is not None:
        return target_repo.lower() != ORIGIN_REPO
    return False
```
The header comment (lines 18-26, same file) states #1171's intent: "deny
only within the upstream-defect channel's own flow, never a role
session's own delivery PR against origin." `in_scope()` never reaches an
origin-equality check when `channel_role_active` is true — the exemption
the comment describes is not implemented in the code path this role
actually hits (canonical: same fenced quote directly above). Following
this role's own `write_scope` (`docs/reports/upstream-findings/`),
attempted to file this as an upstream issue instead — canonical: this
session's own `gh issue create --repo tokenmaxxxer/on-the-record`
invocation and its captured stderr:
```
gh-guard: refused for role session 'upstream-defect-report': issues are the user's requirement backlog, user-authored only (contract v3 s9) — no role touches them. (two-account model, contract v3 s8)
```
Both filing paths (a PR against this repo carrying the finding, and a
`gh issue create` against this repo) were mechanically refused for this
role this session. Recorded as a local fallback per this role's own
`write_scope`: `docs/reports/upstream-findings/
2026-08-15-scope-guard-blocks-own-delivery-pr.md` (committed this
session, commit d0457b01; canonical: `git log -1 --stat -- docs/reports/
upstream-findings/2026-08-15-scope-guard-blocks-own-delivery-pr.md`, run
this session).

Per this session's own controlling instruction ("push/PR가 network으로
막히면 커밋까지는 해 둬라: on-the-record가 밖에서 릴레이한다") and the
same precedent already logged in this issue's history for other roles
hitting a PR-create block (canonical: `docs/issue-1199/reports/
conformance-review.md`, section "pr-preflight comment-race," read this
session; `docs/issue-1174/reports/upstream-defect-report.md`, section
"pr-preflight comment-race (why no PR is opened yet)", read this
session): this session stops retrying `gh pr create`/`gh issue create`
after this reconciliation, and leaves both branches committed and pushed
for on-the-record's outside relay to open the rulebook PR and this
repo's own delivery PR, and to file the scope-guard finding upstream.

## Why

Per issue-1199 (northpole req#1): this role's own rulebook encoded
methodology from #1174 but had not learned from the Claude Code
plugin/skill ecosystem's own solved problems for this domain (verifying a
suspected defect before reporting it, and telling a true duplicate from a
freshly-worded re-report). `fp-check` and the `issue-triage` skill are the
closest direct-domain matches surveyed this session — both operate on
exactly this role's own two hardest judgment calls (is this real, is this
new), so their design moves transfer without needing translation from an
unrelated domain.

## Upstream basis

docs/issue-1199 (issue body, requirements 1-4, 2026-08-14 plugin-ecosystem
amendment); `docs/issue-1199/reports/conformance-review.md` (accepted
record shape, read this session as the shape precedent this record
follows); `docs/issue-1174/reports/upstream-defect-report.md` (this
role's own prior rulebook-repo mount path and pr-preflight-block
precedent).

## What did not work

`gh pr create` (rulebook repo and this repo) and `gh issue create` (this
repo) were both mechanically denied by this session's own role scope
guards (see "Delivery blocked" section above) — not a network failure, a
structural block this role cannot lift from inside its own session.

## Open findings

1. `on-the-record/hooks/upstream-defect-scope-guard.sh`'s `in_scope()`
   denies this role's own delivery PR against its own repo's origin,
   contradicting the guard's own #1171 header-comment intent and contract
   v3 s19's PR-delivery requirement (see "Delivery blocked" section above
   for the canonical diagnosis). Recorded locally at `docs/reports/
   upstream-findings/2026-08-15-scope-guard-blocks-own-delivery-pr.md`
   (committed this session, commit d0457b01) since live upstream filing
   was also refused this session; that file is this finding's resolution
   path pending an outside filing.

## next steps

on-the-record's outside relay opens the PR from
`issue-1199/upstream-defect-report` (commit 5a4c0ab) against
`tokenmaxxxer/upstream-defect-report-rulebook`'s main, the PR from this
branch against this repo's main, and files the scope-guard finding
(`docs/reports/upstream-findings/2026-08-15-scope-guard-blocks-own-delivery-pr.md`)
as an upstream issue.

## resolution path

Once `in_scope()` in `upstream-defect-scope-guard.sh` exempts a target
repo equal to `ORIGIN_REPO` before the role check (matching its own
header comment's stated intent), this role's own future delivery PRs
against `origin` stop being blocked, and this role can also verify
whether `gh-guard.sh`'s issues-are-user-authored-only rule is intended to
apply to this specific report_only channel or needs its own carve-out.
Until then, both branches stay committed and pushed, and the finding
stays recorded locally, available for relay or manual filing from
outside this role's session.
