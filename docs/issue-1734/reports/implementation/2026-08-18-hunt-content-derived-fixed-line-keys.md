---
proposal: docs/issue-1734/proposals/2026-08-18-content-derived-fixed-line-keys.md
---

# Hunt record — content-derived-fixed-line-keys

## after-proposal — stance 1: composition/silent-failure (FIXED_TAG_RE namespace overlap / hash-fallback stability)

Verdict: FINDING — `FIXED_TAG_RE`'s "stop capture at the first colon" design derives the *identical* `fixed:{tag}:{name}` key for multiple, semantically distinct `[watchdog] board-sweep: ...` sub-messages once they are wrapped by `_board_wide_sweep_all`'s per-repo `f"[{label}] {line}"` prefix (spawn.py:3102) — reproducing, inside the very namespace this proposal introduces to fix it, the exact position-shift "false changed" bug issue #1734 exists to eliminate.
Kind: composition
Seed: docs/issue-1734/proposals/2026-08-18-content-derived-fixed-line-keys.md (proposal text); ground truth on-the-record/monitors/poll-heartbeat.sh:233-347; comparison write site spawn.py:3085-3103, 3155-3339 (`_board_wide_sweep_all` / `_board_wide_sweep`)
cap_seconds: not provided by dispatcher (invoked without an explicit cap/tier message this session)
tier: not provided by dispatcher
diff_stat_lines: N/A (phase-1 proposal, no code diff yet; proposal doc is 71 lines)
started_at: 2026-08-18T00:00:00Z (session start, wall clock not separately logged)
ended_at: 2026-08-18T00:45:00Z (approximate, end of this dispatch)

### Reproduce
`spawn.py`'s `_board_wide_sweep` (called once per roster-target repo by `_board_wide_sweep_all`, spawn.py:3066-3103) can print several different `[watchdog] board-sweep: ...` lines in the same tick for the same repo — e.g. the delta-probe line (spawn.py:3260), the carried-over-categories line (spawn.py:3266), and the budget-exceeded line (spawn.py:3338) are independently gated and can co-occur. Each such line, from a non-arm-root roster repo, gets wrapped as `f"[{label}] {line}"` (spawn.py:3102), producing e.g.:

```
[my-repo] [watchdog] board-sweep: delta 3건 변경 [101, 102, 103] — 해당 subject/이슈만 재평가
[my-repo] [watchdog] board-sweep: 이월 (예산) ['closure-sweep']
[my-repo] [watchdog] board-sweep: 예산 초과 (9건 > 8)
```

canonical: `grep -n 'f"\[watchdog\] board-sweep' spawn.py` (this session) — output confirms lines 3260, 3266, 3338 are three independently-gated `print(f"[watchdog] board-sweep: ...")` call sites inside `_board_wide_sweep`, and spawn.py:3102 (`print(f"[{label}] {line}")`) is the wrap `_board_wide_sweep_all` applies per non-arm-root roster repo.

Since the outer bracket in the wrapped form is the repo `label`, not one of `TAG_RE`'s enumerated tags, these lines fall to the proposal's new `else` branch rather than `TAG_RE`. Ran the proposal's exact keying logic (transcribed verbatim from its "What will be" implementation section) against tick 1 (all three lines above) and tick 2 (same repo, but this tick's `delta` probe didn't fire, so only the carryover and budget-exceeded lines remain, both byte-identical to tick 1):

canonical: `python3 /tmp/repro1734/keying.py` (this session, executed live) — full script transcribed below.

