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
LIVING_FACTORS: dict[str, Decimal] = {
    "sedentary": Decimal("1.15"),
    "light": Decimal("1.25"),
    "moderate": Decimal("1.35"),
    "active": Decimal("1.45"),
    "very_active": Decimal("1.55"),
}
DEFAULT_LIVING_FACTOR = LIVING_FACTORS["moderate"]

BalanceStatus = Literal["estimated", "needs_profile"]


@dataclass(frozen=True)
class EnergyBalance:
    status: BalanceStatus
    consumed_kcal: Decimal
    exercise_kcal: Decimal
    resting_kcal: Decimal | None = None
    living_kcal: Decimal | None = None
    total_expenditure_kcal: Decimal | None = None
    balance_kcal: Decimal | None = None


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
    total = _round(living + exercise_kcal)

    return EnergyBalance(
        status="estimated",
        consumed_kcal=consumed_kcal,
        exercise_kcal=exercise_kcal,
        resting_kcal=resting,
        living_kcal=living,
        total_expenditure_kcal=total,
        balance_kcal=_round(consumed_kcal - total),
    )
