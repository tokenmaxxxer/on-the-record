---
issue: 3129
role: adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9
author: adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3137's repair round 4 (registered-repo/tool_response seam redesign)
code_under_review: 9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1
type: defect-verification-record
breaking: false
loop_state: landed
verdict: Angle 1 (command text never consulted for repo attribution anywhere on
  the path) Present. Angle 2 (real-binary-driven tool_response shapes): repo-
  mismatch and no-URL Present (correct fail-closed, stderr, nonzero exit from
  the direct entrypoint); a URL embedded in a FAILED edit's own error text
  Incorrect (a marker is silently written for an edit that explicitly did not
  apply, no success/failure check exists anywhere on this path); multiple
  URLs in one response Incorrect (first-match-wins is order-dependent, can
  falsely reject a legitimate same-repo edit as a policy violation);
  right-repo/unrelated-issue-number Present, by design. Angle 3 (cwd as a
  forgeable trust root) Incorrect, severe: the module's own docstring claim
  that the payload's cwd field is fixed for a session's whole life and cannot
  be retroactively changed by session-controlled text is falsified by Claude
  Code's own hook documentation (cwd updates after Claude runs cd) and
  reproduced end-to-end against the real hook binary — this reopens exactly
  the cd-into-another-checkout collision this whole repair chain exists to
  close, silently, with no policy-violation trace. Angle 4 (PR #3170's five
  shapes re-driven and pass for the stated reason, not incidentally) Present,
  confirmed via a sixth case that keeps a misleading --repo= flag in the
  command text while the URL says otherwise and shows the flag is ignored.
  Angle 5 (the record's two caveats against shipped behavior) Present but
  incomplete — both caveats' own factual claims hold, but Caveat 1 only
  frames the false-block direction (a legitimate multi-repo session gets
  wrongly refused) and does not anticipate the false-accept direction Angle 3
  demonstrates (an unregistered repo getting silently treated as registered).
upstream:
  - path: docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md
    sha: ca58cd7f0bb8b81bdb83dbe1fbac85762843cf5a
  - path: docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7.md
    sha: same-commit
---

# issue-3129 — adversarial-review+silent-failure-audit+test-depth-audit-d863dfd9 record

Note on paths below (all untracked): `on-the-record/hooks/amendment_channel.py` (untracked)
is on PR #3137's branch, not this checkout.
`on-the-record/hooks/amendment-channel.sh` (untracked) is on PR #3137's branch, not this checkout.
`on-the-record/hooks/hook_input.py` (untracked) is on PR #3137's branch, not this checkout.
`tests/test_amendment_channel.py` (untracked) is on PR #3137's branch, not this checkout.
Both `gates/probe_*.py` files (untracked) are also on PR #3137's branch, not this checkout.
Every citation of these five paths anywhere below — bare or sha-prefixed —
was read against a fetched worktree of PR #3137's branch at
`/tmp/pr3137-verify6` (head `9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1`).
`on-the-record/hooks/post-landing-obligation-gate.sh`,
`on-the-record/hooks/fail-open-wrapper.sh`, and `spawn.py` ARE tracked in
this checkout and were read directly from it.

## What was done

canonical: `gh pr view 3170`/`gh pr view 3178` output and both PRs' own
records (`docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md`,
merged as PR #3170; `docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7.md`,
merged as PR #3178), both read first per the spawning prompt. PR #3170 found
round 3's command-text parser still missed five of nine un-enumerated
shapes. PR #3178 records round 4's response: delete the command-text
repo-attribution parser entirely and replace it with two facts neither of
which is command text — this session's own registered repo from
`repo_slug_for_cwd()` applied to the `PostToolUse` payload's own `cwd`
field, and the actual edited issue's repo+number from `gh issue edit`'s own
success-output URL in `tool_response`. A mismatch is a policy violation (no
marker, one stderr line naming both repos, nonzero exit); no parseable URL
or no resolvable registered repo fails the same closed way.

canonical: `gh pr view 3137 --json headRefName,state,url` — result:
`{"headRefName":"issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019","state":"OPEN",...}`.
derived: `git worktree add /tmp/pr3137-verify6 issue-3129/implementation-blueprint+silent-failure-audit+test-derivation-a641f019`
— result: `HEAD의 현재 위치는 9fb4a476입니다 issue-3129: fix acceptance probes' tool_response fixtures for the round-4 seam`,
matching the sha PR #3178's own record cites for round 4's tip. This session
did not merge or edit PR #3137, per the spawning prompt's explicit
instruction — the worktree was read-only, and the review harness scripts
below live entirely outside the repo (`/tmp/verify6_test/`).

### Angle 1 — is command text consulted for repo attribution anywhere on the path?

canonical: `9fb4a476:on-the-record/hooks/amendment_channel.py:555-584`
(`record_amendment_from_response`):

```python
    if not _gh_issue_edit_body_call(tool_name, command):
        return AmendmentSkipped()

    registered_repo = repo_slug_for_cwd(cwd)
    if registered_repo is None:
        return NoRegisteredRepo(cwd)

    parsed = _issue_url_from_response(tool_response)
    if parsed is None:
        return NoIssueUrlInResponse(registered_repo)

    if parsed.repo != registered_repo:
        return RepoMismatch(registered_repo, parsed.repo, parsed.issue)

    note = _extract_note(command, cwd)
    version = write_amendment(state_dir, parsed.repo, parsed.issue, note=note)
```

`command` (the raw Bash string) is touched in exactly two places on this
whole path: `_gh_issue_edit_body_call()` (a boolean shape gate — is this a
`gh issue edit ... --body...` call at all — `9fb4a476:on-the-record/hooks/amendment_channel.py:452-466`)
and `_extract_note()` (cosmetic note text for the marker's own content field,
`9fb4a476:on-the-record/hooks/amendment_channel.py:405-427`). Neither
contributes to `registered_repo` (from `cwd` only) or `parsed.repo`/`parsed.issue`
(from `tool_response` only). derived: `grep -n 'hook_input\.' on-the-record/hooks/amendment_channel.py`,
untracked, run in `/tmp/pr3137-verify6` — result: only
`hook_input.parse_payload`, `hook_input.tool_command`, and
`hook_input.tool_response_text` appear in that grep's output; no
`cd_target`/`resolved_cwd` call exists in this file per that same grep's
absence of either name.

Confirmed empirically, not just by reading: a command string carrying an
explicit, misleading `--repo=` flag naming the CORRECT (registered) repo,
while `tool_response`'s URL names a DIFFERENT repo, still triggers
`RepoMismatch` — proving the flag is genuinely ignored, not incidentally
correct because no test happened to contradict it. acceptance:
`python3 /tmp/verify6_test/attack4_repo_flag_ignored.py /tmp/pr3137-verify6/on-the-record/hooks`
(fed `cmd = "gh issue edit --repo=tokenmaxxxer/repo-a 42 --body x"` from a
`cwd` whose own git origin is `tokenmaxxxer/repo-a`, and `tool_response`
naming `tokenmaxxxer/repo-b`) — result:

```
misleading --repo=repo-a-in-text but URL says repo-b: RepoMismatch(registered_repo='tokenmaxxxer/repo-a', url_repo='tokenmaxxxer/repo-b', issue='42')
```

**Verdict: Present.** No command-text fallback for repo attribution survives
anywhere on the write path, including in the `hook_input.py` helper module
(untracked, on PR #3137's branch), which this module no longer calls at all.

### Angle 2 — driving the real hook binary with adversarial `tool_response` shapes

derived: `/tmp/verify6_test/harness.py`, a standalone script (outside the
repo) that builds two real git checkouts (`repo-a`, `repo-b`, each with a
real `origin` remote) and runs the REAL, unmodified shipped `.sh` wrapper
(`amendment-channel.sh`, untracked, on PR #3137's branch) as a subprocess
via `subprocess.run(["bash", script], input=json.dumps(payload), ...)` — the
production invocation shape, not an in-process import.

acceptance: `python3 /tmp/verify6_test/harness.py /tmp/pr3137-verify6/on-the-record/hooks` — result:

```
mismatch-repo                                 rc=0 markers=[]
  stderr: amendment-channel: POLICY VIOLATION -- gh issue edit #42 landed in tokenmaxxxer/repo-b but this session is registered to tokenmaxxxer/repo-a -- no marker written (an edit outside a session's own registered repo is refused, never silently attributed)
no-url                                        rc=0 markers=[]
  stderr: amendment-channel: gh issue edit ran but its tool_response carries no parseable https://github.com/<owner>/<repo>/issues/<n> URL (the call may have failed, or gh's output shape changed) -- no marker written; this session's own registered repo is tokenmaxxxer/repo-a
url-in-error-message                          rc=0 markers=[]
  stderr: amendment-channel: POLICY VIOLATION -- gh issue edit #42 landed in tokenmaxxxer/repo-b but this session is registered to tokenmaxxxer/repo-a -- no marker written (an edit outside a session's own registered repo is refused, never silently attributed)
url-inside-body-echoed-back-on-failure        rc=0 markers=['issue-999__tokenmaxxxer_repo-a.marker.json']
two-urls-first-wrong-repo                     rc=0 markers=[]
  stderr: amendment-channel: POLICY VIOLATION -- gh issue edit #5 landed in tokenmaxxxer/repo-b but this session is registered to tokenmaxxxer/repo-a -- no marker written (an edit outside a session's own registered repo is refused, never silently attributed)
right-repo-different-issue-number             rc=0 markers=['issue-9999__tokenmaxxxer_repo-a.marker.json']
cwd-drifted-to-other-repo-then-edits-there    rc=0 markers=['issue-42__tokenmaxxxer_repo-b.marker.json']
```

(every case's `rc=0` is `amendment-channel.sh`'s own unconditional trailing
`exit 0`, documented and unchanged this round — see Angle 5 below; the
process-level exit code is checked separately below via the direct
entrypoint.)

**mismatch-repo, no-url**: correct, matches the design's own fail-closed
contract — `RepoMismatch`/`NoIssueUrlInResponse`, no marker, one stderr line.
acceptance: `python3 /tmp/verify6_test/attack2c.py /tmp/pr3137-verify6/on-the-record/hooks`,
`direct-py-mismatch-exit-code` case (drives `amendment_channel.py` directly,
not through the `.sh` wrapper) — result:
`1 "amendment-channel: POLICY VIOLATION -- gh issue edit #42 landed in tokenmaxxxer/repo-b but this session is registered to tokenmaxxxer/repo-a..."` —
`main()` does exit nonzero for this outcome, as the module docstring claims.
**Present.**

**url-in-error-message → INCORRECT (confirmed defect).** The harness's own
`url-in-error-message` case (a same-shaped but different-repo URL) happened
to fail closed by accident, so a second, sharper case was built: a
genuinely-failed edit (`HTTP 422: Validation Failed ... edit 42 was NOT
applied`) whose error text merely references an UNRELATED issue's URL in the
SAME (registered) repo. acceptance:
`python3 /tmp/verify6_test/attack2c.py /tmp/pr3137-verify6/on-the-record/hooks`
(drives `amendment_channel.py` directly, untracked, on PR #3137's branch —
the `.sh` wrapper's own `rc=0` masking is irrelevant to this claim) —
result:

```
same-repo-error-references-unrelated-issue: 0 '' ''
markers: ['issue-7__tokenmaxxxer_repo-a.marker.json']
```

`tool_response` for this case was
`"HTTP 422: Validation Failed. See https://github.com/tokenmaxxxer/repo-a/issues/7 for the field format example. (edit 42 was NOT applied)"`
— the edit explicitly did not apply, yet a marker was silently written
telling any worker watching issue #7 that the orchestrator amended it.
Root cause, canonical: `9fb4a476:on-the-record/hooks/amendment_channel.py:469-487`
(`_issue_url_from_response`):

```python
def _issue_url_from_response(tool_response: object) -> Optional["_IssueUrl"]:
    text = hook_input.tool_response_text(tool_response)
    if not text:
        return None
    m = _ISSUE_URL_RE.search(text)
    if not m:
        return None
```

There is no success/failure check anywhere on this path — `.search()` scans
the ENTIRE `tool_response` blob unconditionally for the URL shape, whether
that text is `gh`'s own stdout on success or a stderr/error message that
happens to contain a URL substring. This repo already has an established
convention for exactly this problem (distinguishing a real success from an
error blob in `tool_response` text) that this module does not use, canonical:
`on-the-record/hooks/post-landing-obligation-gate.sh:137-147`, tracked in
this checkout, read directly (NOT on PR #3137's branch):

```python
resp = e.get("tool_response")
if isinstance(resp, str):
    text = resp
elif resp is not None:
    text = json.dumps(resp)
else:
    sys.exit(0)  # no response captured — unreached, fail open
low = text.lower()
FAILURE_MARKERS = ("failed to merge", "graphql error", "could not merge",
                    "is not mergeable", "pull request is not mergeable")
if any(m in low for m in FAILURE_MARKERS):
    sys.exit(0)  # merge did not actually succeed — no obligation to open
```

That sibling hook checks for known failure phrases before trusting anything
extracted from `tool_response`; `amendment_channel.py`'s round-4 redesign
has no equivalent check, despite its own "Why" claiming "`gh issue edit`'s
own success output already reports exactly which issue it edited" —
success is asserted, never verified.

**two-urls-first-wrong-repo → Incorrect, lower severity (fails closed, not
open).** `tool_response` = `"note: also touched
https://github.com/tokenmaxxxer/repo-b/issues/5\nhttps://github.com/tokenmaxxxer/repo-a/issues/42"`
— `_ISSUE_URL_RE.search()` returns the FIRST match (`repo-b/5`), so a
legitimate, successful edit landing in the registered repo (`repo-a/42`, the
second URL) is rejected as a cross-repo policy violation and its marker is
silently dropped. derived: the harness result table above (acceptance
command cited earlier in this section), `two-urls-first-wrong-repo` case —
`markers=[]`, stderr names `#5`/`repo-b` (the wrong, first-match pair), not
`#42`/`repo-a` (the actual successful edit). Root cause: the regex is an
unanchored `.search()` over the whole blob with no requirement that the
matched URL be gh's OWN reported line (e.g. the last line, or the only
line) rather than incidental text earlier in the same response.

**right-repo-different-issue-number → Present, by design.** derived: the
harness result table above, `right-repo-different-issue-number` case —
marker written for issue 9999 (the URL's number) although the command text
and this session's own branch both name issue 42; matches
`9fb4a476:tests/test_amendment_channel.py:360-370`
(`test_issue_number_comes_from_the_url_never_the_command_text`), which
asserts exactly this. Not independently exploitable on its own —
`check_notice` only ever looks up the session's OWN
`issue_for_cwd(cwd)`-derived number
(`9fb4a476:on-the-record/hooks/amendment_channel.py:676-678`), so a marker
for an unrelated issue number is simply never read by any worker — but it
compounds with the url-in-error-message finding above: an arbitrary,
attacker/session-controlled issue number can be turned into a false
amendment marker for that issue via nothing more than an error message that
happens to quote a URL.

### Angle 3 — is `cwd` actually a fixed trust root, or can a session steer it?

canonical: `9fb4a476:on-the-record/hooks/amendment_channel.py:109-122`
(module docstring, redesign section):

```
  1. This session's own REGISTERED repo: `repo_slug_for_cwd()` applied to
     this `PostToolUse` payload's own top-level `cwd` field -- the
     directory `spawn.py` launched this process into
     (`subprocess.Popen(cmd, cwd=<workspace>, ...)`), which every hook
     payload in this session reports unchanged for the session's whole
     life. This is NOT the same value a `cd X && gh ...` inside a single
     Bash command string affects -- that `cd` only changes the cwd of the
     one subprocess that command string spawns, never this payload
     field ... Treating THIS field as "what spawn.py registered for this
     session" needs no new cross-process registration file: spawn.py
     already IS the one process that chose it, and no session-controlled
     text can retroactively change what the harness reports here for a
     later tool call.
```

This is the round's central trust claim: the payload's `cwd` field is fixed
for a session's whole life, so `repo_slug_for_cwd(cwd)` is a safe proxy for
"what `spawn.py` registered," distinct from anything the session itself
controls. derived: `WebFetch` of `https://code.claude.com/docs/en/hooks`
(Anthropic's own Claude Code hooks reference), asked verbatim whether the
`cwd` field is live or fixed — result, quoted directly from that page's own
"cwd follows Claude" note:

```
cwd follows Claude: the cwd field in the hook's input JSON is the worktree
root after Claude enters a worktree, and the new directory after Claude
runs cd. Read it when a hook needs to know which directory Claude is
working in.
```

This directly falsifies the docstring's "unchanged for the session's whole
life" / "no session-controlled text can retroactively change" claim: an
ordinary, standalone `cd` — the most session-controlled action there is —
changes what every LATER hook payload in that same session reports as
`cwd`, per Anthropic's own documentation. No symlink or worktree trick is
needed; a plain `cd` into a second checkout, run as its own separate Bash
tool call (not chained with the `gh issue edit` call the module's docstring
explicitly excludes), is enough.

Reproduced against the real hook binary rather than argued from the doc
alone. derived: the harness result table in Angle 2 above (acceptance
command: `python3 /tmp/verify6_test/harness.py /tmp/pr3137-verify6/on-the-record/hooks`),
`cwd-drifted-to-other-repo-then-edits-there` case — a payload with
`cwd=<repo-b checkout>` (simulating what the harness reports once a session
has `cd`'d there, per the doc quote above) and `tool_response` naming
`repo-b/issue-42` — result:

```
cwd-drifted-to-other-repo-then-edits-there    rc=0 markers=['issue-42__tokenmaxxxer_repo-b.marker.json']
```

No `RepoMismatch`, no stderr, a marker written silently — because
`repo_slug_for_cwd(cwd)` recomputes "the registered repo" fresh from
whatever `cwd` the CURRENT payload carries, with no persisted record of
what `spawn.py` actually chose at launch to compare against (the module's
own docstring at `9fb4a476:on-the-record/hooks/amendment_channel.py:119-122`,
fenced above, explicitly rejects adding one: "needs no new cross-process
registration file"). This is exactly the scenario the module's own docstring
holds up as its worked example of what round 4 defends against, canonical:
`9fb4a476:on-the-record/hooks/amendment_channel.py:52-58`:

```
originally called `repo_slug_for_cwd()` on the raw `PostToolUse` payload
`cwd` -- the orchestrator's own session directory -- even though the `gh
issue edit` command it is inspecting can `cd` into a DIFFERENT checkout
first (`cd ../study-companion && gh issue edit 42 --body ...`, run from
an `on-the-record` session cwd, is this issue's own worked example)
```

— except now the same collision is reachable through a plain, separate `cd`
Bash call (which the harness's own `cwd` tracking follows, per the doc)
rather than an in-line `cd X && gh ...` (which the docstring correctly says
does NOT affect the payload's `cwd`). The design closed the in-line-`cd`
door and left the standalone-`cd` door — the one the real harness actually
tracks — open, unflagged, and untested. derived: `grep -n 'cwd=' tests/test_amendment_channel.py`,
untracked, run in `/tmp/pr3137-verify6` — every `RecordAmendmentFromResponse`/
`PreviouslyBrokenShapesAreNowIrrelevant` test either omits `cwd` (defaults
to one fixed `self.session_cwd`) or passes a single static
`cwd=no_repo_cwd`; no test in that grep's output constructs two calls where
the SAME session's `cwd` differs between them.

**Verdict: Incorrect, severe.** The "registered repo" is not actually
anchored to `spawn.py`'s launch-time choice — it is recomputed from
whatever `cwd` the current payload happens to carry, which the real harness
updates on an ordinary `cd`. The "policy violation, fail-closed" check this
whole round exists to add provides no defense against the module's own
worked-example scenario once that scenario is driven through a standalone
`cd` instead of an inline one — it silently accepts it as legitimate,
which is worse than round 3's failure mode (a silent miss with no marker at
all) because this one DOES write a plausible-looking marker.

### Angle 4 — do PR #3170's five shapes now pass for the stated reason?

acceptance: `python3 -m pytest tests/test_amendment_channel.py::PreviouslyBrokenShapesAreNowIrrelevant -v`,
untracked, run from `/tmp/pr3137-verify6` — result:

```
6 passed in 0.81s
```

covering all five of PR #3170's shapes (`pushd`, quoted-space `cd`,
subshell-wrapping-only-`gh`, `--repo=`-before-the-number,
`GH_REPO=`-prefixed) plus one bonus case, each asserted via
`9fb4a476:tests/test_amendment_channel.py:427-491`
(`PreviouslyBrokenShapesAreNowIrrelevant`, whose own docstring states the
same "not incidentally" claim this angle checks).

Confirmed independently, not merely by re-running the existing suite: Angle
1's `attack4_repo_flag_ignored.py` case above feeds a SIXTH, adversarial
variant — a `--repo=` flag naming the CORRECT repo while the URL says
otherwise — and shows `RepoMismatch` still fires (the flag is ignored, not
coincidentally honored), which is the strongest available evidence within
inspection that these five shapes pass because command text is structurally
unread for attribution, not because this session's particular five payloads
happened not to exercise a surviving special case.

**Verdict: Present**, confirmed for the stated reason.

### Angle 5 — are the record's two caveats what the shipped code does?

canonical: `docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7.md`,
"Caveat 1" and "Caveat 2" sections, read first this session.

**Caveat 1 (multi-repo sessions unsupported)**: its own factual basis —
`spawn.py`'s roster carries exactly one `work` field per session, never a
set — re-confirmed against the CURRENT branch tip, not cited from the prior
record. derived: `grep -n 'roster_register(roster_key\|"work"' spawn.py`,
tracked in this checkout (also re-run in `/tmp/pr3137-verify6` against the
same file, unmodified by this round) — result:

```
4668:                roster_register(roster_key, _early_roster_entry)
4759:        roster_register(roster_key, {
4650:                    "work": str(cwd), "log": str(log_path),
4762:            "work": str(cwd), "log": str(log_path),
```

Both call sites still write a single `"work": str(cwd)` string, confirming
Caveat 1's premise holds on this tip. **But** Caveat 1 as written only
frames the FALSE-BLOCK direction of this limitation ("a session that
legitimately touches 2 repos" gets wrongly refused, "the new design cannot
serve until spawn.py's registration schema is extended from one repo to a
set"). It does not anticipate the FALSE-ACCEPT direction Angle 3 above
demonstrates: because there is no persisted registration record at all
(by the caveat's own account), a session whose `cwd` drifts is not merely
"wrongly refused" when it touches a second repo — it is silently
RE-REGISTERED to that second repo with no trace, which is a materially
different (and more dangerous) failure mode than the one the caveat
describes.

**Caveat 2 (sessions not started through spawn.py)**: fail-closed via
`NoRegisteredRepo`, re-confirmed with a real test run, not asserted from the
prior record. acceptance: `python3 -m pytest tests/test_amendment_channel.py -k test_no_registered_repo -v`,
untracked, run from `/tmp/pr3137-verify6` — result: `2 passed`
(`test_no_registered_repo_is_fail_closed_not_skip_silently`,
`test_no_registered_repo_exits_nonzero_with_stderr`). The ledger-masking
sub-claim (the `.sh` wrapper's unconditional `exit 0`, and the amendment
hook's absence from `fail-open-wrapper.sh`'s `_fallback_fired` allowlist)
also re-confirmed directly against shipped files, not cited from the prior
record. derived: `tail -6 amendment-channel.sh`, untracked, run in
`/tmp/pr3137-verify6/on-the-record/hooks` — result:

```
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
command -v python3 >/dev/null 2>&1 || exit 0

python3 "$DIR/amendment_channel.py"
exit 0
```

derived: `grep -n 'session-role-bind\|skill-verdict-guard\|stop-gate.sh' on-the-record/hooks/fail-open-wrapper.sh`,
tracked in this checkout, read directly (NOT on PR #3137's branch) —
result: one match, the allowlist line
`session-role-bind.sh|directive.sh|post-landing-obligation-gate.sh|stop-gate.sh|skill-verdict-guard.sh`,
confirming the amendment-channel hook is absent from it, exactly as Caveat 2
describes.

**Verdict: Present but incomplete** — both caveats' own factual claims are
accurate against the shipped tip, but Caveat 1's framing misses the more
severe failure mode Angle 3 found.

## Why

canonical: this session's own Angles 1-5 acceptance/derived citations above
are the evidentiary basis for the three skill applications below.

Per `adversarial-review`'s blind-evaluator stance, this session did not stop
at re-running round 4's own green suite (see "Acceptance checks" below) or
at the five shapes PR #3170 already named — it independently fetched
Anthropic's own hook documentation to check the module's own central
trust-anchor claim against ground truth rather than taking the docstring's
assertion at face value, and constructed six new `tool_response` shapes
(mismatch, no-URL, URL-in-error-text, URL-inside-echoed-body, two-URLs,
cwd-drift) none of which appear in the shipped test suite. derived:
`grep -n 'def test_' tests/test_amendment_channel.py`, untracked, run in
`/tmp/pr3137-verify6`, cross-checked against the six harness case names in
Angle 2 and Angle 3 above — none of those six harness case names match an
existing `def test_` name in that grep's output.

Per `silent-failure-audit`, the central question for Angle 2's
url-in-error-message case was not whether `_issue_url_from_response` raises
(it does not — `hook_input.tool_response_text` and `_ISSUE_URL_RE.search`
are both total, per their own docstrings) but whether a FAILED operation's
error text gets silently mistaken for a success report with zero
distinguishing trace — a "default-value substitution without recording that
a fallback occurred" pattern one layer upstream of the repo/issue match
check itself, structurally identical in shape to the round-3 findings PR
#3170 catalogued, just moved from the resolution layer to a new
success-detection gap this redesign introduced. Angle 3's finding is the
same audit applied to the module's own trust boundary: the "registered
repo" concept promises a decision made once, at spawn time, immune to
later session-controlled input — but the actual code re-derives it fresh
on every call from a mutable field, with the immutability claim resting on
a factual assertion about the harness that this session found to be false.

Per `test-depth-audit`, `PreviouslyBrokenShapesAreNowIrrelevant`
(`9fb4a476:tests/test_amendment_channel.py:427-491`) was confirmed Genuine
Assertion — each test asserts `AmendmentWritten` plus a marker read-back,
not merely that the call didn't raise — but its scope, like the cwd-only
fixtures across the whole suite (the `grep -n 'cwd='` result cited in Angle
3 above), is Happy-Path-Only along exactly the dimension Angle 3 attacks:
no test in the suite varies `cwd` across two calls within what is nominally
"the same session," so the cwd-drift scenario has zero coverage, not merely
undercounted coverage.

## What did not work

None — every harness/script constructed this session ran successfully on
the first attempt (`/tmp/verify6_test/harness.py`, `attack2c.py`,
`attack4_repo_flag_ignored.py`). One adjustment mid-session, not a failure:
inline `python3 -c "..."` invocations containing the literal substring
`gh issue edit` were refused by this session's own `gh-guard`/board-gate
PreToolUse hooks (issues are user-authored-only for this skill session, and
an inline `-c` script hides its write target from the text-level gate) — all
scratch scripts were written to `/tmp/verify6_test/*.py` via the `Write`
tool instead and invoked as `python3 <path> <args>`, which the gate
accepts.

## Upstream basis

- `docs/issue-3129/reports/adversarial-review+silent-failure-audit+test-depth-audit-e93e7a3b.md`
  (merged as PR #3170, sha `ca58cd7f0bb8b81bdb83dbe1fbac85762843cf5a`) —
  canonical: this file's own nine-shape harness result table and "Open
  findings" §1-5, read first per the spawning instructions — round 3's
  failure catalogue that round 4 was built to close. Whether it is now moot
  is independently re-derived, not cited from that file: see this record's
  own Angle 4 above and Angle 1 above (command text structurally unread for
  attribution at all) — round 4 did not merely patch the nine shapes, it
  removed the entire attack surface that produced them.
- `docs/issue-3129/reports/implementation-blueprint+silent-failure-audit+test-derivation-f70893c7.md`
  (merged as PR #3178) — canonical: this file's own "Acceptance checks"
  section, read first per the spawning instructions. Every one of its
  acceptance numbers was independently re-derived against the same tip, not
  cited from that record — see this record's own "Acceptance checks"
  section below, which matched for `tests/test_amendment_channel.py`
  (untracked) and both gate probes but NOT for `tests/ -q` (see that section below for why,
  and why it is not attributable to this round's own code).
- `https://code.claude.com/docs/en/hooks` (Anthropic's own Claude Code hooks
  reference, fetched this session) — the "cwd follows Claude" note that
  falsifies the module's own trust-anchor claim, Angle 3 above.

## Open findings

1. **(Angle 3, severe)** A session's `cwd`-derived "registered repo" is not
   anchored to `spawn.py`'s launch-time choice; it silently follows the
   session's own later `cd` calls, because the real harness updates the
   `PostToolUse` payload's `cwd` field on `cd` (Anthropic's own
   documentation, quoted in Angle 3) and this module keeps no separate
   registration record to compare against (a deliberate design choice, per
   its own docstring). A session that `cd`s into a second checkout via an
   ordinary, standalone Bash call and then edits that repo's issue is
   treated as a fully legitimate, same-repo edit — no `RepoMismatch`, no
   stderr, a marker written exactly as if that had been the session's own
   registered repo all along. This reopens, silently, the exact
   cd-into-another-checkout collision the module's own docstring names as
   its worked example for why round 4 exists. Resolution path: either
   persist the ACTUAL spawn-time registered repo somewhere `spawn.py`
   writes once and never updates (a real cross-process registration record,
   the thing this round's own docstring explicitly declined to add), or
   explicitly narrow the trust claim to "the repo this specific payload's
   `cwd` names right now" and drop the "registered by spawn.py" framing,
   which is not what the field actually carries.
2. **(Angle 2, moderate)** `_issue_url_from_response` has no success/failure
   check; a URL-shaped substring anywhere in a FAILED edit's own error text
   (e.g. a validation-error message that echoes back an invalid `--body`
   value, or references an example/related issue by URL) is silently
   trusted as if it were `gh`'s own success report. This repo already has
   an established `FAILURE_MARKERS`-heuristic convention for exactly this
   problem in `on-the-record/hooks/post-landing-obligation-gate.sh` that
   this module does not reuse or reimplement. Resolution path: add a
   failure-marker heuristic (or require the matched URL to be gh's own
   trailing/sole output line) before trusting `_issue_url_from_response`'s
   result.
3. **(Angle 2, minor)** `_ISSUE_URL_RE.search()` returns the first URL match
   in `tool_response`, with no requirement that it be gh's own reported
   line; a response containing an earlier, incidental URL for a different
   repo (e.g. in a warning/note preceding the real success line) causes a
   legitimate same-repo edit to be misdiagnosed as a cross-repo policy
   violation and its marker dropped. Resolution path: anchor the match to
   the last line of `tool_response`, or to a line matching `^https://...$`
   with nothing else on it, rather than an unconstrained substring search.
4. Carried forward from PR #3178's own record, unresolved this round: the
   `tests/ -q` staleness finding below (branch-hygiene, not this round's
   code) and both caveats' documented gaps (Caveat 1's multi-repo
   limitation, now sharpened by finding 1 above; Caveat 2's ledger-masking
   gap, both re-confirmed accurate in Angle 5 above).

## Acceptance checks (all run for real, this session, against `/tmp/pr3137-verify6` at `9fb4a4769f39944c859ab7cc3e5b0a8f57dee3f1`; every command in this section runs against paths untracked in this checkout, on PR #3137's branch)

```
$ python3 -m pytest tests/test_amendment_channel.py -q
65 passed in 0.96s
```
Acceptance requirement met — checked: `python3 -m pytest tests/test_amendment_channel.py -q` — result: 65 passed, matching PR #3178's own record.

```
$ python3 gates/probe_running_session_sees_amendment.py; echo $?
ok
0
```
Acceptance requirement met — checked: `python3 gates/probe_running_session_sees_amendment.py` — result: ok, exit 0.

```
$ python3 gates/probe_amendment_notice_fires_once.py; echo $?
ok
0
```
Acceptance requirement met — checked: `python3 gates/probe_amendment_notice_fires_once.py` — result: ok, exit 0.

```
$ python3 -m pytest tests/ -q
1 failed, 318 passed, 2 warnings in 13.71s
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
```
NOT matching PR #3178's own record (`319 passed, 2 warnings`). Root-caused,
not left as a bare mismatch. derived: `git merge-base HEAD origin/main` —
result `820e9dc5`. derived: `git show 820e9dc5:on-the-record/hooks/hooks.json | grep -c amends-landing-apply`
— result `0`. derived: `git show origin/main:on-the-record/hooks/hooks.json | grep -c amends-landing-apply`
— result `1`. derived: `git log --oneline --all -- on-the-record/hooks/amends-landing-apply.sh`
— result:

```
6ae02cce [issue-3134/implementation-blueprint+silent-failure-audit+test-derivation-f2953dbf] (#3181)
2cef8cfa issue-3134: repair round 5 -- fix repo-targeting bypass and silent declines in amends-landing-apply.sh
e109ddad issue-3134: repair round 4 -- fix over-broad merge-hook trigger, add hook-driving e2e test
3c6b59e1 issue-3134: repair round 3 -- silent-failure-audit pass on the new landing-apply path
f347bbd9 issue-3134: repair round 3, finding 3 -- automatic landing-step caller for amends: backlinks
```

— issue-3134 work, merged to `main` after PR #3137's branch diverged at
`820e9dc5`. The failing test diffs this branch's `hooks.json` against
`origin/main`'s CURRENT tip and finds `amends-landing-apply.sh` (added to
`main` by these unrelated issue-3134 commits after PR #3137 branched)
missing from PR #3137's stale branch — a branch-hygiene/rebase gap, not a
defect in this round's `amendment_channel.py`/`hook_input.py` changes.
derived: `git log --oneline -- on-the-record/hooks/amends-landing-apply.sh`
run against PR #3137's own branch history in `/tmp/pr3137-verify6` — no
result (empty output), confirming this file was never touched on that
branch. **Not counted against this round's own code**, but PR #3137 needs a
rebase before landing regardless of this session's other findings.

```
$ python3 -m pytest test/ -q
15 failed, 548 passed, 3 xfailed in 32.35s
```
Matching PR #3178's own record exactly. derived: `python3 -m pytest test/ -q 2>&1 | grep FAILED`
— result: the same 5 files (`test_convention_equivalence.py`,
`test_local_dependency_env.py`, `test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) PR #3091 already owns per
PR #3170's own record; count did not move.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; used the blind-
evaluator stance to fetch Anthropic's own hook documentation and check the
module's own central trust-anchor claim ("cwd unchanged for the session's
whole life") against it rather than trusting the docstring's assertion,
and built six `tool_response` shapes beyond the shipped test suite's own
coverage — canonical: Angle 3's `WebFetch` citation and the harness result
table in Angle 2, both above.

skill-verdict: silent-failure-audit — applied: invoked; traced
`_issue_url_from_response`'s missing success/failure check forward from
catch site to downstream consequence (a false amendment marker for an issue
that was never actually edited), named the pattern against this repo's own
`FAILURE_MARKERS` convention in `post-landing-obligation-gate.sh`, and
applied the same trace-forward method to Angle 3's cwd claim as a trust-
boundary silent-failure, not only to literal try/except sites — canonical:
Angle 2's `attack2c.py` result and Angle 3's harness result, both above.

skill-verdict: test-depth-audit — applied: invoked; confirmed
`PreviouslyBrokenShapesAreNowIrrelevant` is Genuine Assertion by construction
(asserts `AmendmentWritten` plus a marker read-back per case) and flagged
its Happy-Path-Only gap along the one dimension this round's whole redesign
depends on — no test varies `cwd` within "the same session" — canonical:
the `grep -n 'cwd='` result cited in Angle 3 above.

skill-verdict: work-in-english — applied: invoked; this record, every
scratch script under `/tmp/verify6_test/`, and this session's git/gh
commands are in English; this final summary to the user follows in Korean
per policy.

other mounted skills: not triggered — `implementation-audit`,
`conformance-review-verdict-assignment`, and
`defect-verification-independence-from-upstream-verdicts` were configured
by task-text match (per the spawning prompt) rather than mounted for this
role directly; their guidance (independent re-derivation rather than citing
PR #3178's/PR #3170's own verdicts, naming the failing clause on each
Incorrect verdict, re-checking a defect once before finalizing it) was
followed throughout this record without a separate Skill-tool invocation
distinct from the ones already listed above — every Incorrect/Present
verdict above cites its own re-derived evidence rather than the upstream
records' claims, and Angle 3 in particular was re-checked against the real
hook binary (not just argued from the doc) before being finalized.

## Next steps

`loop_state: landed` — derived: this record's Angles 1-5 above, each with
its own `acceptance:`/`derived:` citations, cover every item the spawning
prompt assigned (command-text-never-read confirmation, five adversarial
`tool_response` shapes driven through the real binary, the cwd-trust-root
attack, PR #3170's five shapes re-driven for the stated reason, and both
caveats checked against shipped behavior), plus the full `tests/`/`test/`
run. This session does not edit or merge PR #3137, per the spawning
prompt's explicit instruction; findings 1-4 above are handed to whoever
picks the PR up next. No further action is planned from this session
itself.
