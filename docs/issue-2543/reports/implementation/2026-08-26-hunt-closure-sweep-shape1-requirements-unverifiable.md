---
proposal: docs/issue-2543 (issue #2543 fix: closure_sweep shape1 fail-vs-zero + requirements.md UNVERIFIABLE conversion)
---

# Hunt record — closure-sweep-shape1-requirements-unverifiable

## after-proposal — stance 1: silent-failure / composition-regression in the #2543 diff (closure_sweep.py, gates.py, board.py, requirements.md)

Verdict: NO FINDING
Seed: git diff 480d1a78..e380f7f7 -- gates/closure_sweep.py gates/gates.py board.py docs/specs/requirements.md
cap_seconds: not specified by dispatcher
tier: default
diff_stat_lines: ~90 (4 files)
started_at: 2026-08-26T11:05:00Z
ended_at: 2026-08-26T11:45:00Z

Checked all four hinted angles, each with a live repro, all clean:

1. `prior.get("shape1_sites", 0)` against an OLD-format state file containing
   a stale `shape5_files` key: wrote `{"shape1_sites": 42, "shape5_files": 87}`
   to `runs/accumulation_trend.json` and called `accumulation_trend(Path("."))`
   — produced `delta: {"shape1_sites": 323}` correctly, no KeyError, old key
   silently ignored as intended.

2. `board.gate_report()`'s new `gates.requirement_registry_unverifiable_summary()`
   call: confirmed by reading `board.py:832-841` that the call sits *inside*
   the existing `try: ... except Exception as e: return [...]` block (between
   `bad = ci.check(...)` and the `except`), so any exception it raises (e.g.
   malformed `requirements.md`) is already caught by the pre-existing handler.
   No new uncaught path.

3. Grepped for `shape5` and for any reader of `_current_accumulation_counts()`'s
   dict shape across `.py`/`.sh`/`.md` (excluding the `on-the-record/`
   packaged-copy tree): only `gates/closure_sweep.py` itself (docstring
   comments) and `watchdog.py` (which only prints via
   `format_accumulation_trend()`) reference it. No stale reader.

4. Checked whether anything besides `gates/ci.py` calls `gates.requirement_registry()`:
   only `gates/ci.py:631` and the `ALL` dict registration (`gates/gates.py:1310`,
   which `ci.py` iterates through — same call). Ran
   `gates.requirement_registry(Path("."), {})` live against the real,
   already-updated `docs/specs/requirements.md` — returns `bad == []` (the 3
   UNVERIFIABLE entries correctly produce no "요구사항 체크 소실" entries),
   and `requirement_digest.py`'s own `check()` (which independently re-derives
   staleness from the same `UNVERIFIABLE:` prefix) also passes clean
   (`통과: ... 일치한다`), confirming no divergent consumer.

Also chased one path outside the four hints: the repo ships a packaged plugin
copy at `on-the-record/` (per `.claude-plugin/marketplace.json`'s
`"source": "./on-the-record"`), and a prior commit (d750dbf5, issue #2295)
established a convention of syncing `gates/gates.py` into
`on-the-record/gates/gates.py` in the same commit, enforced by a now-deleted
regression test (`on-the-record/hooks/test_hook_cache_layout.py`, removed by
a555e169 issue #2525's blanket test-suite retirement, itself well before
e380f7f7). `e380f7f7` indeed left `on-the-record/gates/gates.py` unsynced
(missing `requirement_registry_unverifiable_summary` and the new docstring),
unlike 480d1a78 which synced both copies in one commit. However this produces
no reproducible wrong *output*: `board.gate_report()` (the only caller of the
new function) imports gates via `sys.path.insert(0, _sp.ROOT / "gates")` where
`_sp.ROOT = Path(spawn.py).resolve().parent` — the dev-tree root, not the
packaged copy — so it always resolves the up-to-date root `gates/gates.py`
regardless of packaged-copy staleness. `requirement_registry()`'s own
behavior (the function real hook sessions load from the packaged copy) was
not changed by this diff at all — only a docstring and a brand-new,
board.py-only function were added. So the drift exists textually but has no
live behavioral divergence to reproduce; declining to report it per the
no-reproduction rule.
