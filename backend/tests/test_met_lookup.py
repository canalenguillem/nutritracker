import json
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.models.enums import ExerciseIntensity
from app.services.exercise_calories import estimate_calories, resolve_met, table_met
from app.services.met_lookup import _to_met

USER_ID = uuid4()


@dataclass
class FakeMetLookup:
    met: Decimal | None = None
    calls: list[str] = field(default_factory=list)

    async def met_for(self, user_id: UUID, activity_name: str) -> Decimal | None:
        self.calls.append(activity_name)
        return self.met


@dataclass
class FakeMetCache:
    entries: dict[tuple[UUID, str], Decimal] = field(default_factory=dict)

    async def get(self, user_id: UUID, activity_name: str) -> Decimal | None:
        return self.entries.get((user_id, activity_name))

    async def set(self, user_id: UUID, activity_name: str, met: Decimal) -> None:
        self.entries[(user_id, activity_name)] = met


def payload(**overrides: object) -> str:
    return json.dumps({"recognised": True, "activity": "bouldering", "met": 8.0, **overrides})


async def test_a_tabulated_activity_never_asks_the_provider() -> None:
    lookup = FakeMetLookup(met=Decimal("3.0"))

    resolved = await resolve_met(USER_ID, "Brooklyn Fitboxing", lookup=lookup)

    assert resolved.source == "table"
    assert resolved.met == Decimal("9.5")
    assert lookup.calls == []


async def test_an_unknown_activity_is_asked_about_once() -> None:
    lookup = FakeMetLookup(met=Decimal("8.00"))
    cache = FakeMetCache()

    first = await resolve_met(USER_ID, "Escalada en rocódromo", lookup=lookup, cache=cache)
    second = await resolve_met(USER_ID, "escalada en  ROCÓDROMO", lookup=lookup, cache=cache)

    assert first.source == "provider"
    assert second.source == "remembered"
    assert second.met == Decimal("8.00")
    assert len(lookup.calls) == 1


async def test_without_a_provider_an_unknown_activity_falls_back() -> None:
    resolved = await resolve_met(USER_ID, "malabares con antorchas")

    assert resolved.source == "generic"
    assert resolved.met == Decimal("6.0")


async def test_a_provider_that_does_not_know_falls_back() -> None:
    resolved = await resolve_met(USER_ID, "cosa raquítica", lookup=FakeMetLookup(met=None))

    assert resolved.source == "generic"


async def test_the_resolved_value_drives_the_estimate() -> None:
    resolved = await resolve_met(USER_ID, "Escalada", lookup=FakeMetLookup(met=Decimal("8.00")))

    estimate = estimate_calories(
        "Escalada", ExerciseIntensity.MODERATE, 60, Decimal("80"), met=resolved.met
    )

    # 8 MET * 1.0 * 80 kg * 1 h
    assert estimate == Decimal("640.00")


def test_the_table_still_answers_for_what_it_knows() -> None:
    assert table_met("sesión de natación") == Decimal("7.0")
    assert table_met("malabares") is None


@pytest.mark.parametrize(
    "body",
    [
        payload(met=None),
        payload(recognised=False),
        payload(met=400),
        payload(met=0.1),
        "not json",
        None,
    ],
)
def test_an_answer_that_cannot_be_trusted_is_discarded(body: str | None) -> None:
    assert _to_met(body) is None


def test_a_sensible_answer_is_kept() -> None:
    assert _to_met(payload(met=8.3)) == Decimal("8.3")
