from datetime import date
from decimal import Decimal

from app.services.energy import age_on, energy_balance, resting_energy

TODAY = date(2026, 8, 18)


def test_age_waits_for_the_birthday() -> None:
    assert age_on(date(1974, 9, 11), TODAY) == 51
    assert age_on(date(1974, 8, 18), TODAY) == 52
    assert age_on(date(1974, 8, 19), TODAY) == 51


def test_resting_energy_follows_mifflin_st_jeor() -> None:
    # 10*105.4 + 6.25*174 - 5*51 + 5
    assert resting_energy(Decimal("105.40"), Decimal("174"), 51, "male") == Decimal("1892")


def test_a_woman_of_the_same_size_rests_lower() -> None:
    male = resting_energy(Decimal("70"), Decimal("170"), 40, "male")
    female = resting_energy(Decimal("70"), Decimal("170"), 40, "female")

    assert female < male
    assert male - female == Decimal("166")


def test_an_unstated_sex_lands_between_the_two() -> None:
    male = resting_energy(Decimal("70"), Decimal("170"), 40, "male")
    female = resting_energy(Decimal("70"), Decimal("170"), 40, "female")
    unstated = resting_energy(Decimal("70"), Decimal("170"), 40, None)

    assert female < unstated < male


def test_the_balance_counts_resting_living_and_training() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("1435.00"),
        exercise_kcal=Decimal("1059.00"),
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.status == "estimated"
    assert balance.resting_kcal == Decimal("1892")
    # 1892 * 1.35 for daily living, then the training on top.
    assert balance.living_kcal == Decimal("2554")
    assert balance.total_expenditure_kcal == Decimal("3613")
    assert balance.balance_kcal == Decimal("-2178")


def test_training_is_not_counted_twice() -> None:
    """The living factor must exclude workouts, which are added separately."""
    without_training = energy_balance(
        consumed_kcal=Decimal("2000"),
        exercise_kcal=Decimal("0"),
        weight_kg=Decimal("80"),
        height_cm=Decimal("178"),
        birth_date=date(1990, 1, 1),
        biological_sex="male",
        activity_level="very_active",
        today=TODAY,
    )

    assert without_training.living_kcal is not None
    assert without_training.resting_kcal is not None
    # Even at the top setting, living stays well under the textbook 1.9 factor
    # that would already include training.
    assert without_training.living_kcal < without_training.resting_kcal * Decimal("1.6")


def test_eating_more_than_spent_is_a_surplus() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("4000"),
        exercise_kcal=Decimal("0"),
        weight_kg=Decimal("70"),
        height_cm=Decimal("170"),
        birth_date=date(1990, 1, 1),
        biological_sex="female",
        activity_level="sedentary",
        today=TODAY,
    )

    assert balance.balance_kcal is not None
    assert balance.balance_kcal > Decimal("0")


def test_a_missing_height_leaves_the_balance_unanswered() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("1435"),
        exercise_kcal=Decimal("1059"),
        weight_kg=Decimal("105.40"),
        height_cm=None,
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.status == "needs_profile"
    assert balance.balance_kcal is None
    # What is known is still reported.
    assert balance.consumed_kcal == Decimal("1435")
    assert balance.exercise_kcal == Decimal("1059")


def test_a_missing_birth_date_leaves_the_balance_unanswered() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("1435"),
        exercise_kcal=Decimal("0"),
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174"),
        birth_date=None,
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.status == "needs_profile"


def test_an_unknown_activity_level_falls_back() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("2000"),
        exercise_kcal=Decimal("0"),
        weight_kg=Decimal("80"),
        height_cm=Decimal("178"),
        birth_date=date(1990, 1, 1),
        biological_sex="male",
        activity_level="astronaut",
        today=TODAY,
    )

    assert balance.status == "estimated"
    assert balance.living_kcal is not None
