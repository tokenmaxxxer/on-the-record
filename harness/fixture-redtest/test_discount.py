from fixture_redtest.discount import bulk_discount


def test_bulk_discount_applies():
    # 10 units at $10 each, 10% bulk discount at quantity >= 10 -> $90.00
    assert bulk_discount(10.0, 10) == 90.0
