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
