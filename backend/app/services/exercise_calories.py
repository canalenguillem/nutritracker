import unicodedata
from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import ExerciseIntensity

TWO_PLACES = Decimal("0.01")
MINUTES_PER_HOUR = Decimal("60")

# Metabolic equivalents for the activities people record most often. A value is
# an average for the activity, which the intensity then adjusts.
ACTIVITY_METS: tuple[tuple[tuple[str, ...], Decimal], ...] = (
    (("fitboxing", "boxeo", "boxing", "kickboxing", "muay"), Decimal("9.5")),
    (("correr", "running", "carrera", "trote", "maraton"), Decimal("9.8")),
    (("caminar", "andar", "walking", "paseo", "senderismo"), Decimal("3.5")),
    (("bicicleta", "ciclismo", "bici", "cycling", "spinning"), Decimal("7.5")),
    (("natacion", "nadar", "swimming", "piscina"), Decimal("7.0")),
    (("pesas", "gimnasio", "fuerza", "musculacion", "crossfit"), Decimal("5.0")),
    (("yoga", "pilates", "estiramientos", "movilidad"), Decimal("3.0")),
    (("padel", "tenis", "futbol", "baloncesto", "squash"), Decimal("7.3")),
    (("eliptica", "remo", "hiit", "circuito", "cinta"), Decimal("8.0")),
    (("baile", "zumba", "danza"), Decimal("6.5")),
)

GENERIC_MET = Decimal("6.0")

INTENSITY_FACTORS: dict[ExerciseIntensity, Decimal] = {
    ExerciseIntensity.LOW: Decimal("0.80"),
    ExerciseIntensity.MODERATE: Decimal("1.00"),
    ExerciseIntensity.HIGH: Decimal("1.20"),
    ExerciseIntensity.VERY_HIGH: Decimal("1.35"),
}


def _fold(value: str) -> str:
    """Lowercase and drop the accents, so natación matches natacion."""
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def metabolic_equivalent(activity_name: str) -> Decimal:
    folded = _fold(activity_name)
    for keywords, met in ACTIVITY_METS:
        if any(keyword in folded for keyword in keywords):
            return met
    return GENERIC_MET


def estimate_calories(
    activity_name: str,
    intensity: ExerciseIntensity,
    duration_minutes: int,
    weight_kg: Decimal | None,
) -> Decimal | None:
    """Estimate the expenditure, or nothing when body weight is unknown.

    Expenditure depends on how much body is being moved, so without a weight
    any number would be invented rather than estimated.
    """
    if weight_kg is None or weight_kg <= 0 or duration_minutes <= 0:
        return None

    met = metabolic_equivalent(activity_name) * INTENSITY_FACTORS[intensity]
    hours = Decimal(duration_minutes) / MINUTES_PER_HOUR

    return (met * weight_kg * hours).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
