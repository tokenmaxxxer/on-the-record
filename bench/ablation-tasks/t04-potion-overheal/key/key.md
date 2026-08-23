# Answer key — t04-potion-overheal (HIDDEN: never enters a run workspace)

Class: bugfix  ·  Fixture: harness/fixture-arcade

## Acceptance behaviors (one scoresheet row each)

- **a1** — After the fix, `Player.drink_potion()` never leaves hp > max_hp (seeded defect arcade-d1: `self.hp = self.hp + POTION_HEAL` with no clamp).
- **a2** — `fixture-arcade fight --seed 1 --battles 10` shows no hp/max_hp line where hp > max_hp.
- **a3** — A regression test exists that would fail on the unclamped code and passes now.
- **a4** — Healing below max still works (a potion at hp=10 raises hp; the fix is a clamp, not a no-op).

## Adjudication

Run the seed-1 gauntlet and grep the log. a4 guards against the lazy fix (disabling potions entirely).
