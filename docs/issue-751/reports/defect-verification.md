---
subject: issue-751
role: defect-verification
kind: verify-record
loop_state: reproduced
---

# Defect-verification record — inter-agent comm audit vs northpole req#5

Phase-2 record per role-handoff contract v3 s19, gated behind the
`APPROVE issue-751/defect-verification` comment.
canonical: `gh issue view 751 --comments` (run this session) shows the
comment "APPROVE issue-751/defect-verification" posted by author
JiwonJung94, association member — satisfying single-account-mode approval.

code_under_review:
- spawn.py
- on-the-record/hooks/delegated-judgment-gate.sh
- docs/specs/northpole.md
- docs/specs/platform-capabilities.md

closed_checks cited (not re-derived): docs/issue-751/reports/architecture/survey.md's
OF-1..OF-4 verdicts as findings-of-fact are cited, not re-litigated; only
their line citations are re-derived below against current HEAD, per this
role's phase-1 survey (docs/issue-751/reports/defect-verification/survey.md).

canonical: `git rev-parse --short HEAD` (run this session) = 74315c9.

## Attempts and outcomes

**Attempt 1 (source: architecture survey OF-1 — "no mechanism forwards a
predecessor role's board-record body into a successor's spawn-time task
string").** Outcome: **reproduced.**
canonical: spawn.py:5037-5096 (read this session). `_spawn_one()` is at
spawn.py:5037. Its task template is a fixed Korean string built at
spawn.py:5083-5096:
```
task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
        f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
        f"완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
        ...
        f"마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n\n") + task
```
This is a fixed instruction prefix concatenated with the caller's
free-text `task` string. No `docs/issue-<n>/reports/` path is opened
anywhere in `_spawn_one()`'s body. Line numbers shifted from the
architecture survey's citation ("line 4382") to 5037 at current HEAD —
re-derived, verdict unchanged.

**Attempt 2 (source: architecture survey OF-2 — "`consult_cmd()` has zero
board-record read access").** Outcome: **reproduced.**
canonical: spawn.py:4095-4162 (read this session). `consult_cmd()` is at
spawn.py:4095. Its subprocess prompt is built at spawn.py:4133-4142:
```
prompt = (
    "당신은 자문(consult) 으로 불렸다 — 판단만 돌려주면 된다. 이 역할의 "
    "룰북은 이미 로드돼 있다. 브랜치를 만들지도, 커밋하지도, PR 을 열지도 "
    "마라 — 텍스트로 답하고 끝난다. 답을 다 쓴 뒤 마지막에, 다른 어떤 "
    "텍스트도 없이 JSON 객체 하나만 출력하라: "
    '{"answer": "<판단>", "confidence": "low|medium|high", '
    '"caveats": ["<유보/전제>", ...]}\n\n'
    f"질문: {question}"
)
```
One fixed instruction string plus the caller's `question`; the function
body never opens any path under `docs/`. Re-derived from survey's stale
"line 3556" citation to 4095 at current HEAD — verdict unchanged.

**Attempt 3 (source: architecture survey OF-3 — "PR-status comments never
carry board-record content, only a status line and a URL/path").**
Outcome: **reproduced.**
canonical: spawn.py:2947-2980 (read this session). `_post_session_end_comment`
is at spawn.py:2947. Its comment body at spawn.py:2978:
```
body = f"{marker} {line}\n\nworkspace: {work}\nlog: {log}"
r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
```
`{line}` is one of three fixed status strings ("PR ... opened" /
"no PR (pr-check-failed)" / "no PR") set earlier in the function — never
board-record content. Re-derived from survey's stale "line 2458" citation
to 2947 at current HEAD — verdict unchanged.

**Attempt 4 (self-devised — does anything on-the-record ships satisfy
req#5's literal text, "1+ agents judging simultaneously and discussing a
problem together", as opposed to one session reading another's prior
static output?).** Outcome: **reproduced (as a gap).**
canonical: docs/specs/northpole.md:88-93 (read this session), req#5
traceability paragraph:
```
**Traceability:** `gates/remediation_spawn.py` converts an open remediation
finding directly into a spawn task instead of surfacing it to the human.
`on-the-record/hooks/delegated-judgment-gate.sh` auto-approves/auto-rejects a
candidate decision via a named multi-role panel rule
(`panel-unanimous-support-v1`) when depth and impact axes clear, escalating
only when a precondition is missing — keeping routine mid-course judgment
off the human's desk while still recording it.
```
canonical: spawn.py:4147 (read this session):
```
r = subprocess.run(cmd, cwd=cwd or str(ROOT), input=prompt, text=True,
                   capture_output=True, timeout=CONSULT_TIMEOUT, env=env)
```
`consult_cmd()` issues exactly one `subprocess.run` per call: one caller,
one callee, one turn, no loop, no second party the callee can address.

canonical: on-the-record/hooks/delegated-judgment-gate.sh:499-508 (read
this session):
```
def latest_axis_evaluation(role, axis):
    path = role_record_path(role)
    if path is None or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    entries = [en for en in parse_axis_evaluations(text) if en.get("axis") == axis]
    return entries[-1] if entries else None
```
`panel-unanimous-support-v1` (invoked via this function per role) reads
each panel role's prior `axis_evaluation` from that role's already-written
record file and synthesizes from those static entries; it never spawns or
invokes a role session at gate-evaluation time. Neither mechanism northpole.md
cites for req#5 runs two-or-more agent sessions concurrently exchanging
turns on a live problem. canonical: docs/specs/northpole.md:88-93,
spawn.py:4147, on-the-record/hooks/delegated-judgment-gate.sh:499-508 (all
read this session, cited again here) — gap confirmed at current HEAD
74315c9; the traceability paragraph states the panel rule serves req#5
without stating that the panel never convenes live.

**Attempt 5 (self-devised — is the harness's own live inter-session
messaging surface, `SendMessage`/`ListAgents`, used or even considered
anywhere in on-the-record?).** Outcome: **reproduced (as a gap).**
derived: `grep -rn "SendMessage\|ListAgents" spawn.py protocol.md docs/specs/*.md on-the-record/`
```
(no output — 0 matches)
```
canonical: this session's own tool-list `<system-reminder>` (read this
turn) lists `SendMessage`/`ListAgents` as available deferred tools for
cross-session messaging, and a same-session comment on issue #751
(canonical: `gh issue view 751 --comments`, read this session) states as
official-docs fact: "Cross-session messaging IS official:
ListAgents/SendMessage between local sessions sharing a filesystem
(https://code.claude.com/docs/en/cross-session-messaging.md). Messages
are plain text only, never history/files." — confirming the primitive
exists and is documented upstream as usable for exactly this purpose.
canonical: docs/specs/platform-capabilities.md:26-39 (read this session)
documents the adjacent `Monitor` tool (session-bound, install-target
fail-open behavior) in detail but contains no mention of
`SendMessage`/`ListAgents` anywhere in the file. on-the-record has not
adopted, audited, or even mentioned the harness-native concurrent-
messaging primitive that would most directly serve req#5's literal
"simultaneously... discussing" clause.

## Findings

**Finding 1** (addressed_to: architecture). Req#5's literal clause — two
or more agents judging *simultaneously* and *discussing* a problem
together — has no serving mechanism in on-the-record today, and
docs/specs/northpole.md's req#5 traceability paragraph presents
`panel-unanimous-support-v1` as serving req#5 without stating that the
panel never convenes live (it only reads each role's already-written
static record). Evidence pointer: spawn.py:4147 (consult_cmd single
subprocess.run, no loop); on-the-record/hooks/delegated-judgment-gate.sh:499-508
(`latest_axis_evaluation` reads a prior static record entry, no live
spawn). canonical: same citations, Attempt 4 above (read this session).
Severity by band lookup: High → **blocking**.

**Finding 2** (addressed_to: architecture). The harness's own native
concurrent-messaging tools (`SendMessage`/`ListAgents`, per the
cross-session-messaging.md fact posted on issue #751) are unused and
unaudited anywhere in on-the-record — a directly-relevant serving option
for req#5 was never evaluated. Evidence pointer: `derived: grep -rn
"SendMessage\|ListAgents" spawn.py protocol.md docs/specs/*.md
on-the-record/` → 0 matches; docs/specs/platform-capabilities.md:26-39
documents the adjacent Monitor tool but omits SendMessage/ListAgents
entirely. canonical: same citations, Attempt 5 above (read this session).
Severity by band lookup: Medium → **advisory**.

## Eligibility for "cleared"

Not eligible: Finding 1 is an unresolved blocking finding with no human
waiver on record. canonical: `gh issue view 751 --comments` (read this
session) shows no waiver comment. This record therefore does not assert
"cleared."

## What was done

Independently re-attempted architecture's OF-1..OF-3, re-deriving their
line citations against current HEAD 74315c9 (canonical: spawn.py:5037,
4095, 2947, Attempts 1-3 above, read this session) — all three
re-confirmed unchanged. Ran two self-devised attempts targeting req#5's
literal concurrency clause specifically: (1) whether either mechanism
docs/specs/northpole.md cites for req#5 (`consult_cmd`,
`panel-unanimous-support-v1`) actually runs live concurrent agent
sessions — reproduced as a gap; (2) whether on-the-record uses or has
considered the harness's own native `SendMessage`/`ListAgents`
cross-session messaging primitive — reproduced as a gap, 0 grep matches.
Wrote this phase-2 verify-record with two findings addressed to
architecture, each carrying an evidence pointer and a band-lookup
severity.

## Why

canonical: docs/issue-751/reports/architecture/survey.md (read this
session) covered consult/board/spawn-context/PR-comments as OF-1..OF-4
but did not test req#5's literal concurrency clause against the specific
mechanisms northpole.md cites for it, nor examine whether the harness's
own concurrent-messaging primitive was ever considered. Issue #751 asks
to pin gaps between what exists and what concurrent judgment/discussion
between live sessions would need, mapped to the requirement each gap
blocks — this record supplies that for req#5 specifically, per the
operator's stated focus in this session's invocation.

## Upstream basis

- docs/issue-751/reports/defect-verification/survey.md (this role's
  phase-1 survey)
- docs/issue-751/proposals/2026-08-12-defect-verification-concurrent-judgment.md
  (approved phase-2 proposal)
- docs/issue-751/reports/architecture/survey.md (OF-1..OF-4, cited not
  re-litigated)
- docs/specs/northpole.md (req#5 text and traceability paragraph)
- on-the-record/hooks/delegated-judgment-gate.sh (`panel-unanimous-support-v1`)
- spawn.py (`consult_cmd`, `_spawn_one`, `_post_session_end_comment`)
- issue #751 comment (this session, JiwonJung94): official-docs
  cross-session-messaging facts
- issue #748 (northpole requirements), issue #699 (consult design)

## Open findings

Finding 1 (blocking, addressed_to: architecture) and Finding 2 (advisory,
addressed_to: architecture), both above, are open — neither has a
follow-up issue filed yet.

## Next steps

Architecture role opens a dedicated follow-up issue against
docs/specs/northpole.md's req#5 traceability text and the mechanisms
named in Finding 1's evidence pointer (spawn.py `consult_cmd`,
delegated-judgment-gate.sh `panel-unanimous-support-v1`), then a second
follow-up evaluating `SendMessage`/`ListAgents` as a req#5 serving option
per Finding 2.

## Resolution path

Finding 1 resolves when either (a) docs/specs/northpole.md's req#5
traceability paragraph is corrected to state the panel-rule limitation
explicitly, or (b) a live-concurrent mechanism is built and cited in its
place — ranked first because it blocks landing. Finding 2 resolves when
architecture's follow-up issue records a decision (adopt
SendMessage/ListAgents for req#5, or explicitly reject with a stated
reason) — ranked second, advisory only.

## What did not work

None.
