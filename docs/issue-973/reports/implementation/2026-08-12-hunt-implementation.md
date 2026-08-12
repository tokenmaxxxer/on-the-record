---
proposal: docs/issue-973/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 4: assume the frozen write set cannot carry the work — find the path the build will need that the proposal does not list

Verdict: FINDING — write set for the new harness fixture omits `harness/fixture-concurrent-judgment/pyproject.toml`, which every sibling fixture has and the harness's own documented convention (`pip install -e harness/fixture-<name>`, harness/README.md:35) requires to make the package importable/installable; without it `pip install -e harness/fixture-concurrent-judgment` fails outright.
Kind: design-error
Seed: git show 021320b --stat (docs/issue-973/proposals/implementation.md, docs/issue-973/reports/implementation/survey.md)
cap_seconds: 120
tier: default
diff_stat_lines: ~237 (docs-only)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:15:00Z

### Reproduce
```
ls harness/fixture-multirole/    # has pyproject.toml (canonical sibling, cited as pattern by this proposal)
ls harness/fixture-target/       # also has pyproject.toml; harness/README.md:35 documents `pip install -e harness/fixture-target`
# frozen write set for the new fixture:
#   harness/fixture-concurrent-judgment/fixture_concurrent_judgment/__init__.py
#   harness/fixture-concurrent-judgment/test_panel.py
# no pyproject.toml listed. Reproduce the resulting failure with an equivalent minimal layout:
mkdir -p /tmp/fake-fixture/fixture_concurrent_judgment
touch /tmp/fake-fixture/fixture_concurrent_judgment/__init__.py
printf 'from fixture_concurrent_judgment import x\n' > /tmp/fake-fixture/test_panel.py
pip install -e /tmp/fake-fixture
```

### Observed
```
ERROR: file:///tmp/fake-fixture does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.
```

### Expected
The proposal's "What will be done" step 4 promises a fixture package matching "the existing harness
pattern of `fixture_<name>/` package + `test_fixture_<name>.py`" (its own rationale section, citing
`fixture-multirole` as canonical) and following the harness's documented install path
(`harness/README.md:35`, `pip install -e harness/fixture-<name>`). Both canonical siblings
(`fixture-multirole`, `fixture-target`) ship a `pyproject.toml` declaring the package name/version so
`pip install -e` succeeds. The frozen write set names only the package `__init__.py` and the test
file — no `pyproject.toml` path — so a build following the write set literally produces an
uninstallable fixture package, unless pytest's own rootdir-sys.path insertion happens to make the
bare `import fixture_concurrent_judgment` resolve without install (which the existing siblings do not
rely on — they are pip-installed, per `pip show fixture-multirole` showing an editable install).

## before-landing — stance 1: assume this change and another plugin's rule cancel each other out — find the pair

Verdict: NO FINDING
Seed: spawn.py panel_cmd()/_run_panel_session()/_panel_degrade()/_PanelMessagingUnavailable (~186 new lines, spawn.py:4166-4352), harness/fixture-concurrent-judgment/
cap_seconds: 180
tier: default
diff_stat_lines: 277 (186 spawn.py + 91 fixture)
started_at: 2026-08-12T11:54:58+09:00
ended_at: 2026-08-12T11:58:30+09:00

Avenues checked, none reproduced a collision:

canonical: spawn.py:476-620 (role_settings(), read this turn) — no line removes or overwrites an
unknown top-level settings key; `_run_panel_session()` sets `s["crossSessionInbound"] = "accept"`
after `role_settings()` returns (spawn.py:4237-4238), so nothing downstream strips it back out.

canonical: spawn.py:4097-4168 (consult_cmd(), read this turn) — no `roster_register()` call in this
function either, so panel_cmd()'s two threads not touching `ROSTER`/`runs/active.json` matches the
sibling function's existing behavior, not a new gap introduced by this diff.

canonical: spawn.py:237-256 (`_locked_rulebook_dir()`, read this turn) — uses `fcntl.flock` per
marketplace-dir lock file, which is the concurrency-safety mechanism that would already absorb two
`plugin_dirs()` calls racing on the same marketplace from panel_cmd()'s two threads.

canonical: on-the-record/hooks/delegated-judgment-gate.sh (read this turn) — its "panel" concept
(`panel-unanimous-support-v1`) triggers on gh PR-lifecycle events; panel_cmd()'s spawned session
prompt (spawn.py:4258-4260) explicitly forbids branching/committing/opening a PR, so that gate's
trigger condition is never reached from inside a panel session.

```
$ grep -n "WATCHDOG_SILENCE_MIN\s*=\|WATCHDOG_NO_COMMIT_MIN\s*=\|PANEL_TIMEOUT\s*=" spawn.py
2007:WATCHDOG_SILENCE_MIN = 90     # signal 1
2008:WATCHDOG_NO_COMMIT_MIN = 71   # signal 4
67:PANEL_TIMEOUT = 240    # panel: two judges + a rebuttal round, wider than a single consult
```
`WATCHDOG_SILENCE_MIN`/`WATCHDOG_NO_COMMIT_MIN` are minute-scale watchdog thresholds while
`PANEL_TIMEOUT` is a second-scale `subprocess.run(timeout=...)` bound — different units, no shared
resource, no interaction found.

canonical: on-the-record/hooks/spawn-allow-gate.sh (read this turn) — keys its allow decision on
orchestrator identity (CLAUDE_ROLE empty) plus Bash-command shape (`python3 spawn.py ...`); it
governs the orchestrator's own Bash-tool invocation of spawn.py, not anything the `claude -p`
subprocesses panel_cmd() spawns do internally (they never themselves shell out to spawn.py).

Could not find, within the time budget, a rule that panel_cmd() silently violates, bypasses, or that
cancels its effect. Stopping rather than reporting a plausible-but-unreproduced concern.
