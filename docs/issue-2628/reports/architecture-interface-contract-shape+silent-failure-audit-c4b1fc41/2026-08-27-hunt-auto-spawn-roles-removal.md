---
proposal: docs/issue-2628/proposals/architecture-interface-contract-shape+silent-failure-audit-c4b1fc41.md
---

# Hunt record — auto-spawn-roles-removal

## before-landing — stance 0: assume the gate/mechanism just touched is bypassable — find the bypass

Verdict: FINDING — replacing named AUTO_SPAWN_ROLES identity with positional `independent-verification-<slot>` naming (slot = `range(1, deficit+1)`, recomputed fresh every tick from the current count) lets `park_state`/`MAX_RESPAWN_ATTEMPTS` state silently attach to the wrong logical requirement whenever the lower-numbered slot resolves first, resetting a genuinely-stuck verifier's attempt count and defeating the respawn ceiling backstop.
Kind: composition
Seed: commit eb61de56, gates/spawn_on_pr.py (`verification_deficit()`, `spawn_missing_for_pr()`'s `for slot in range(1, deficit + 1): all_pairs.append((subject, f"independent-verification-{slot}", pr_number))`, park_state keyed `f"{subject}/{role}"`)
cap_seconds: 180
tier: default
diff_stat_lines: gates/spawn_on_pr.py 246 changed, gates/test_spawn_on_pr.py 24 changed, test/test_verifies_subject_scaffold.py 8 changed (141 insertions(+), 137 deletions(-) total per `git show HEAD --stat`)
started_at: 2026-08-27T08:22:00Z
ended_at: 2026-08-27T08:29:00Z

### Reproduce

Ad hoc script (no repo files modified), run from repo root with `gates/` on `sys.path`:

```python
import sys, json, tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, ".")
sys.path.insert(0, "gates")
import spawn_on_pr

SUBJECT = "issue-88002"
tmp = Path(tempfile.mkdtemp())
park_path = tmp / "spawn_on_pr_parked.json"

def run(missing_dict, blocked, backoff_state):
    with mock.patch.object(spawn_on_pr, "_park_state_path", lambda root: park_path), \
         mock.patch.object(spawn_on_pr, "missing_verification",
                            lambda root, issue_states=None, pr_index=None: dict(missing_dict)), \
         mock.patch.object(spawn_on_pr, "subject_deliverable_branch",
                            lambda subject, pr_index: f"{subject}/impl"), \
         mock.patch.object(spawn_on_pr, "_pr_number_for_branch",
                            lambda root, branch, pr_index: 1), \
         mock.patch.object(spawn_on_pr, "resolve_live_base", lambda root: "deadbeef"), \
         mock.patch.object(spawn_on_pr, "is_approval_blocked", lambda root, issue, role: blocked), \
         mock.patch.object(spawn_on_pr.spawn, "roster_register", lambda *a, **k: None), \
         mock.patch.object(spawn_on_pr.spawn, "_spawn_one", lambda *a, **k: None), \
         mock.patch.object(spawn_on_pr.spawn, "ledger_write", lambda entry: None):
        return spawn_on_pr.spawn_missing_for_pr(
            tmp, str(tmp), dry_run=False, issue_states=None,
            backoff_state=backoff_state, pr_index={}, max_respawn_attempts=4)

# Seed state as if REQUIRED_INDEPENDENT_VERIFICATIONS=2, deficit was 2 last
# tick: slot "independent-verification-1" (session A) just landed its
# verifies_subject record after 1 attempt. Slot "independent-verification-2"
# (session B) is the REAL troublemaker -- already respawned 3 times
# (attempts=3), one more push hits the MAX_RESPAWN_ATTEMPTS=4 ceiling.
park_path.parent.mkdir(parents=True, exist_ok=True)
park_path.write_text(json.dumps({
    f"{SUBJECT}/independent-verification-1": {"blocked": True, "pr_number": 1,
                                                "parked": False, "attempts": 1},
    f"{SUBJECT}/independent-verification-2": {"blocked": True, "pr_number": 1,
                                                "parked": False, "attempts": 3},
}))

backoff_state = {}
# This tick: session A's record landed -> total deficit 2 -> 1. Session B
# is still stuck, unchanged.
pairs = run({SUBJECT: 1}, blocked=False, backoff_state=backoff_state)
print("pairs spawned this tick:", pairs)
print(json.loads(park_path.read_text()))
```

### Observed

```
pairs spawned this tick: [('issue-88002', 'independent-verification-1')]
{'issue-88002/independent-verification-1': {'attempts': 2, 'blocked': True, 'parked': False, 'pr_number': 1},
 'issue-88002/independent-verification-2': {'attempts': 3, 'blocked': True, 'parked': False, 'pr_number': 1}}
```

Session B is really on its 4th respawn (attempts was already 3), which
should hit `MAX_RESPAWN_ATTEMPTS=4` this tick and print `CEILING HIT` /
write a `spawn_on_pr_respawn_ceiling_hit` ledger event so a human
intervenes (this is exactly what issue #2238's ceiling backstop exists to
guarantee — "not loop forever, and not silently no-op if some future bug
defeats the park rule again", per this file's own `MAX_RESPAWN_ATTEMPTS`
comment). Instead it silently respawned again with `attempts: 2` under
key `independent-verification-1`, no ceiling warning at all, no ledger
event. Session B's real history (`attempts: 3`) is now permanently
orphaned under key `independent-verification-2` and never read again
(that position no longer exists once deficit drops to 1). It will take
two more ticks before the ceiling has any chance of tripping for what is
actually already a 4th-attempt case — and if a third, well-behaved slot
resolves in between and shifts numbering again, the reset can repeat.

Root cause: `spawn_missing_for_pr()` regenerates slot names purely
positionally every tick (`for slot in range(1, deficit + 1)`), and
`park_state`/roster keys are `f"{subject}/{role}"` where `role` is that
positional slot name. Nothing ties a slot name to a specific ongoing
verifier session — when a *lower*-numbered slot resolves before a
higher-numbered one, the higher slot's outstanding attempt history is
silently discarded and replaced by whatever stale entry happens to sit
at its new (lower) position. Under the old `AUTO_SPAWN_ROLES` scheme,
role names (`execution-observation`, `conformance-review`) were stable
per-kind identities that a sibling role resolving could never renumber,
so this collision could not arise.

### Expected

The respawn ceiling should trip precisely when the same underlying
verification requirement has been respawned `max_respawn_attempts`
times, regardless of the order in which sibling slots for the same
subject resolve. Slot identity would need to stay stable across ticks
(not a position recomputed from the live deficit count each tick), or
the park/ceiling state would need explicit migration when the slot
count shrinks instead of silent positional reuse.
