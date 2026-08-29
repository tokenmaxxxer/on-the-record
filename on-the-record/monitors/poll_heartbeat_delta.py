#!/usr/bin/env python3
"""issue #2266 (fixes #1719's recurring landmine, #2181's regression):
line-keyed delta diff for on-the-record/monitors/poll-heartbeat.sh's due
tick. Used to live inline as a `python3 - <<'PY' ... PY` heredoc inside
poll-heartbeat.sh's `diff_output="$( ... )"` capture; bash 3.2 miscounts
quote nesting through a heredoc body while scanning for the enclosing
$( )'s own closing paren, so an edit that changed the heredoc body's total
apostrophe count could flip `bash -n` from clean to a syntax error
(#1719 first hit this at an even count, #2181's comment edits flipped it
back to odd). Extracting the script to its own file removes the heredoc —
and the landmine — entirely, rather than re-balancing the apostrophe
count as a workaround.

Invoked as:
  POLL_HEARTBEAT_TEXT=<tick text> python3 poll_heartbeat_delta.py \\
      <state_json_path> <now_epoch_seconds>

Reads the tick's captured watchdog report from the POLL_HEARTBEAT_TEXT
env var, diffs it line-by-line against the previous tick's persisted
state, and prints only the lines that changed (or belong to an
always-emit category), per docs/issue-1220/proposals/delta-only-monitor-emission.md.
"""
import hashlib
import json
import os
import re
import sys

TAG_RE = re.compile(r"^\[(poll-report|watchdog|health|reconcile|orphaned|resume|watchdog-crash|returned-pr)\]\s*([^:]+):")
ENTRY_RE = re.compile(r"^([\w./-]+/[\w./-]+):\s")
BULLET_RE = re.compile(r"^\s+-\s")
# issue #1719: [returned-pr] no longer joins the always-emit set —
# it is compared below with its age= token stripped instead, so an
# unchanged set doesn't re-announce every tick (supersedes #1239 req 2).
# issue #2133: [awaiting-approval] joins the always-emit set — the healthy
# approval pause must reach the Monitor relay every tick (the remaining-time
# token changes anyway, but the always-emit membership is the contract).
ALWAYS_RE = re.compile(
    r"^\[(resume|orphaned|watchdog-crash|awaiting-approval)\]|STALLED|CRASHED|COMPLETED|watcher-dead",
    re.IGNORECASE,
)
AGE_STRIP_RE = re.compile(r"age=[^ ]+")
# issue #2180: short "#<issue>" label extracted for the collapsed
# still-pending summary line and the distinct new-item marker below.
ISSUE_TOKEN_RE = re.compile(r"#\d+")
# issue #1719: two watchdogs contending for the cross-workspace board-sweep
# lock make this line alternate between a real sweep result and this skip
# text tick to tick; treat the skip text as no-change (never emitted, prior
# sweep state kept) instead of flapping the delta state.
BOARD_SWEEP_LOCK_SKIP_RE = re.compile(
    r"^\[watchdog\] board-sweep:.*건너뜀 \(다른 워크스페이스가 스윕 중\)"
)
# issue #1734: lines matching none of TAG_RE/ENTRY_RE/BULLET_RE used to
# share one fixed placeholder key literal, disambiguated only by an
# appearance-order ordinal -- inserting or dropping one such line shifted
# every following line onto a different ordinal and the delta comparison
# then compared it against a different lines previous text, emitting
# unchanged content as "changed". FIXED_TAG_RE derives a content-carried
# key instead: a broader bracket-tag prefix (not just TAG_REs enumerated
# set) plus a hash of the full line, so a key travels with its own
# content and position no longer matters.
FIXED_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*([^:]+):")