```bash
python3 - <<'PY'
import hashlib, re
TAG_RE = re.compile(r"^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):")
ENTRY_RE = re.compile(r"^([\w./-]+/[\w./-]+):\s")
BULLET_RE = re.compile(r"^\s+-\s")
FIXED_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*([^:]+):")

def key_lines(lines):
    curr, order, last_key, bullet_ordinal = {}, [], None, 0
    for line in lines:
        m = TAG_RE.match(line)
        if m:
            key = f"{m.group(1)}:{m.group(2)}"; last_key = key; bullet_ordinal = 0
        elif ENTRY_RE.match(line):
            key = f"entry:{ENTRY_RE.match(line).group(1)}"; last_key = key; bullet_ordinal = 0
        elif BULLET_RE.match(line) and last_key is not None:
            key = f"{last_key}#{bullet_ordinal}"; bullet_ordinal += 1
        else:
            fm = FIXED_TAG_RE.match(line)
            key = f"fixed:{fm.group(1)}:{fm.group(2).strip()}" if fm else \
                  f"fixed:hash:{hashlib.sha256(line.encode('utf-8')).hexdigest()[:12]}"
        if key in curr:
            n = 1
            while f"{key}~{n}" in curr: n += 1
            key = f"{key}~{n}"
        curr[key] = line; order.append(key)
    return curr, order

label = "my-repo"
tick1 = [
    f"[{label}] [watchdog] board-sweep: delta 3건 변경 [101, 102, 103] — 해당 subject/이슈만 재평가",
    f"[{label}] [watchdog] board-sweep: 이월 (예산) ['closure-sweep']",
    f"[{label}] [watchdog] board-sweep: 예산 초과 (9건 > 8)",
]
tick2 = [
    f"[{label}] [watchdog] board-sweep: 이월 (예산) ['closure-sweep']",  # byte-identical to tick1
    f"[{label}] [watchdog] board-sweep: 예산 초과 (9건 > 8)",           # byte-identical to tick1
]
curr1, order1 = key_lines(tick1)
curr2, order2 = key_lines(tick2)
print("tick1 keys:", order1)
print("tick2 keys:", order2)
prev_lines = dict(curr1)  # tick2 diffs against tick1's persisted state
for k in order2:
    changed = prev_lines.get(k) != curr2[k]
    print(f"key={k!r} changed={changed} new={curr2[k]!r} prev={prev_lines.get(k)!r}")
PY
```

### Observed
```
tick1 keys: ['fixed:my-repo:[watchdog] board-sweep', 'fixed:my-repo:[watchdog] board-sweep~1', 'fixed:my-repo:[watchdog] board-sweep~2']
tick2 keys: ['fixed:my-repo:[watchdog] board-sweep', 'fixed:my-repo:[watchdog] board-sweep~1']
key='fixed:my-repo:[watchdog] board-sweep' changed=True new="[my-repo] [watchdog] board-sweep: 이월 (예산) ['closure-sweep']" prev='[my-repo] [watchdog] board-sweep: delta 3건 변경 [101, 102, 103] — 해당 subject/이슈만 재평가'
key='fixed:my-repo:[watchdog] board-sweep~1' changed=True new='[my-repo] [watchdog] board-sweep: 예산 초과 (9건 > 8)' prev="[my-repo] [watchdog] board-sweep: 이월 (예산) ['closure-sweep']"
```
canonical: `python3 /tmp/repro1734/keying.py` (this session, executed live) — output pasted above verbatim.

Both remaining lines are flagged `changed=True` and would re-emit and wake the orchestration session, even though the "이월 (예산)" and "예산 초과" lines' own text is byte-identical between tick 1 and tick 2 — the only thing that changed tick to tick is that the "delta" sub-message did not fire this time, which shifted the other two onto different `~N` ordinals within the `fixed:my-repo:[watchdog] board-sweep` collision group. This is the same "insertion/removal of one line shifts every following line onto a different ordinal, causing a false 'changed' verdict" mechanism the issue's own bug report describes (survey.md's write-surface #1) — reproduced entirely inside the new content-derived-key namespace the proposal introduces, because `FIXED_TAG_RE`'s `([^:]+):` capture stops at the first colon, so every `[watchdog] board-sweep: <anything>` message emitted through the multi-board wrap (spawn.py:3102) derives the identical `fixed:{label}:[watchdog] board-sweep` key regardless of which of the (at least three) independently-gated board-sweep sub-messages it actually is.

The proposal's Rationale claims the reused ordinal-disambiguation block is "now reached only when two genuinely different lines derive the identical key" — worded as if that were rare/coincidental. This repro shows it is reached routinely, by construction, for a line family already present in the codebase (multi-board roster sweep output), not a coincidence.

### Expected
A content-derived key for this line family should not collapse three independently-gated, semantically distinct board-sweep signals (delta-count, carryover, budget-exceeded) into one ordinal-disambiguated group whose members' identities depend on which sibling messages happened to fire this tick. Either `FIXED_TAG_RE`'s key needs to include enough of each message's distinguishing text (not just tag+name up to the first colon) to keep these apart, or the proposal should acknowledge that the multi-board-wrapped `[watchdog] board-sweep: ...` family is not actually fixed by this change and remains subject to the same class of false "changed" wake-ups the issue reports.
