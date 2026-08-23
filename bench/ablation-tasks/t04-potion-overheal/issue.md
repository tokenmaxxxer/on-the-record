## Task (t04-potion-overheal, quality-ablation arm A — issue #2130)

Drinking a potion can push the player's hp above max_hp (e.g. hp 35/30 shows up in fight logs). hp must never exceed max_hp — fix it and add a regression test.

## Acceptance
check: adjudicated against a hidden answer key by the operator after the run — the run is graded on delivered behavior, not on self-report.
empty state: the fixture as checked out.
provenance: executed-unit.
