# Current-state survey — issue #2093 hook-crash class fix

kind: survey
loop_state: surveyed

Scope of this survey: the write surfaces the eventual proposal expects to touch —
`on-the-record/hooks/hooks.json` (the registry the conformance test is driven from),
the embedded-python input-parsing preamble shared in spirit (but not in code) by the
registered hook scripts, `on-the-record/hooks/contract-guard.sh` (the #2092 instance),
and the append-only ledger convention a fail-open record would have to follow.

## 1. How many hooks are registered, and under which events

derived:
```
$ python3 -c "
import json
d = json.load(open('on-the-record/hooks/hooks.json'))
for event, groups in d['hooks'].items():
    n = sum(len(g['hooks']) for g in groups)
    print(event, n)
print('TOTAL', sum(sum(len(g['hooks']) for g in groups) for groups in d['hooks'].values()))
"
SessionStart 2
UserPromptSubmit 5
PreToolUse 41
PostToolUse 2
Stop 8
TOTAL 58
```

58 registrations, not ~40: the issue text undercounts because it thinks in scripts,
while `hooks.json` counts *entries* — the same script can be registered more than once
under different `matcher` blocks or with different argv (e.g. `retry-loop-bound.sh pre`
under PreToolUse and `retry-loop-bound.sh post` under PostToolUse). The conformance
test's unit must be the registration, not the script file, because argv changes which
code path parses the input.

## 2. The actual input-parsing idiom (the issue's premise needs correcting)

canonical: read of the embedded python blocks in acceptance-command-real-run-guard.sh,
accessibility-guard.sh, call-shape-guard.sh, merge-allow-gate.sh, stop-gate.sh,
pr-preflight.sh, delegated-judgment-gate.sh, directive.sh, session-role-bind.sh,
retry-loop-bound.sh, record-scaffold.sh

No hook does `json.load(sys.stdin)` inside its python. The dominant idiom is: bash
captures stdin once, exports it as a per-hook env var, and the python snippet does
`json.loads(os.environ.get("<PREFIX>_PAYLOAD", ""))` — typically under `python3 -c "$GUARD"`
where `$GUARD` was read from a quoted heredoc into a bash variable. A smaller family uses
`python3 - <<'PY'` against a `payload_raw` variable (`directive.sh`, `session-role-bind.sh`,
`retry-loop-bound.sh`, `record-scaffold.sh`).

Consequence for the design: the shared library's entry point cannot be "read stdin" —
it must accept a raw string, because the transport into python is already an env var in
most hooks. A stdin-reading helper would be unusable by the majority of the corpus.

Every sampled `json.loads` on the payload is already inside a `try/except` that exits 0.
So the crash class is **not** the JSON decode. It is what happens *after* a successful
decode: the ad-hoc command/cd-target extraction and the filesystem calls made with the
values it produces.

## 3. `cd`-target extraction — the actual crash surface

Three coexisting idioms, none of them shared.

(a) Raw regex on the whole command string, `on-the-record/hooks/contract-guard.sh:94-96`:
```python
cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
if cd_m:
    target_cwd = cd_m.group(1)
```

Byte-identical copy at `on-the-record/hooks/merge-allow-gate.sh:167-169`:
```python
cd_m = re.match(r"^\s*cd\s+(\S+)\s*&&", cmd)
if cd_m:
    target_cwd = cd_m.group(1)
```

(b) Positional token equality against a pre-tokenized list, `post-landing-obligation-gate.sh:98-104`
and the same structure at `quality-bar-gate.sh:130-137`.

(c) A separate extraction heredoc whose result is captured through stdout,
`absorbed-branch-recut-guard.sh:58-62` feeding line 91.

Defect: `(\S+)` captures `~/repo` verbatim and no site applies `os.path.expanduser`
to it. The captured string is then used as a real path — `cwd=target_cwd` on a
`subprocess.run`, or joined via `os.path.join(target_cwd or os.getcwd(), ...)` — which
raises `FileNotFoundError` on an unexpanded `~`. That is #2092, and it is duplicated
verbatim in at least a second hook, which is what makes it a class rather than an instance.

The same regex is also wrong for `cd 'a b' && ...` (quoted path), `cd $DIR &&`, and any
command whose `cd` is not the leading token. It silently returns `None` there rather than
crashing — a quieter failure of the same parser.

## 4. `os.path.expanduser` in the hooks dir

derived:
```
$ grep -rn "expanduser" on-the-record/hooks/*.sh
on-the-record/hooks/contract-guard.sh:256:    log_path = os.path.expanduser(
on-the-record/hooks/directive.sh:64:    ...os.path.expanduser("~/.claude/tokenmaxxxer/monitor-alive")
```
Two hits, both on fixed `~/.claude/...` state paths. Neither is applied to a
`cd`-extracted target. The expansion competence exists in the dir; it has simply never
been wired to the value that needs it.

## 5. Where a shared module can live — the constraint that decides placement

canonical: read of on-the-record/hooks/pr-preflight.sh:7-9

```
# gates/pr_reference.py::check_body and gates/flows.py::_plan_from_body
# inline rather than importing them, because a zero-install hook cannot
# assume gates/ is on sys.path in the consumer repo.
```

This is the load-bearing constraint. Nine hooks *do* `sys.path.insert` a `gates/` dir
(`impact-guard.sh:108`, `plan-order-guard.sh:100`, `quality-bar-gate.sh:95`,
`skill-verdict-guard.sh:195`, `role-spec-reference-guard.sh:84`,
`record-claim-shape-directive.sh:45`, `record-claim-guard.sh:89`, plus
`credential-network-guard.sh:72` / `credential-record-guard.sh:61` which insert a
*hooks* dir from an env var) — but they are the hooks that only ever run inside this
repo. `pr-preflight.sh` documents why a hook that must run against an arbitrary consumer
repo cannot: `gates/` is not guaranteed to exist there.

The resolution idiom when a hook does import, `role-spec-reference-guard.sh:29-35`:
```bash
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gates_dir=""
if [ -d "$script_dir/../gates" ]; then
    gates_dir="$(cd "$script_dir/../gates" && pwd)"
elif [ -d "$script_dir/../../gates" ]; then
    gates_dir="$(cd "$script_dir/../../gates" && pwd)"
fi
```
It probes two relative depths because the hook may run from the plugin dir or from a
consumer checkout. `credential-network-guard.sh:72` shows the other half of the pattern:
inserting the *hooks' own dir*, which always exists next to the hook wherever it was
copied — that is the only sys.path entry a zero-install hook can rely on.

## 6. Tests and test tiering

`on-the-record/hooks/` already holds ~45 `test_*.py` files (`test_contract_guard.py`,
`test_merge_allow_gate.py`, `test_pr_preflight.py`, …), so the acceptance-named path
`on-the-record/hooks/test_hook_crash_conformance.py` sits in an established home.

Root `pytest.ini` sets `addopts = -n auto`, `norecursedirs = runs harness/fixture-redtest
harness/fixture-target`, and declares a `slow` marker: "real subprocess spawn or real git
clone/checkout lifecycle tests, excluded by default (issue #1490)". No `testpaths`.

`.on-the-record/test-tiers.json` exists at repo root:
```json
{
  "fast": {"command": "python3 -m pytest -q -m \"not slow\"", "budget_seconds": 300},
  "slow": {"command": "python3 -m pytest -q -m slow",
    "trigger_change_classes": ["spawn.py", "...", "on-the-record/hooks/*.sh", "on-the-record/hooks/test_*.py"]}
}
```
Both `on-the-record/hooks/*.sh` and `on-the-record/hooks/test_*.py` are declared slow-tier
triggers, so this issue's diff will trigger the slow suite by the repo's own contract.

Cost shape the conformance test must respect: 58 registrations x a ~9-case corpus is
~522 real subprocess spawns. At a conservative 40ms/spawn that is ~20s serial; `-n auto`
divides it, but it is unambiguously slow-marker territory, not a default-suite cost.

## 7. Existing append-only ledger convention

The top-level `ledger/` package (`ledger/decisions.py`, `ledger/collect.py`) is
citation/decision bookkeeping, unrelated to per-invocation hook logging.

The convention hooks actually use is a JSONL provenance log, `contract-guard.sh:249-274`:
```python
log_path = os.path.expanduser(
    os.environ.get("CONTRACT_GUARD_PROVENANCE_LOG")
    or "~/.claude/on-the-record/hook-provenance.log"
)
os.makedirs(os.path.dirname(log_path), exist_ok=True)
```
One JSON object per line, append mode, env-overridable path (which is what makes it
testable), and the whole write wrapped in `try/except Exception: pass` so a log failure
can never change the gate's verdict. Only `contract-guard.sh` uses it today — it is a
file-local pattern, not yet shared. A fail-open ledger should adopt this shape rather
than invent a second one.

`pytest.ini`'s `norecursedirs = runs` implies a `runs/` directory convention elsewhere in
the repo; its line format was not read in this pass.

unverifiable: the `runs/` line format — not read in this pass; the issue text names `runs/`
as the ledger home, but the only hook-authored ledger precedent found is the
`~/.claude/on-the-record/` JSONL above, so the proposal must pick one deliberately.

## 8. Status of #2092 (the instance fix)

canonical: `git log --all --oneline | grep -i 2092` and `git show --stat 221ec300`

derived:
```
$ git show --stat 221ec300
commit 221ec300a1bec2b60716cbd946478fd053bd5722
    issue-2092: consult-trace (ok)
 docs/issue-2092/reports/consult-log.md | 1 +
 1 file changed, 1 insertion(+)
```

The only #2092 commit reachable anywhere is a one-line consult-trace bookkeeping commit.
No implementation landed; `docs/issue-2092/` does not exist in this checkout's tree at
HEAD. The tilde fix is **not** on main, and `contract-guard.sh:94-96` still holds the
unexpanded capture quoted in §3.

Consequence: this issue cannot assume the instance fix as an upstream. It must either
land the class fix such that #2092 becomes a no-op, or land alongside it and accept a
merge conflict on `contract-guard.sh`. The board is what is merged, and nothing is.

## 9. Exit-code semantics

canonical: read of docs/handbooks/hooks.md:1-9 and docs/handbooks/on-the-record.md:8-11

`docs/handbooks/hooks.md` states PreToolUse hooks "can deny it (exit 2) when they
positively determine a violation" and that "all of them fail open (exit 0) on environment
gaps". `docs/handbooks/on-the-record.md` records the one deliberate exception:
`deliverable-guard.sh` "fails closed (deny, exit 2) on stdin it cannot verify".

So the allowed-exit-code set the conformance test asserts against is `{0, 2}` per hook,
with the further requirement that no Traceback reaches stderr — and `deliverable-guard.sh`
needs an explicit exception because for it, `2` on garbage input is correct behaviour, not
a crash.

## Open unknowns handed to the proposal

- Ledger home: `runs/` (issue text) vs `~/.claude/on-the-record/` (only existing hook
  precedent). Must be decided, not left ambiguous.
- Whether the ~522-spawn conformance matrix runs as one slow-marked test or is split
  into a cheap fast-tier smoke plus a slow full matrix.
- How a hook that legitimately exits 2 on garbage (`deliverable-guard.sh`) is
  distinguished from one that crashed into a nonzero exit.
