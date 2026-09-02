# Reconciled spec index

Issue #336: several repos build against this engine's spec, but no
document lists or hashes the others, so contradictions between
documents survive indefinitely. This file is the single reconciled
reading — every spec-shaped document, its recorded content hash, and
(below) the ambiguities already found and resolved.

`gates/spec_index.py` recomputes each listed file's SHA256 and fails
when it no longer matches what's recorded here. Regenerate with
`python3 gates/spec_index.py --update` after reading what changed and
updating "Resolved ambiguities" if the edit touches a resolved point.

## Tracked documents

| path | sha256 |
| --- | --- |
| `protocol.md` | `84addaa507f829b4b9a061dd1c9b5059b087e4e3bcdb1353860de06398d4717d` |
| `protocol.ko.md` | `03ba195003285a20d0d1d7df5d914ef68f122672d39a7dba042fb5f6c184433a` |
| `README.md` | `25119c5757b032335d8dc73bf53e7555a668552081c9a9e77ab3998fd4ce736c` |
| `README.ko.md` | `dcf2c9d28a6c1058eb0950a5fc0a15c2883d95da081d65e0531cdac168873f16` |
| `docs/specs/approvers.md` | `bbcb4e239a5aed872956a01acc04c9431027a1f2df483b53265f72577ba16ab9` |
| `docs/specs/flows-schema.md` | `78440f72845e44c8ed5eb6814890bff5a325d1736633365d78f8d7ceb061adbb` |
| `docs/handbooks/on-the-record.md` | `9e314a347f6265950b2eedc791891e329255ee4adf9f6b5ffab5554f2e6e20f1` |
| `docs/handbooks/operations.md` | `18a65866836764534c590c42af826ca160f253ae2696867bdaf8871d3e893845` |
| `docs/handbooks/setup.md` | `8f957a3de4594602e03d76c87988927abb453fab16516bdd557f0be064639cc6` |
| `on-the-record/commands/run.md` | `e48a0aface754bb683cfec0457c08c04cb56934a4576b0dc46fca7c63fd1bfed` |
| `roles/specs/brand-design.spec.json` | `a3458deaf40cb03f286d68ec250d66e6cd9e0d8ec269ea5a59d8d72fed7ea824` |
| `roles/specs/content-design.spec.json` | `923c4c55d5b48c4289f4939f8eb1675b64e9866db0b6e3fc12298277cd349346` |
| `roles/specs/market-analysis.spec.json` | `13ee9b2a855beacb0b25316d969a2c8b3dc14c4c373fb9dbebe0880878ccba77` |

## Resolved ambiguities

- **Ledger storage location.** Canonical storage is `runs/ledger.jsonl`
  (per `docs/handbooks/operations.md:159,405`,
  `docs/specs/flows-schema.md:243-252`, and
  `on-the-record/commands/run.md:677`, all of which agree).
  `ledger/collect.py` (repo-root script) is an aggregator that *reads*
  `runs/ledger.jsonl` — it is not itself the storage location.
  `docs/handbooks/on-the-record.md`'s architecture diagram previously
  labeled `ledger/` as "the scorecard" without naming it as an
  aggregator, which read as if `ledger/` were the storage; corrected in
  this change (both the Korean and English diagram lines) to name it as
  the aggregator over `runs/ledger.jsonl`. `protocol.md` does not
  mention the ledger at all and is not in contradiction with the above —
  it is simply silent on this topic.
