---
proposal: docs/issue-2610/architecture-module-boundary-definition+silent-failure-audit-cc748487
---

# Hunt record — issue-2610-retire-spawn-roles

## before-landing — stance 0: assume the gate just touched is bypassable -- find the bypass

Verdict: NO FINDING
Seed: gates/gates.py + on-the-record/gates/gates.py (_role_cfg), and the four
on-the-record/hooks/*.sh scripts reading roles/<role>.json directly
cap_seconds: 180
tier: default
diff_stat_lines: ~450 (gates.py x2, roles_due.py, 4 hook .sh files, spawn.py, spec_schema_five_activities_test.py + 44 new roles/*.json)
started_at: 2026-08-27T06:52:00Z
ended_at: 2026-08-27T07:12:00Z

Investigated three candidate bypasses named in the stance.

(a) Path traversal via role name: `role` is always captured by
`RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")`
(canonical: gates/gates.py line 302) — the `[^/]+` capture group cannot
contain `/`, so a traversal `role` value is unreachable through this regex.

(b) except-clause swallowing: `_role_cfg()`'s new body raises
`FileNotFoundError` for an unknown role, still caught by every call site's
`except (OSError, json.JSONDecodeError, KeyError)`.
derived: `cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2610-architecture-module-boundary-definition+silent-failure-audit-cc748487 && python3 -c "import sys; sys.path.insert(0,'gates'); import gates as g; g._role_cfg('nonexistent-role-xyz')" ; echo exit=$?`
— result: raises `FileNotFoundError`, an `OSError` subclass, so every call
site's existing except-tuple still catches it (unchanged, still caught).

(c) Installed-plugin CHECKOUT/roles resolution: `on-the-record/gates/gates.py`'s
`ON_THE_RECORD_ROOT` resolves to the nested `on-the-record` dir itself in a
real installed marketplace checkout, so `_ROLE_DATA_DIR` would point at a
roles subdirectory nested one level too deep that doesn't exist there.
derived: `ls -d /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/roles 2>&1; ls -d /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/roles 2>&1`
— result: `spawn.py` and `roles` exist directly under the marketplace root;
the nested lookup under `on-the-record/` fails with "No such file or
directory". This is a real mismatch, but not new: the pre-#2610 code had the
identical mismatch — `_ROLE_DATA_PATH` also resolved to a nested
`spawn_roles.json` path under `on-the-record/` that never existed.
derived: `test -f /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn_roles.json && echo top-level-exists; test -f /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/spawn_roles.json && echo nested-exists || echo nested-missing; git -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer log --oneline -1`
— result: `top-level-exists`, then `nested-missing`, at commit 9ef9dc4a of
that live clone. In both old and new code the effect is `_role_cfg` raising
`OSError`, which every call site (`record_enums`, `record_refusal_reasoned`,
`record_checked_claims`) turns into a `bad.append(...)` entry — the gate
blocks on this condition, it does not open up. Also confirmed
`gates/roles_due.py` always loads its `gates.py` sibling from its own
directory (canonical: gates/roles_due.py lines 31-46,
`Path(__file__).parent / "gates.py"`), so in a real deployment it uses the
top-level `gates/gates.py` (co-located with the top-level `roles/`), never
the mirror — the mirror's self-location bug is not load-bearing for any live
gate path found.

No reproducible new bypass found for this stance.

## before-landing — stance 1: assume this guard goes silent when its own input is malformed -- make it go silent

Verdict: FINDING
Kind: silent-failure
One-line statement: delegated-judgment-gate.sh's load_roles() silently drops
any one role whose roles/<role>.json fails to parse, with no error and no
observable difference in the gate's allow-vs-escalate result, where the
pre-#2610 single-file version's equivalent corruption reliably forced
`escalate("no eligible role owns an implicated judgment axis")` on every
decision — see "Observed" below for the live run this rests on.
Seed: on-the-record/hooks/delegated-judgment-gate.sh (load_roles(), line 440; ROLES = load_roles(), line 457; escalate("no eligible role owns an implicated judgment axis"), line 625)
cap_seconds: 180
tier: default
diff_stat_lines: ~450
started_at: 2026-08-27T07:12:00Z
ended_at: 2026-08-27T07:24:00Z

### Reproduce

```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2610-architecture-module-boundary-definition+silent-failure-audit-cc748487
rm -rf /tmp/roles-test && cp -r roles /tmp/roles-test
# simulate the ordinary way a role file goes bad: a truncated/partial write
# (e.g. an interrupted commit, a bad merge) leaves syntactically invalid JSON
python3 -c "
data = open('/tmp/roles-test/architecture.json').read()
open('/tmp/roles-test/architecture.json','w').write(data[:len(data)//2])
"
# this is load_roles() from on-the-record/hooks/delegated-judgment-gate.sh
# lines 440-455, copied verbatim
python3 -c "
import json
from pathlib import Path
def load_roles(TARGET):
    role_data_dir = TARGET / 'roles'
    if not role_data_dir.is_dir():
        return {}
    out = {}
    for f in role_data_dir.glob('*.json'):
        try:
            cfg = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if isinstance(cfg, dict):
            out[f.stem] = cfg
    return out
class FakeTarget:
    def __truediv__(self, other): return Path('/tmp/roles-test')
ROLES = load_roles(FakeTarget())
print('architecture in ROLES?', 'architecture' in ROLES)
print('total roles loaded:', len(ROLES), 'of', len(list(Path('/tmp/roles-test').glob('*.json'))))
"
```
canonical: on-the-record/hooks/delegated-judgment-gate.sh lines 440-455 (load_roles body, verbatim in the command above), lines 614-625 (standing_roles/implicated_axes/eligible_roles/escalate)

### Observed

derived: the exact python3 command block above, run live in this session
against a copy of this PR's own `roles/` directory with `architecture.json`
truncated to invalid JSON:
```
architecture in ROLES? False
total roles loaded: 43 of 44
```
No stderr, no exception propagated, no trace of the corrupted file anywhere
in the gate's output. `standing_roles = set(ROLES)` (line 614) and
`implicated_axes`/`eligible_roles` (lines 616-621) are built entirely from
the 43 survivors; as long as some other role's `judgment_axes` happens to
cover whatever axis a decision item implicates, `eligible_roles` is
non-empty and `escalate("no eligible role owns an implicated judgment axis")`
(line 625) never fires — panel composition silently proceeds one role
short, indefinitely, until someone happens to notice `architecture.json` is
broken by unrelated means.

### Expected

Before #2610, `load_roles()` parsed one `spawn_roles.json` file
(`data = json.loads(role_data_file.read_text(...))`).
derived: `git -C /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2610-architecture-module-boundary-definition+silent-failure-audit-cc748487 show origin/main:on-the-record/hooks/delegated-judgment-gate.sh | sed -n '438,455p'`
A syntactically invalid entry anywhere in that file raises during the single
`json.loads` call, caught by the same try/except but returning `{}` for all
44 roles at once, not just the broken one. With `ROLES = {}`,
`standing_roles` is empty, `eligible_roles` is always empty, and
`escalate(...)` fires unconditionally on every decision-item evaluation from
that point on — a loud, unmissable failure mode that gets fixed immediately
because nothing works. Splitting into `roles/<role>.json` traded that
guaranteed, impossible-to-miss total failure for a per-role partial failure
that produces no signal at all: the gate keeps issuing its normal
allow/escalate verdicts, just without one role's judgment axes ever being
considered, and nothing in this hook's own output distinguishes that state
from "architecture doesn't need to weigh in here."
