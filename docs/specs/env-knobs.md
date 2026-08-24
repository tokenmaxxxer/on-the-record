---
name: env-knobs
description: >
  Operator-facing environment knobs read by the engine but previously
  documented nowhere (#2141 item, from the #2139 B6 evidence row). One
  row per knob: read site, default, effect. This table exists so a knob
  is discoverable before someone re-invents it or grep-hunts the reader.
---

# Environment knobs

Knobs already documented elsewhere (`MUSTER_STATE_ROOT`,
`MUSTER_SETTING_SOURCES`, `ORCHESTRATE_OFF`, `TOKENMAXXXER_CHECKOUT`,
`MONITOR_LIVENESS_STALE_SECONDS`, ...) are not repeated here — this
table covers the previously undocumented set from the #2139 sweep.

| knob | read at | default | effect |
|---|---|---|---|
| `TOKENMAXXXER_PANEL_MESSAGING` | consult.py:1065 | unset | `unavailable` makes panel messaging raise `_PanelMessagingUnavailable` for every role — test/degradation switch for the panel path |
| `SPAWN_WATCHDOG_ALLOW_NONCANONICAL` | watchdog.py:1086 | unset | `1` lets `spawn.py watchdog` run from a non-canonical checkout instead of refusing (the refusal protects the single-watchdog rearm contract) |
| `SKILL_JUDGE_TIMEOUT` | consult.py:60 | `90` (s, `SKILL_JUDGE_TIMEOUT_DEFAULT`) | per-call timeout for the skill_judge haiku call; non-numeric values fall back to the default |
| `OTR_LEASE_TTL_MIN` | spawn.py:842 | `90` (min) | lease TTL for an in-progress board claim (#2101 mechanism 1); an expired lease on a dead entry is requeued by the reconcile sweep |
| `OTR_EVIDENCE_CHECK` | consult.py:102 | `1` (on) | `0`/`false`/`off` disables the consult-trace evidence summary annotation |
| `OTR_DEADMAN_INTERVAL_SEC` | spawn.py:844 | `120` (s) | expected watchdog/monitor tick cadence — one unit of the dead-man staleness budget (#2101 mechanism 4) |
| `OTR_DEADMAN_STALE_INTERVALS` | spawn.py:845 | `5` | tick intervals without a coverage-OK marker before `spawn.py deadman-check` prints the DEAD advisory (default threshold 5 x 120s = 600s) |
| `MUSTER_RULEBOOK_TTL` | pipeline.py:63 | `15` (min) | freshness TTL for managed clone pulls (core/skill-repo); `0` = pull every time. Legacy name kept — renaming churns installed checkouts (#2139 cosmetic row) |
| `BOARD_READ_FULL_EVERY` | gates/board_read.py:276 | `20` | every Nth board sweep forces a full re-read instead of the ETag delta path |
| `BOARD_READ_FORCE_FULL` | gates/board_read.py:273 | unset | `1` forces a full board re-read on this sweep (bypasses delta/ETag) |
| `CHECKPOINT_POLL_SECONDS` | pipeline.py:1187 | `60` (s) | poll interval of the checkpoint-mode `spawn.py await-approval` wait (#2129) |
| `CHECKPOINT_WAIT_MAX_SECONDS` | pipeline.py:1195 | `1800` (s) | max wall-clock the checkpoint await-approval wait holds before timing out to the two-session path |

Disposition: all twelve are live (grep-verified read sites, 2026-08-24) —
document, not drop. `MUSTER_RULEBOOK_TTL` is the only legacy-named one;
it stays under keep-with-reason (rename churn) per the #2139 cosmetic
rows.
