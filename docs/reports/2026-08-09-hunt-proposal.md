---
proposal: docs/issue-551/proposals/proposal.md
---

# Hunt record — issue-551-test-env-resolution

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-551/proposals/proposal.md (frozen files: docs/specs/test-env-resolution.md, gates/test_env_resolve.py, gates/test_test_env_resolve.py); diff `git show f75533b` (2 new files, docs-only, ~237 lines)
cap_seconds: 120
tier: default
diff_stat_lines: ~237 (docs-only diff; proposal commits to code files not yet written)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:15:00Z

Checked candidates for a missing required path: (1) `python3 -m gates.test_env_resolve` needing a `gates/__init__.py` — verified empirically that `python3 -m gates.skip_gate` already works today without one (PEP 420 namespace package, Python 3.10.12), so the same invocation style for the new module needs nothing extra. (2) `docs/specs/reconciled-index.md` claims to track "every spec-shaped document," which would imply the new `docs/specs/test-env-resolution.md` needs a matching entry not in the write set — but `gates/spec_index.py::check` only validates hashes for documents *already listed* in the index; it does not require new `docs/specs/*.md` files to be added, and in fact 8 of 11 existing `docs/specs/*.md`/`.json` files (enforcement-boundary.md, impact-classification.md, parallel-conflict-methodology.md, platform-capabilities.md, requirements.md, role-spec-template.schema.json, standing-decisions.md, survey-conventions.md) are already untracked today, so this is pre-existing, unenforced drift rather than a build-breaking omission caused by this proposal. (3) `docs/specs/requirements.md`'s registry is append-only per-requirement but `gates/gates.py::requirement_registry` only fails on `check:` paths going stale, not on missing new entries — not a hard dependency. (4) No CI workflow file, gate-test enumeration script, or `__init__.py`/conftest.py exists that whitelists specific gate test filenames, so pytest auto-discovers `gates/test_test_env_resolve.py` with no extra registration file needed. (5) `hooks/lib/gate-lib.sh`, the marker file `resolve_core` checks for, does not need to exist in this repo (it's a check against caller-supplied candidate paths / env var, exercised via tmpdir fixtures in unit tests, not a real dependency).

No reproduction of a genuinely missing build-required path was found within the cap; the three-file write set appears sufficient for what the proposal commits to deliver.
