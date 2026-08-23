# Deviation log — issue-2070 / implementation

- 2026-08-23T00:00:00Z, inline, proposal's frozen write set didn't list
  `tests/test_spawn_pipeline.py`, `test/test_spawn_artifact_skill_pairing.py`,
  `test/test_spawn_cross_family_skill_selection.py` — the shipped routing
  policy's `default_tier` (opus) intentionally changed `spawn_cmd()`'s
  terminal default away from the old flat `"sonnet"` (exactly the gap this
  issue asks routing to fill), which broke five `execution-observation`
  "builtin default" assertions in `test_spawn_pipeline.py` plus two
  `spy_spawn_cmd` stubs in the other two files that had a fixed positional
  signature and choked on the new `single_phase`/`design_bearing_verdict`
  kwargs. Updated the five assertions to the new intended default and
  widened the two stub signatures with `**kwargs` — mechanical, no
  design judgment, required to keep the fast tier green per this issue's
  own acceptance text. spawn.py:5568-5620 / spawn.py:8590-8636.
