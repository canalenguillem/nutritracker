from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

ZERO_PLACES = Decimal("1")

# Mifflin-St Jeor, the estimate most used for resting expenditure.
WEIGHT_FACTOR = Decimal("10")
HEIGHT_FACTOR = Decimal("6.25")
AGE_FACTOR = Decimal("5")
MALE_OFFSET = Decimal("5")
FEMALE_OFFSET = Decimal("-161")
# Without a sex the formula has no offset to use, so take the midpoint and say
# the estimate is rougher for it.
UNSPECIFIED_OFFSET = (MALE_OFFSET + FEMALE_OFFSET) / Decimal("2")

# What daily living costs on top of resting, NOT counting workouts: those are
# recorded one by one and added separately. Using a textbook activity factor
# here would count the same training session twice.
# Sedentary is the 1.2 the textbooks use for someone who does not train, which
# is exactly what this factor should describe. The tiers above it are physically
# demanding days, not training weeks: training is added on top.
LIVING_FACTORS: dict[str, Decimal] = {
    "sedentary": Decimal("1.20"),
    "light": Decimal("1.30"),
    "moderate": Decimal("1.40"),
    "active": Decimal("1.50"),
    "very_active": Decimal("1.60"),
}
DEFAULT_LIVING_FACTOR = LIVING_FACTORS["moderate"]

MINUTES_PER_DAY = Decimal("1440")

BalanceStatus = Literal["estimated", "needs_profile"]


@dataclass(frozen=True)
class EnergyBalance:
    status: BalanceStatus
    consumed_kcal: Decimal
    exercise_kcal: Decimal
    resting_kcal: Decimal | None = None
    living_kcal: Decimal | None = None
    #: What the training added on top of resting, which living already covers.
    exercise_above_resting_kcal: Decimal | None = None
    total_expenditure_kcal: Decimal | None = None
    balance_kcal: Decimal | None = None
    #: The intake the person is aiming for on an ordinary day, if they set one.
    daily_target_kcal: Decimal | None = None
    #: Target plus what training earned, minus what has been eaten.
    remaining_kcal: Decimal | None = None


def _round(value: Decimal) -> Decimal:
    return value.quantize(ZERO_PLACES, rounding=ROUND_HALF_UP)


def age_on(birth_date: date, today: date) -> int:
    had_birthday = (today.month, today.day) >= (birth_date.month, birth_date.day)
    return today.year - birth_date.year - (0 if had_birthday else 1)


def resting_energy(
    weight_kg: Decimal,
    height_cm: Decimal,
    age_years: int,
    biological_sex: str | None,
) -> Decimal:
    """Resting expenditure by Mifflin-St Jeor, in kilocalories a day."""
    offset = {
        "male": MALE_OFFSET,
        "female": FEMALE_OFFSET,
    }.get(biological_sex or "", UNSPECIFIED_OFFSET)

    estimate = (
        WEIGHT_FACTOR * weight_kg
        + HEIGHT_FACTOR * height_cm
        - AGE_FACTOR * Decimal(age_years)
        + offset
    )
    return _round(estimate)


def energy_balance(
    *,
    consumed_kcal: Decimal,
    exercise_kcal: Decimal,
    exercise_minutes: int,
    daily_target_kcal: Decimal | None = None,
    weight_kg: Decimal | None,
    height_cm: Decimal | None,
    birth_date: date | None,
    biological_sex: str | None,
    activity_level: str,
    today: date,
) -> EnergyBalance:
    """Food against everything spent, or an honest refusal.

    A deficit is the difference between what went in and what the body spent,
    resting included. Without height, weight and age there is no resting figure,
    and calling food minus exercise a deficit would be wrong by a couple of
    thousand kilocalories.
    """
    if weight_kg is None or height_cm is None or birth_date is None:
        return EnergyBalance(
            status="needs_profile",
            consumed_kcal=consumed_kcal,
            exercise_kcal=exercise_kcal,
        )

    resting = resting_energy(weight_kg, height_cm, age_on(birth_date, today), biological_sex)
    living = _round(resting * LIVING_FACTORS.get(activity_level, DEFAULT_LIVING_FACTOR))

    # A metabolic equivalent of 1 is resting, so the figure for a session already
    # contains the resting energy of those minutes, and daily living covers all
    # 24 hours. Only what the training added above resting belongs on top.
    resting_during_training = resting * Decimal(exercise_minutes) / MINUTES_PER_DAY
    above_resting = _round(max(exercise_kcal - resting_during_training, Decimal("0")))
    total = _round(living + above_resting)

    # Training earns room to eat, which is why it is added rather than the
    # target being lowered on the days someone trains.
    remaining = (
        _round(daily_target_kcal + above_resting - consumed_kcal)
        if daily_target_kcal is not None
        else None
    )

    return EnergyBalance(
        status="estimated",
        consumed_kcal=consumed_kcal,
        exercise_kcal=exercise_kcal,
        resting_kcal=resting,
        living_kcal=living,
        exercise_above_resting_kcal=above_resting,
        total_expenditure_kcal=total,
        balance_kcal=_round(consumed_kcal - total),
        daily_target_kcal=daily_target_kcal,
        remaining_kcal=remaining,
    )
