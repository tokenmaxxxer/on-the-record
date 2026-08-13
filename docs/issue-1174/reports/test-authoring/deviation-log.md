# Deviation log — test-authoring (issue #1174)

- 2026-08-13T00:00:00Z | inline | rulebook repo's board-gate.sh refused
  the fan-out brief's literal top-level `playbook/` landing path;
  relocated the operational-playbook file under that repo's
  docs/specs/ standing bucket instead to satisfy its own contract v3
  s10 layout gate. Stays inside that repo's frozen write surface
  (a new doctrine file), mechanical, one-off.
