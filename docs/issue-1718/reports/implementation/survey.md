# Survey — issue #1718

Scout skip condition: pure bugfix. The issue names the exact fix
direction against one existing file,
`on-the-record/hooks/decision-queue-stopgate.sh` — (1) a `stop_hook_active`
guard that must suppress every emission, not only the two branches that
already check it, and (2) a checkout-scope filter on `decision_queue`
items — with acceptance cases already pointed at the existing test file
`on-the-record/hooks/test_decision_queue_stopgate.py`. No product-facing
or design decision is open — this scouts nothing and the sweep protocol
is skipped per the scout-directive's mandatory skip record. This mirrors
`docs/issue-1021/reports/implementation/survey.md`'s skip record for the
same file/same class of fix.

## Current state — bug 1 (stop_hook_active only partially honored)

canonical: on-the-record/hooks/decision-queue-stopgate.sh (read in full
this session)

Issue #1021 already taught this hook to read
`stop_hook_active = bool(stdin_payload.get("stop_hook_active"))`
(on-the-record/hooks/decision-queue-stopgate.sh:72) and to use it in two
places: the waiting-declaration branch's block condition
(on-the-record/hooks/decision-queue-stopgate.sh:217) and the tier2
(age >= 4h) branch's degrade-to-advisory condition
(on-the-record/hooks/decision-queue-stopgate.sh:265). Neither place makes
the hook emit *nothing* — both still write JSON to stdout on a
`stop_hook_active` turn.

derived: `sed -n '260,278p' on-the-record/hooks/decision-queue-stopgate.sh`
```
if tier2:
    tier2_ids = sorted(
        {(i.get("issue"), i.get("pr")) for i in tier2}, key=lambda t: repr(t)
    )
    names = ", ".join(_name(i) for i in tier2)
    if stop_hook_active or _load_tier2_last_blocked_ids() == tier2_ids:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": (
                    "decision-queue-stopgate: decision-queue items have "
                    "aged past 4h with no operator decision: " + names + ". "
                    "Already blocked once for this queue snapshot -- "
                    "degrading to advisory instead of repeating the block."
                ),
            }
        }
        sys.stdout.write(json.dumps(out))
        sys.exit(0)
```
When `stop_hook_active` is true, tier2 still writes an
`additionalContext` payload (just not `decision: "block"`) — this is the
loop the issue reports, since the harness treats any Stop
`additionalContext` as inject-and-resume regardless of whether the
emitting branch calls itself "advisory".

The tier1 (`1 <= age_hours < 4`) branch has no `stop_hook_active` check
at all:

derived: `sed -n '292,303p' on-the-record/hooks/decision-queue-stopgate.sh`
```
names = ", ".join(_name(i) for i in tier1)
out = {
    "hookSpecificOutput": {
        "hookEventName": "Stop",
        "additionalContext": (
            "decision-queue-stopgate: decision-queue items waiting on an "
            "operator decision: " + names + "."
        ),
    }
}
sys.stdout.write(json.dumps(out))
sys.exit(0)
```
This branch always emits `additionalContext` on a non-empty tier1 queue,
`stop_hook_active` or not.

## Current state — bug 2 (queue not scoped to this checkout)

canonical: gates/flows.py (read in full this session)

`decision_queue` is built by `gates/flows.py`'s `flows_payload()`, which
the hook fetches verbatim via `spawn.py flows --json`
(on-the-record/hooks/decision-queue-stopgate.sh:56). Issue #1035 already
added an ownership filter, `_own_item()`, but its own comment states the
filter cannot deny ownership when the local roster has no observation of
an item at all — it defaults to *showing* it:

derived: `sed -n '358,367p' gates/flows.py`
```
def _own_item(subject: str, role: str) -> bool:
    if all_scope:
        return True
    key = f"{subject}/{role}"
    # 이슈 #1035: 로스터에 아예 항목이 없으면(둘 다 관측 불가) 소유를
    # 부정할 수 없다 -- `_roster_own`의 observation-loss invariant와
    # 동일하게 계속 노출한다. 로스터에 있는데 다른 세션 소유일 때만 뺀다.
    if key not in roster_all:
        return True
    return key in roster_own_keys
```
`roster_all` comes from `spawn._roster_load()`, which reads
`ROOT / "runs" / "active.json"` where `ROOT = Path(__file__).resolve().parent`
(spawn.py:40, spawn.py:76-77) — i.e. wherever *this* `spawn.py` file
lives, not any particular target repo. For #1712, the spawning session
ran from a different checkout of `spawn.py` entirely, so this checkout's
`roster_all` never had a `issue-1712/*` key to begin with —
`_own_item()` can't distinguish "no observation" from "not mine" and
defaults to showing the item, exactly the reported symptom.

`gates/flows.py`'s payload already carries two other checkout-local
signals the hook does not currently look at:

derived: `sed -n '463,471p' gates/flows.py`
```
return {
    "schema_version": FLOWS_SCHEMA_VERSION,
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "repo": repo_slug,
    "decision_queue": decision_queue,
    "flows": flows_out,
    "sessions": sessions,
    "ledger": sorted(ledger_by_issue.values(), key=lambda d: d["issue"]),
    "unattributed": unattributed,
```
`sessions` (gates/flows.py:421-433) is built from the same
`spawn._roster_load()` used above, one entry per roster key, each
carrying `"issue": e.get("issue")` — this is "the active roster" the
issue's acceptance text names. `ledger` (gates/flows.py:435-450) is
built from `runs/ledger.jsonl` (also rooted at this checkout's `ROOT`,
spawn.py:5109) aggregated per issue via `_ledger_issue()` — this is "the
runs ledger" the issue names. Both are already present on the same
`flows --json` payload the hook already parses
(`STOPGATE_FLOWS_JSON` -> `flows` dict,
on-the-record/hooks/decision-queue-stopgate.sh:98). No new spawn.py or
flows.py surface is needed to answer "does this checkout have a spawn
record for issue N" — the data is already on the payload the hook holds.

## Write set implied

- `on-the-record/hooks/decision-queue-stopgate.sh`:
  - one guard: immediately after computing `stop_hook_active`
    (on-the-record/hooks/decision-queue-stopgate.sh:72), exit 0 with no
    stdout when it is true — before the role check, before the queue is
    even read, so every branch below (waiting-declaration, tier1, tier2)
    is unreachable on such a turn.
  - one filter: right after the existing `decision_queue` empty check
    (on-the-record/hooks/decision-queue-stopgate.sh:104-106), drop any
    queue item whose `issue` does not appear in `flows.get("sessions")`
    or `flows.get("ledger")`, then re-check emptiness.
- `on-the-record/hooks/test_decision_queue_stopgate.py`: cases for both
  guards named in the issue's Acceptance section — `stop_hook_active`
  true emits nothing regardless of queue age/branch; an item absent from
  both `sessions` and `ledger` is silently skipped; an item present in
  either still surfaces.
- a phase-2 implementation record, written at the start of phase 2, at
  this issue's standard report path under docs/issue-1718/reports/ (not
  yet created — phase-2 output, per the record-shape directive).

No new dependency, no new env var, no change to `spawn.py` or
`gates/flows.py` — both signals the filter needs already exist on the
payload the hook already fetches.
