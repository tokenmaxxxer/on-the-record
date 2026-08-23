import random

from arcade import Monster, Player, run_battle


def test_player_starts_at_level_one():
    p = Player()
    assert p.level == 1
    assert p.hp == p.max_hp


def test_gain_xp_levels_up():
    p = Player()
    p.gain_xp(10)
    assert p.level == 2


def test_battle_is_deterministic_for_a_seed():
    rng = random.Random(7)
    p = Player()
    won = run_battle(p, Monster(1), rng)
    assert isinstance(won, bool)
