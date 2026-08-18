from decimal import Decimal

from app.models.enums import ExerciseIntensity
from app.services.exercise_calories import (
    estimate_calories,
    metabolic_equivalent,
    table_met,
)

WEIGHT = Decimal("80")


def test_a_known_activity_uses_its_own_value() -> None:
    assert metabolic_equivalent("Brooklyn Fitboxing") == Decimal("8.0")
    assert metabolic_equivalent("Sesión de FITBOXING") == Decimal("8.0")


def test_accents_do_not_hide_an_activity() -> None:
    assert metabolic_equivalent("Natación") == metabolic_equivalent("natacion")


def test_an_unknown_activity_falls_back_to_a_general_value() -> None:
    assert metabolic_equivalent("malabares con antorchas") == Decimal("6.0")


def test_a_fitboxing_session_is_estimated_from_weight_and_time() -> None:
    # 8.0 MET * 1.12 for a hard effort * 80 kg * 47/60 h
    estimate = estimate_calories("Brooklyn Fitboxing", ExerciseIntensity.HIGH, 47, WEIGHT)

    assert estimate == Decimal("561.49")


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


def test_a_word_ending_does_not_hide_an_activity() -> None:
    """Only the infinitive used to match, so a noun or a gerund was missed."""
    for name in ("caminar", "caminata", "caminando", "andando", "un paseo"):
        assert table_met(name) == Decimal("3.5"), name

    for name in ("boxeo", "boxeando", "Brooklyn fitboxing"):
        assert table_met(name) == Decimal("8.0"), name

    for name in ("correr", "corriendo", "una carrera"):
        assert table_met(name) == Decimal("9.8"), name


def test_a_stem_only_matches_the_start_of_a_word() -> None:
    # "recorrido" contains "corr" but is not running.
    assert table_met("recorrido en bici") == Decimal("7.5")


def test_walking_a_hill_is_not_walking_on_the_flat() -> None:
    flat = table_met("caminata")
    uphill = table_met("caminata en cuesta")

    assert flat == Decimal("3.5")
    assert uphill is not None and flat is not None
    # The Compendium puts an uphill walk between 5.3 and 8.0, against 3.5 level.
    assert Decimal("5.3") <= uphill <= Decimal("8.0")
    assert uphill > flat


def test_every_word_for_a_slope_is_understood() -> None:
    for slope in ("cuesta", "subida", "pendiente", "montaña", "colina"):
        assert table_met(f"caminata en {slope}") == Decimal("6.30"), slope


def test_a_slope_does_not_touch_activities_already_priced_high() -> None:
    # Running is near the top of its band already; the walking factor would
    # push it past competitive levels.
    assert table_met("correr en cuesta") == Decimal("9.8")
    assert table_met("bici en cuesta") == Decimal("7.5")


def test_hiking_is_its_own_activity() -> None:
    assert table_met("senderismo") == Decimal("6.0")
    assert table_met("trekking por el pirineo") == Decimal("6.0")


def test_a_hill_walk_is_estimated_above_a_flat_one() -> None:
    flat = estimate_calories("caminata", ExerciseIntensity.MODERATE, 40, WEIGHT)
    uphill = estimate_calories("caminata en cuesta", ExerciseIntensity.MODERATE, 40, WEIGHT)

    assert flat is not None and uphill is not None
    assert uphill > flat
