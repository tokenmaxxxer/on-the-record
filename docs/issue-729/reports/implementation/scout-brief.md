# Scout brief (issue #729) — test directory layout

Mode: parallel WebSearch, 2 angles in one batch, 1 sweep stage. Stopped
after judge point 1 — findings directly answered the open decisions with
no disagreement across sources, so no deepening round was needed.

## Must-bes (pytest ecosystem)

- A single `tests/` directory is the documented pytest convention, not
  `test/` — pytest's own good-practices doc and community guides both
  use `tests/`.
- `conftest.py` fixture scope follows directory ancestry: a top-level
  conftest.py's fixtures apply to "siblings and descendants" — every
  test file anywhere under the repo, regardless of which subdirectory
  holds the file itself. A subdirectory can add its own conftest.py for
  fixtures local to that subtree, without losing the top-level ones.

## Performance axes

- **Discoverability**: does a new contributor find the right home
  without asking? Central `tests/` wins for "no obvious owning module"
  suites; colocation wins for suites bound to one implementation file.
- **Fixture reach**: root conftest.py's env-default injection (#204) and
  session-leak check (#360) must reach every file, wherever it lives —
  this is an ancestry property, not a "same folder" property.

## Adopt / skip

- Adopt: name the unified home `tests/` (plural) — matches ecosystem
  convention and the fixtures subtree (`tests/fixtures/`) already
  anchored there by #204.
- Adopt: colocation for suites bound to one implementation module in its
  own subsystem directory (`gates/`, `on-the-record/hooks/`) — a
  recognized, legitimate pattern, not an accident to correct.
- Skip: moving `conftest.py` out of root — would silently narrow its
  fixture reach to only its new subtree, breaking #204/#360 for every
  file outside that subtree. Nothing in the sources recommends this;
  the ecosystem convention is the opposite (root conftest.py for
  repo-wide fixtures).

## Gap line

Current state already matches the "central home for no-obvious-owner
suites" must-be in spirit (a `test/` and `tests/` both exist) but splits
it across two differently-named, non-semantically-distinct directories —
the gap is naming/consolidation, not the presence of a wrong pattern.
Colocation for `gates/`/`on-the-record/hooks/` already matches the
must-be exactly — no gap there.

Sources:
- [Good Integration Practices - pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [5 Best Practices For Organizing Tests (Simple And Scalable) | Pytest with Eric](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/)
- [pytest import mechanisms and sys.path/PYTHONPATH - pytest documentation](https://docs.pytest.org/en/stable/explanation/pythonpath.html)
- [Colocation of Tests: A Cross-Language Perspective | by Mario Dias | Medium](https://itsmariodias.medium.com/colocation-of-tests-a-cross-language-perspective-982e75c872d8)
- [Should you colocate your tests? A proof-of-concept - Janmeppe.com](https://www.janmeppe.com/blog/should-you-colocate-your-tests-a-proof-of-concept/)
