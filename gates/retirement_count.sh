#!/usr/bin/env bash
# Retirement invariant check: fails (non-zero exit) if the retired `role`
# axis reappears anywhere in this repo's py/sh sources (docs/ excluded).
# See gates/retirement_count.py for what population this covers and why
# a plain `grep -rn '\brole\b'` cannot see it.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
exec python3 gates/retirement_count.py
