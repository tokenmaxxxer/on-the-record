"""fixture-arcade — a tiny deterministic dice-battle RPG CLI.

Self-contained (stdlib only). The player fights a sequence of monsters,
gains XP, levels up, and can drink potions between battles. Combat is
seeded-deterministic so every behavior is checkable without flakiness.

Commands:
  fixture-arcade fight --seed N [--battles K]   run K battles, print a log
  fixture-arcade stats                          print the balance table
"""
import argparse
import random

__version__ = "0.1.0"

# --- balance parameters -------------------------------------------------
BASE_HP = 30
BASE_ATTACK = 6
POTION_HEAL = 12
MONSTER_HP = 14
MONSTER_ATTACK = 4
XP_PER_WIN = 10
# XP required to reach each level (index 0 = level 2 threshold, etc.).
# Balance surface: derivation tasks retune this curve.
XP_CURVE = [10, 25, 45, 70, 100]
CRIT_CHANCE = 0.15
CRIT_MULTIPLIER = 2


class Player:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.max_hp = BASE_HP
        self.hp = BASE_HP
        self.attack = BASE_ATTACK

    def gain_xp(self, amount):
        self.xp += amount
        while self.level - 1 < len(XP_CURVE) and self.xp >= XP_CURVE[self.level - 1]:
            self.level += 1
            self.max_hp += 5
            self.attack += 2

    def drink_potion(self):
        # Seeded defect (arcade-d1): heals past max_hp — no clamp.
        self.hp = self.hp + POTION_HEAL


class Monster:
    def __init__(self, level):
        self.hp = MONSTER_HP + 3 * (level - 1)
        self.attack = MONSTER_ATTACK + (level - 1)


def roll_damage(rng, attack):
    dmg = attack + rng.randint(0, 3)
    if rng.random() < CRIT_CHANCE:
        # Seeded defect (arcade-d2): crit multiplies the random bonus
        # only, not the whole damage roll — crits are nearly worthless.
        dmg = attack + (dmg - attack) * CRIT_MULTIPLIER
    return dmg


def run_battle(player, monster, rng):
    """One battle to the death. Returns True when the player wins."""
    while True:
        monster.hp -= roll_damage(rng, player.attack)
        if monster.hp <= 0:
            player.gain_xp(XP_PER_WIN)
            return True
        player.hp -= roll_damage(rng, monster.attack)
        if player.hp <= 0:
            return False


def run_gauntlet(seed, battles):
    rng = random.Random(seed)
    player = Player()
    log = []
    for i in range(1, battles + 1):
        won = run_battle(player, Monster(player.level), rng)
        log.append(
            f"battle {i}: {'WIN' if won else 'LOSS'}  "
            f"level={player.level} xp={player.xp} hp={player.hp}/{player.max_hp}"
        )
        if not won:
            break
        if player.hp < player.max_hp // 2:
            player.drink_potion()
            log.append(f"  potion: hp={player.hp}/{player.max_hp}")
    return player, log


def _build_parser():
    parser = argparse.ArgumentParser(prog="fixture-arcade")
    sub = parser.add_subparsers(dest="command")
    fight = sub.add_parser("fight")
    fight.add_argument("--seed", type=int, default=1)
    fight.add_argument("--battles", type=int, default=10)
    sub.add_parser("stats")
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "fight":
        player, log = run_gauntlet(args.seed, args.battles)
        for line in log:
            print(line)
        print(f"final: level={player.level} xp={player.xp} hp={player.hp}/{player.max_hp}")
        return
    if args.command == "stats":
        print(f"base_hp={BASE_HP} base_attack={BASE_ATTACK} potion_heal={POTION_HEAL}")
        print(f"monster_hp={MONSTER_HP} monster_attack={MONSTER_ATTACK}")
        print(f"xp_per_win={XP_PER_WIN} xp_curve={XP_CURVE}")
        print(f"crit_chance={CRIT_CHANCE} crit_multiplier={CRIT_MULTIPLIER}")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
