from decimal import Decimal

from app.models.enums import ExerciseIntensity
from app.services.exercise_calories import estimate_calories, metabolic_equivalent

WEIGHT = Decimal("80")


def test_a_known_activity_uses_its_own_value() -> None:
    assert metabolic_equivalent("Brooklyn Fitboxing") == Decimal("9.5")
    assert metabolic_equivalent("Sesión de FITBOXING") == Decimal("9.5")


def test_accents_do_not_hide_an_activity() -> None:
    assert metabolic_equivalent("Natación") == metabolic_equivalent("natacion")


def test_an_unknown_activity_falls_back_to_a_general_value() -> None:
    assert metabolic_equivalent("malabares con antorchas") == Decimal("6.0")


def test_a_fitboxing_session_is_estimated_from_weight_and_time() -> None:
    # 9.5 MET * 1.2 for high intensity * 80 kg * 47/60 h
    estimate = estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.HIGH, 47, WEIGHT)

    assert estimate == Decimal("714.40")


def test_intensity_moves_the_estimate() -> None:
    gentle = estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.LOW, 47, WEIGHT)
    hard = estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.VERY_HIGH, 47, WEIGHT)

    assert gentle is not None and hard is not None
    assert gentle < hard


def test_a_heavier_body_spends_more() -> None:
    lighter = estimate_calories("correr", ExerciseIntensity.MODERATE, 30, Decimal("60"))
    heavier = estimate_calories("correr", ExerciseIntensity.MODERATE, 30, Decimal("90"))

    assert lighter is not None and heavier is not None
    assert heavier > lighter


def test_without_a_weight_nothing_is_invented() -> None:
    assert estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.HIGH, 47, None) is None
    assert estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.HIGH, 47, Decimal("0")) is None


def test_a_session_of_no_length_spends_nothing() -> None:
    assert estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.HIGH, 0, WEIGHT) is None
