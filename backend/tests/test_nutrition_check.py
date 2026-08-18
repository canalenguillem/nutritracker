from decimal import Decimal

from app.services.nutrition_check import kcal_from_macros, macros_disagree


def test_energy_is_added_from_the_macronutrients() -> None:
    # 100 g protein and 70 g fat: 400 + 630.
    assert kcal_from_macros(Decimal("100"), Decimal("70"), Decimal("0")) == Decimal("1030")


def test_a_consistent_item_raises_nothing() -> None:
    assert not macros_disagree(Decimal("352"), Decimal("4"), Decimal("35"), Decimal("2"))


def test_the_beef_that_did_not_add_up_is_caught() -> None:
    """900 kcal stated, but the macronutrients describe 1030."""
    assert macros_disagree(Decimal("900"), Decimal("100"), Decimal("70"), Decimal("0"))


def test_rounding_on_a_small_item_is_not_a_contradiction() -> None:
    # Blueberries: 29 stated against 34 from the macronutrients.
    assert not macros_disagree(Decimal("29"), Decimal("0.40"), Decimal("0.30"), Decimal("7.30"))


def test_an_item_with_no_energy_at_all_is_fine() -> None:
    assert not macros_disagree(Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"))


def test_energy_without_any_macronutrients_is_a_contradiction() -> None:
    assert macros_disagree(Decimal("500"), Decimal("0"), Decimal("0"), Decimal("0"))


def test_macronutrients_without_any_energy_are_a_contradiction() -> None:
    assert macros_disagree(Decimal("0"), Decimal("30"), Decimal("20"), Decimal("10"))


def test_a_gap_within_the_tolerance_passes() -> None:
    # 1000 against 1050, which rounding and fibre can explain.
    assert not macros_disagree(Decimal("1000"), Decimal("100"), Decimal("30"), Decimal("95"))