def main() -> None:
    state_path, now_s = sys.argv[1], sys.argv[2]
    now = int(now_s)
    text = os.environ.get("POLL_HEARTBEAT_TEXT", "")
    lines = text.split("\n") if text else []

    curr = {}
    order = []
    last_key = None
    bullet_ordinal = 0
    for line in lines:
        m = TAG_RE.match(line)
        if m:
            key = f"{m.group(1)}:{m.group(2)}"
            last_key = key
            bullet_ordinal = 0
        elif ENTRY_RE.match(line):
            key = f"entry:{ENTRY_RE.match(line).group(1)}"
            last_key = key
            bullet_ordinal = 0
        elif BULLET_RE.match(line) and last_key is not None:
            key = f"{last_key}#{bullet_ordinal}"
            bullet_ordinal += 1
        else:
            line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()[:12]
            fm = FIXED_TAG_RE.match(line)
            if fm:
                key = f"fixed:{fm.group(1)}:{fm.group(2).strip()}:{line_hash}"
            else:
                key = f"fixed:hash:{line_hash}"
        if key in curr:
            # collision within one tick's text (e.g. two genuinely singleton
            # lines) — keep both by disambiguating with an ordinal so neither
            # is silently dropped.
            n = 1
            while f"{key}~{n}" in curr:
                n += 1
            key = f"{key}~{n}"
        curr[key] = line
        order.append(key)

    prev = {"lines": {}, "last_emit_epoch": 0}
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                prev.update(loaded)
        except (OSError, ValueError):
            pass
    prev_lines = prev.get("lines", {})
    first_tick = not os.path.exists(state_path)
    # issue #2180 warrant-hunt finding: the returned-pr diff key
    # (`returned-pr:issue #N (phaseX)`) bakes in the phase label, so a
    # phase1->phase2 transition on the SAME still-open PR (relay.py's
    # _undispositioned_skill_prs reclassifies one gh-pr-list entry's phase in
    # place -- same url/number, new phase label once approved) is a brand
    # new diff key even though it is not a brand new PR. Using that key
    # directly for "is this PR new" would re-fire the [new-returned-pr]
    # marker on every phase transition of an already-surfaced PR. Tracked
    # separately here, keyed by the bare issue number (stable across phase
    # relabeling), persisted across ticks in the same state file.
    surfaced_issues = set(prev.get("surfaced_returned_pr_issues", []))

    to_emit = []
    new_lines = {}
    new_pr_markers = []
    for key in order:
        line = curr[key]
        if BOARD_SWEEP_LOCK_SKIP_RE.search(line):
            # lock-contention skip is not a real state change: carry the
            # previously known board-sweep line forward (or, if none was ever
            # recorded, fall back to the skip text itself) and never emit it.
            new_lines[key] = prev_lines.get(key, line)
            continue
        new_lines[key] = line
        if key.startswith("returned-pr:"):
            prev_line = prev_lines.get(key)
            changed = prev_line is None or (
                AGE_STRIP_RE.sub("age=", prev_line) != AGE_STRIP_RE.sub("age=", line)
            )
            m1 = ISSUE_TOKEN_RE.search(line)
            issue_token = m1.group(0) if m1 else key
            if issue_token not in surfaced_issues:
                # issue #2180: a returned-pr entry whose issue number has
                # never been surfaced before gets its own distinctly-tagged
                # line, prepended ahead of the rest of this tick's body
                # below, so it reads as its own event instead of blending
                # into the routine heartbeat around it. The original
                # [returned-pr] line is kept too (still appended to to_emit
                # below, unchanged) for any existing consumer of that exact
                # tag. Keyed by issue number, not the phase-qualified diff
                # key above, so a later phase transition on the same PR
                # does not re-fire this marker.
                new_pr_markers.append(line.replace("[returned-pr]", "[new-returned-pr]", 1))
                surfaced_issues.add(issue_token)
        else:
            changed = prev_lines.get(key) != line
        if first_tick or changed or ALWAYS_RE.search(line):
            to_emit.append(line)

    # issue #2180: drop surfaced-issue bookkeeping for issues no longer
    # present in this tick's returned-pr set (closed/merged/disposed) -- so
    # a later, genuinely new PR reusing that issue number surfaces fresh
    # instead of inheriting stale suppression.
    surfaced_issues &= {
        (ISSUE_TOKEN_RE.search(curr[k]).group(0) if ISSUE_TOKEN_RE.search(curr[k]) else k)
        for k in order if k.startswith("returned-pr:")
    }

    emitted_now = False
    if to_emit:
        sys.stdout.write("\n".join(new_pr_markers + to_emit) + "\n")
        emitted_now = True
    else:
        last_emit_epoch = int(prev.get("last_emit_epoch", 0) or 0)
        if now - last_emit_epoch >= 1800:
            # issue #1732: the periodic no-op liveness line is dropped --
            # liveness is already covered by the alive marker
            # (poll-heartbeat.sh:105-114). Only the undisposed-PR set #1719
            # req#1 attached to this bound stays visible, and only when
            # non-empty; an empty result leaves emitted_now False so
            # last_emit_epoch (line 343) stays untouched.
            # issue #2180: this used to re-print every current [returned-pr]
            # line verbatim, which is exactly the "already-surfaced PR
            # repeats forever" complaint -- collapsed into one summary line
            # instead, so an already-surfaced PR's full line never reappears
            # here, only its continued presence as a count plus short label.
            returned_pr_keys = [k for k in order if k.startswith("returned-pr:")]
            if returned_pr_keys:
                labels = []
                for k in returned_pr_keys:
                    m2 = ISSUE_TOKEN_RE.search(curr[k])
                    labels.append(m2.group(0) if m2 else k.split(":", 1)[1].strip())
                sys.stdout.write(
                    "[returned-pr-pending] %d PR(s) still awaiting review: %s\n"
                    % (len(returned_pr_keys), ", ".join(labels))
                )
                emitted_now = True

    new_state = {
        "lines": new_lines,
        "last_emit_epoch": now if emitted_now else prev.get("last_emit_epoch", 0),
        "surfaced_returned_pr_issues": sorted(surfaced_issues),
    }
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(new_state, f)


if __name__ == "__main__":
    main()
