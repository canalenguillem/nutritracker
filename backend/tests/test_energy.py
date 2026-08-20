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
        exercise_kcal=Decimal("805.82"),
        exercise_minutes=47,
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.status == "estimated"
    assert balance.resting_kcal == Decimal("1892")
    # 1892 * 1.40 for a day spent in movement.
    assert balance.living_kcal == Decimal("2649")
    # The session cost 806, of which 62 was resting that living already counts.
    assert balance.exercise_above_resting_kcal == Decimal("744")
    assert balance.total_expenditure_kcal == Decimal("3393")
    assert balance.balance_kcal == Decimal("-1958")


def test_resting_is_not_counted_twice_during_training() -> None:
    """A session priced at exactly resting adds nothing to the day."""
    resting_only = energy_balance(
        consumed_kcal=Decimal("2000"),
        # An hour at a metabolic equivalent of 1 is resting, not exercise.
        exercise_kcal=(Decimal("1892") / Decimal("24")).quantize(Decimal("0.01")),
        exercise_minutes=60,
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert resting_only.exercise_above_resting_kcal == Decimal("0")
    assert resting_only.total_expenditure_kcal == resting_only.living_kcal


def test_a_session_cheaper_than_resting_never_goes_negative() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("2000"),
        exercise_kcal=Decimal("5.00"),
        exercise_minutes=120,
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.exercise_above_resting_kcal == Decimal("0")


def test_training_is_not_counted_twice() -> None:
    """The living factor must exclude workouts, which are added separately."""
    without_training = energy_balance(
        consumed_kcal=Decimal("2000"),
        exercise_kcal=Decimal("0"),
        exercise_minutes=0,
        weight_kg=Decimal("80"),
        height_cm=Decimal("178"),
        birth_date=date(1990, 1, 1),
        biological_sex="male",
        activity_level="very_active",
        today=TODAY,
    )

    assert without_training.living_kcal is not None
    assert without_training.resting_kcal is not None
    # Even at the top setting, living stays under the textbook multipliers for a
    # training week (1.725 and 1.9), which would already contain the sessions.
    assert without_training.living_kcal < without_training.resting_kcal * Decimal("1.7")


def test_eating_more_than_spent_is_a_surplus() -> None:
    balance = energy_balance(
        consumed_kcal=Decimal("4000"),
        exercise_kcal=Decimal("0"),
        exercise_minutes=0,
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
        exercise_minutes=47,
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
        exercise_minutes=0,
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
        exercise_minutes=0,
        weight_kg=Decimal("80"),
        height_cm=Decimal("178"),
        birth_date=date(1990, 1, 1),
        biological_sex="male",
        activity_level="astronaut",
        today=TODAY,
    )

    assert balance.status == "estimated"
    assert balance.living_kcal is not None


def test_a_sedentary_day_matches_the_textbook_no_exercise_factor() -> None:
    """1.2 is what the textbooks apply to someone who does not train."""
    balance = energy_balance(
        consumed_kcal=Decimal("1435.00"),
        exercise_kcal=Decimal("739.77"),
        exercise_minutes=47,
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="sedentary",
        today=TODAY,
    )

    assert balance.resting_kcal == Decimal("1892")
    assert balance.living_kcal == Decimal("2270")
    assert balance.exercise_above_resting_kcal == Decimal("678")
    assert balance.total_expenditure_kcal == Decimal("2948")
    assert balance.balance_kcal == Decimal("-1513")


def test_sitting_all_day_spends_less_than_moving_all_day() -> None:
    def spend(activity_level: str) -> Decimal:
        balance = energy_balance(
            consumed_kcal=Decimal("2000"),
            exercise_kcal=Decimal("0"),
            exercise_minutes=0,
            weight_kg=Decimal("105.40"),
            height_cm=Decimal("174.00"),
            birth_date=date(1974, 9, 11),
            biological_sex="male",
            activity_level=activity_level,
            today=TODAY,
        )
        assert balance.living_kcal is not None
        return balance.living_kcal

    assert spend("sedentary") < spend("light") < spend("moderate") < spend("active")


def test_the_total_is_daily_living_plus_training_and_nothing_else() -> None:
    """Resting must not be added on its own: daily living already contains it.

    The interface shows resting as a figure, which invites reading the column as
    a sum of every line. It is not, and this pins the arithmetic down.
    """
    balance = energy_balance(
        consumed_kcal=Decimal("1435.00"),
        exercise_kcal=Decimal("1360.00"),
        exercise_minutes=97,
        weight_kg=Decimal("105.40"),
        height_cm=Decimal("174.00"),
        birth_date=date(1974, 9, 11),
        biological_sex="male",
        activity_level="moderate",
        today=TODAY,
    )

    assert balance.living_kcal is not None
    assert balance.exercise_above_resting_kcal is not None
    assert balance.resting_kcal is not None

    assert balance.total_expenditure_kcal == (
        balance.living_kcal + balance.exercise_above_resting_kcal
    )
    # And emphatically not the sum that counts the basal rate twice.
    assert balance.total_expenditure_kcal != (
        balance.resting_kcal + balance.living_kcal + balance.exercise_above_resting_kcal
    )
    assert balance.balance_kcal == Decimal("1435") - balance.total_expenditure_kcal
