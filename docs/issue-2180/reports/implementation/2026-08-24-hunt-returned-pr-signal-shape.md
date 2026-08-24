---
proposal: docs/issue-2180/reports/implementation.md
---

# Hunt record — returned-pr-signal-shape

## before-landing — stance 0: assume the gate/suppression logic just touched is bypassable — find a way an input can defeat it

Verdict: FINDING — the `is_new_pr` one-shot check re-fires `[new-returned-pr]` for a PR already surfaced, because the dedup key embeds the mutable `phase` text, so a phase1→phase2 transition (a normal approval event on an already-open PR) makes `prev_lines.get(key)` miss and the "genuinely-first-sighting" marker is spuriously re-emitted.
Kind: composition
Seed: on-the-record/monitors/poll-heartbeat.sh diff (issue #2180): `is_new_pr = prev_line is None` keyed off `key = f"{m.group(1)}:{m.group(2)}"` where group(2) is `"issue #{issue} ({phase})"` (TAG_RE capturing up to the first colon), fed by relay.py's `_print_returned_pr_surfaced`: `f"[returned-pr] issue #{b['issue']} ({b['phase']}): age={age} — {b['url']}"`.
cap_seconds: 120
tier: default
diff_stat_lines: 33
started_at: 2026-08-24T19:05:20+09:00
ended_at: 2026-08-24T19:08:30+09:00

### Reproduce
Extracted the embedded heredoc body verbatim from `on-the-record/monitors/poll-heartbeat.sh` (lines 256-414, the `python3 - "$state" "$now"` script) to `/tmp/ph_script.py`, then ran two ticks against a fresh state file for the *same* issue/PR, only flipping `phase1` -> `phase2` (i.e. simulating the PR getting its first approval while still open — a routine, expected event, not a new PR):

```
rm -f /tmp/state.json
POLL_HEARTBEAT_TEXT='[returned-pr] issue #999 (phase1): age=1.0h — https://github.com/org/repo/pull/999' \
  python3 /tmp/ph_script.py /tmp/state.json 1000
# -> emits [new-returned-pr] ... (correct: first sighting)

POLL_HEARTBEAT_TEXT='[returned-pr] issue #999 (phase2): age=1.5h — https://github.com/org/repo/pull/999' \
  python3 /tmp/ph_script.py /tmp/state.json 1100
```

### Observed
Second tick (same PR #999, only the phase text changed) still writes:
```
[new-returned-pr] issue #999 (phase2): age=1.5h — https://github.com/org/repo/pull/999
[returned-pr] issue #999 (phase2): age=1.5h — https://github.com/org/repo/pull/999
```
i.e. the "genuinely-first-sighting" marker fires a second time for a PR that was already surfaced one tick earlier, purely because its dedup key (`returned-pr:issue #999 (phase2)`) differs from the prior tick's key (`returned-pr:issue #999 (phase1)`) — `prev_lines.get(new_key)` is `None`, so `is_new_pr` is (wrongly) `True` again.

### Expected
`[new-returned-pr]` should be a strict one-shot per underlying PR (per issue number), matching the fix's own stated intent ("a genuinely-first-sighting returned-pr entry gets its own distinctly-tagged line ... so it reads as its own event"). Because the key incorporates the phase label rather than just the issue number, any phase1→phase2 transition on an already-surfaced, still-open PR is silently treated as a brand-new PR sighting and re-announced — the same failure mode (spurious re-announcement) the age= stripping in issue #1719 was specifically added to prevent for the base `changed` check, but that stripping doesn't apply to the key itself, only to the `changed` comparison once two lines already share a key.

### Resolution
Fixed in the same commit, before landing: `is_new_pr` detection moved off the phase-qualified diff key onto a separate, persisted `surfaced_returned_pr_issues` set keyed by the bare `#<issue>` token (extracted via `ISSUE_TOKEN_RE`), pruned each tick to issue tokens still present in the current returned-pr set. The plain `[returned-pr]` line's own re-emission on a phase change is untouched (still correctly driven by the phase-qualified key — a real content change). Regression-pinned by `on-the-record/monitors/test_poll_heartbeat.py`'s `t_returned_pr_phase_transition_does_not_refire_new_marker`, which reproduces this exact phase1→phase2, same-issue-number two-tick sequence and asserts `[new-returned-pr]` fires on tick 1 only. Full detail in docs/issue-2180/reports/implementation.md's Open findings section.
