# issue-1818 phase-1 survey: APPROVE-needle consumers, structured-record carrier

canonical: gh issue view 1818

Scout skip: the candidate carrier set is closed by what's already
established in this exact file for exactly this kind of GH-API-derived
data (the ETag comment cache, `_etag_cache_path`); there is no external
product to benchmark a repo-internal cache-record format against. This
is the current-state read the issue's "decide the carrier with #1814's
reachability method" line asks for.

## Which sites the needle touches, and which this issue does and does not

```
$ derived: grep -rn "_approved_roles_on_issue" --include=*.py .
gates/ci.py:189:def _approved_roles_on_issue(repo: Path, issue: int) -> set[str]:
gates/ci.py:222:    approved_roles = _approved_roles_on_issue(repo, issue)
gates/ci.py:544:    found = ", ".join(sorted(_approved_roles_on_issue(repo, issue))) or "없음"
gates/landing_readiness.py:155: has_approval = role in ci._approved_roles_on_issue(root, issue)
gates/spawn_on_pr.py:260:    return role not in _ci._approved_roles_on_issue(root, issue)
spawn.py:1067: approved_roles = _ci._approved_roles_on_issue(root, issue)
spawn.py:1110: approved_roles = _ci._approved_roles_on_issue(root, issue)
spawn.py:1299: approved_roles = _ci._approved_roles_on_issue(root, pr["issue"])
```

Every python consumer of the APPROVE needle funnels through the single
function `_approved_roles_on_issue` defined at `gates/ci.py:189` —
`landing_readiness.py`, `spawn_on_pr.py`, and all three `spawn.py` call
sites call it directly; none of them re-implements the needle match
independently. Migrating this one function's read path covers every
python consumer in one edit.

`approval-gate.sh:182` (`needle = "APPROVE issue-%d/%s" % (issue,
role)`) is a **separate, independent** exact-match implementation in a
different language/process (bash-embedded Python heredoc,
`on-the-record/hooks/approval-gate.sh`) — it does not call
`_approved_roles_on_issue` and is not touched by editing that function.
The issue body names this explicitly as entry 5, out of scope here:

```
$ derived: grep -n "needle = " on-the-record/hooks/approval-gate.sh
on-the-record/hooks/approval-gate.sh:182:needle = "APPROVE issue-%d/%s" % (issue, role)
```

So the map is: **this issue migrates** the one python funnel-point
(`_approved_roles_on_issue` at `gates/ci.py:189`, and transitively every
python caller listed above); **this issue does not touch**
`approval-gate.sh`'s own needle build/match (frozen migration order
entry 5, a later sub-issue).

## Who "issues" an approval, and where a dual-write would fire

```
$ derived: grep -n "gh issue comment\|gh pr review\|--approve" spawn.py gates/ci.py
(no matches)
```

No code path in this repo posts the `APPROVE issue-<n>/<role>` comment
itself — per role-handoff contract v3 s19, approval is always a human
account (listed in `docs/specs/approvers.md`) typing the exact string
into a GitHub comment. There is no "approval-issuing" code to dual-write
from at the write-the-comment moment; the only code that runs whenever
an approval is *acted on* is `_approved_roles_on_issue` itself, called
from the "normal orchestration flow" sites above (`spawn.py`'s phase
checks, `landing_readiness.py`, `spawn_on_pr.py`). That is the
observation point available to dual-write from.

## Existing precedent for this exact kind of record: the ETag comment cache

```
$ derived: sed -n '1327,1332p' spawn.py
def _etag_cache_path(root: Path, number: int) -> Path:
    """이슈 #1459: `number` 스레드의 ETag 조건부-재조회 캐시 위치.
    `.git/` 아래(레포별, 워크트리 공유)에 둔다 — 커밋되지 않고, 레포
    삭제/재클론 시 자연히 사라진다."""
    return root / ".git" / "gh-read-cache" / f"issue-{number}-comments.json"
```

`spawn.py` already has an established, working convention for exactly
this shape of data — a derived cache of GH-API comment data, keyed by
issue number, stored uncommitted under `.git/gh-read-cache/` inside the
workspace, self-clearing on reclone. `_issue_comments`, defined at
`spawn.py:1368`, already reads/writes this cache on every call;
`_approved_roles_on_issue` (`gates/ci.py:189`) already calls
`spawn._issue_comments`, so the same `root` (workspace checkout) is
already in scope at the exact call site that would need to read a
structured approval record.

This is the #1814-style reachability read applied to *this* consumer:
#1814 found the branch-role carrier had to be picked per-site because
its four sites did not share one reachable medium (a live-session
directive file, a workspace sidecar, and a PR-body trailer were not
interchangeable). Here there is exactly **one** python funnel-site
(`_approved_roles_on_issue`), and it already has a workspace-root
(`repo: Path`) parameter and an established uncommitted-cache
convention at that exact call site — no per-site split is needed, and
no new carrier convention needs inventing.

## Reachability of `.git/gh-read-cache/` vs. alternatives

- **Workspace-local file under `.git/gh-read-cache/`** (chosen — see
  proposal Rationale): reachable from every listed python call site,
  since all of them receive the same `root`/`repo: Path` workspace
  checkout that `_issue_comments` already keys its own cache off of. No
  network call beyond what `_approved_roles_on_issue` already makes
  (the comment scan itself, on cache miss). Not committed — cleared on
  reclone, matching the ETag cache's own stated behavior; a fresh
  checkout falls back to the needle scan exactly like it does today
  (satisfies the "legacy/absence case resolves byte-identically"
  requirement trivially, since the fallback path *is* today's unmodified
  code).
- **Repo-committed file** (e.g. under `docs/issue-<n>/`): rejected —
  see proposal Rationale; would require every approval detection to
  produce a *commit*, which role-handoff contract v3 s13's one-subject
  one-commit trailer rule and the deviation-loop's SCOPE-EXCEEDED rule
  both make heavier than a cache write, for no reachability gain over
  the workspace-local file (every consumer here already resolves the
  same workspace root).
- **A second, machine-readable issue comment** (e.g. auto-posted
  alongside the human's token comment): rejected — nothing in this
  repo posts comments as a side effect of *reading* approval state
  (only humans post the token today), and inventing a bot-posted
  comment would need write scope (`gh issue comment`) at every
  `_approved_roles_on_issue` call site, a new network-write dependency
  the read-only funnel does not have today.

## Open finding: staleness is a cache-coherence question, not a design gap

Because the structured record is *derived from* the same comment scan
`_approved_roles_on_issue` already performs (a write-through cache, not
an independently-computed value), "read structured record when present,
else re-scan" cannot itself diverge from "always re-scan" for any role
already recorded — the record is populated from, and only from, the
comment scan's own result. The one input that can change after a record
is written is a *new* approval or a *new* role, which the record
doesn't yet know about; the proposal's read path must therefore still
consult the live comment scan for roles the record has not yet
captured, not treat the record as an exhaustive substitute. This is
the deciding fact for the proposal's read-path design (merge, not
replace).
