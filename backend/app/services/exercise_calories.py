import re
import unicodedata
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import UUID

from app.models.enums import ExerciseIntensity
from app.services.met_cache import RedisMetCache
from app.services.met_lookup import MetLookup

TWO_PLACES = Decimal("0.01")
MINUTES_PER_HOUR = Decimal("60")
WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class ActivityFamily:
    name: str
    #: Word beginnings, so caminata, caminando and caminar all land together.
    stems: tuple[str, ...]
    met: Decimal


# Metabolic equivalents following the Compendium of Physical Activities. Each
# value is an average for a whole session at a normal effort, rest between
# rounds and sets included, which is why the intensity below only nudges it.
ACTIVITY_FAMILIES: tuple[ActivityFamily, ...] = (
    # A class is bag work in intervals: the Compendium puts a punching bag at
    # 5.5 and sparring at 7.8, while 12.8 is competitive boxing in a ring.
    ActivityFamily("boxing", ("fitbox", "box", "kickbox", "muay"), Decimal("8.0")),
    ActivityFamily("running", ("corr", "carrera", "running", "trot", "maraton"), Decimal("9.8")),
    ActivityFamily("cycling", ("bici", "ciclismo", "cycling", "spinning", "pedal"), Decimal("7.5")),
    ActivityFamily("swimming", ("nadar", "nadando", "natacion", "swim", "piscina"), Decimal("7.0")),
    ActivityFamily(
        "strength",
        ("pesa", "gimnasio", "fuerza", "musculacion", "crossfit", "halterofilia"),
        Decimal("5.0"),
    ),
    ActivityFamily("mobility", ("yoga", "pilates", "estiramiento", "movilidad"), Decimal("3.0")),
    # Cross country hiking is 6.0, well above a walk on the flat.
    ActivityFamily("hiking", ("senderismo", "hiking", "trekking", "excursion"), Decimal("6.0")),
    ActivityFamily(
        "racquet",
        ("padel", "tenis", "futbol", "baloncesto", "squash", "basket"),
        Decimal("7.3"),
    ),
    ActivityFamily("cardio", ("eliptica", "remo", "hiit", "circuito", "cinta"), Decimal("8.0")),
    ActivityFamily("dance", ("baile", "bailar", "zumba", "danza"), Decimal("6.5")),
    ActivityFamily(
        "walking", ("camin", "andar", "andando", "walk", "paseo", "pasear"), Decimal("3.5")
    ),
)

# Words that say the ground went up. Walking a hill is a different activity from
# walking on the flat: the Compendium puts a 1-5% grade at 5.3 and 6-15% at 8.0,
# against 3.5 on the level.
HILL_STEMS = ("cuesta", "subida", "subiendo", "pendiente", "montana", "monte", "colina", "uphill")
HILL_FACTOR = Decimal("1.8")

GENERIC_MET = Decimal("6.0")

MetSource = Literal["table", "remembered", "provider", "generic"]


@dataclass(frozen=True)
class ActivityMet:
    met: Decimal
    source: MetSource


# The table value already describes a normal effort at that activity, so these
# adjust it rather than scale it. A wider range would compound with a value that
# is already vigorous: 9.5 times 1.35 lands on competitive boxing for 47 minutes
# straight, which is not what a class is.
INTENSITY_FACTORS: dict[ExerciseIntensity, Decimal] = {
    ExerciseIntensity.LOW: Decimal("0.85"),
    ExerciseIntensity.MODERATE: Decimal("1.00"),
    ExerciseIntensity.HIGH: Decimal("1.12"),
    ExerciseIntensity.VERY_HIGH: Decimal("1.22"),
}


def _fold(value: str) -> str:
    """Lowercase, drop the accents and tidy the spacing.

    So natación matches natacion, and a stray double space does not make the
    same activity look like a new one.
    """
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return WHITESPACE.sub(" ", without_accents).strip()


def metabolic_equivalent(activity_name: str) -> Decimal:
    return table_met(activity_name) or GENERIC_MET


def _starts_any(words: tuple[str, ...], stems: tuple[str, ...]) -> bool:
    """Match a stem against the start of a word, never mid-word.

    Plain substrings would read "recorrido" as running, and would miss
    "caminata" while matching "caminar".
    """
    return any(word.startswith(stem) for word in words for stem in stems)


def table_met(activity_name: str) -> Decimal | None:
    """The published value for an activity the table knows, or nothing."""
    words = tuple(_fold(activity_name).split(" "))

    for family in ACTIVITY_FAMILIES:
        if not _starts_any(words, family.stems):
            continue

        # Only walking gets the slope treatment: a run or a ride uphill is
        # already priced near the top of its own band.
        if family.name == "walking" and _starts_any(words, HILL_STEMS):
            return family.met * HILL_FACTOR

        return family.met

    return None


async def resolve_met(
    user_id: UUID,
    activity_name: str,
    lookup: MetLookup | None = None,
    cache: RedisMetCache | None = None,
) -> ActivityMet:
    """Find the metabolic equivalent, asking the provider only when needed.

    The table answers instantly and for free, so it goes first. A provider is
    worth a request only for an activity nobody tabulated here, and the answer
    is remembered because it will not change.
    """
    tabulated = table_met(activity_name)
    if tabulated is not None:
        return ActivityMet(met=tabulated, source="table")

    key = _fold(activity_name)

    if cache is not None:
        remembered = await cache.get(user_id, key)
        if remembered is not None:
            return ActivityMet(met=remembered, source="remembered")

    if lookup is not None:
        found = await lookup.met_for(user_id, activity_name)
        if found is not None:
            if cache is not None:
                await cache.set(user_id, key, found)
            return ActivityMet(met=found, source="provider")

    return ActivityMet(met=GENERIC_MET, source="generic")


def estimate_calories(
    activity_name: str,
    intensity: ExerciseIntensity,
    duration_minutes: int,
    weight_kg: Decimal | None,
    met: Decimal | None = None,
) -> Decimal | None:
    """Estimate the expenditure, or nothing when body weight is unknown.

    Expenditure depends on how much body is being moved, so without a weight
    any number would be invented rather than estimated. The arithmetic stays
    here: a language model is asked what an activity costs, never to multiply.
    """
    if weight_kg is None or weight_kg <= 0 or duration_minutes <= 0:
        return None

    base = met if met is not None else metabolic_equivalent(activity_name)
    hours = Decimal(duration_minutes) / MINUTES_PER_HOUR

    return (base * INTENSITY_FACTORS[intensity] * weight_kg * hours).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
