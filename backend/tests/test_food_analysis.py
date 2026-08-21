import json
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.food_analysis import (
    EstimatedItem,
    FoodAnalysisDisabledError,
    FoodAnalysisError,
    FoodAnalysisService,
    FoodEstimate,
    InvalidAnalysisResponseError,
    MealPhoto,
    normalize_description,
)
from app.services.openai_food_analyzer import _to_estimate
from fakes import FakeFoodAnalyzer, FakeFoodEstimateCache

USER_ID = uuid4()

COFFEE = FoodEstimate(
    summary="Café con nata",
    items=[
        EstimatedItem(
            name="Café solo",
            quantity=Decimal("60"),
            unit="ml",
            kcal=Decimal("2.00"),
            protein_g=Decimal("0.20"),
            fat_g=Decimal("0.00"),
            carbohydrates_g=Decimal("0.00"),
            confidence=Decimal("0.9"),
        ),
        EstimatedItem(
            name="Nata para café",
            quantity=Decimal("20"),
            unit="ml",
            kcal=Decimal("58.00"),
            protein_g=Decimal("0.40"),
            fat_g=Decimal("6.00"),
            carbohydrates_g=Decimal("0.60"),
            confidence=Decimal("0.5"),
            assumptions=["Se asume nata líquida para café"],
        ),
    ],
    total_kcal=Decimal("999.00"),
)


async def test_the_service_reports_when_no_provider_is_configured() -> None:
    service = FoodAnalysisService(None)

    assert service.enabled is False
    with pytest.raises(FoodAnalysisDisabledError):
        await service.describe(USER_ID, "café con nata")


async def test_the_service_totals_the_items_itself() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE))

    estimate = await service.describe(USER_ID, "café con nata")

    # The provider claimed 999; the sum of the items is what counts.
    assert estimate.total_kcal == Decimal("60.00")


async def test_the_service_passes_the_account_language() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    service = FoodAnalysisService(analyzer)

    await service.describe(USER_ID, "  café con nata  ", "es")

    assert analyzer.calls == [("café con nata", "es")]


async def test_an_empty_description_is_refused() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE))

    with pytest.raises(InvalidAnalysisResponseError):
        await service.describe(USER_ID, "   ")


async def test_an_estimate_without_food_is_refused() -> None:
    empty = FoodEstimate(summary="", items=[], total_kcal=Decimal("0"))
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=empty))

    with pytest.raises(InvalidAnalysisResponseError):
        await service.describe(USER_ID, "una piedra")


async def test_a_provider_failure_surfaces_as_an_analysis_error() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(error=FoodAnalysisError()))

    with pytest.raises(FoodAnalysisError):
        await service.describe(USER_ID, "café con nata")


def test_a_provider_payload_is_mapped_to_the_domain() -> None:
    payload = json.dumps(
        {
            "meal_summary": "Café con nata",
            "analysis_confidence": 0.7,
            "warning": "Las calorías son una estimación.",
            "items": [
                {
                    "name": " Café solo ",
                    "estimated_quantity": 60,
                    "unit": "ml",
                    "estimated_kcal": 2,
                    "protein_g": 0.2,
                    "fat_g": 0,
                    "carbohydrates_g": 0,
                    "confidence": 0.9,
                    "assumptions": ["Sin azúcar", ""],
                }
            ],
            "clarification_questions": [
                {
                    "key": "cream_type",
                    "question": "¿La nata era líquida o montada?",
                    "options": ["Líquida", "Montada", "No lo sé"],
                }
            ],
        }
    )

    estimate = _to_estimate(payload, "v1")

    assert estimate.items[0].name == "Café solo"
    assert estimate.items[0].kcal == Decimal("2.00")
    assert estimate.items[0].assumptions == ["Sin azúcar"]
    assert estimate.total_kcal == Decimal("2.00")
    assert estimate.questions[0].key == "cream_type"
    assert estimate.confidence == Decimal("0.7")


def test_a_malformed_payload_is_refused() -> None:
    with pytest.raises(InvalidAnalysisResponseError):
        _to_estimate("not json at all", "v1")


def test_an_empty_payload_is_refused() -> None:
    with pytest.raises(InvalidAnalysisResponseError):
        _to_estimate(None, "v1")


def test_a_negative_amount_is_refused() -> None:
    payload = json.dumps(
        {
            "meal_summary": "Café",
            "analysis_confidence": 0.5,
            "warning": "",
            "items": [
                {
                    "name": "Café",
                    "estimated_quantity": 60,
                    "unit": "ml",
                    "estimated_kcal": -5,
                    "protein_g": 0,
                    "fat_g": 0,
                    "carbohydrates_g": 0,
                    "confidence": 0.5,
                    "assumptions": [],
                }
            ],
            "clarification_questions": [],
        }
    )

    with pytest.raises(InvalidAnalysisResponseError):
        _to_estimate(payload, "v1")


async def test_a_repeated_description_is_served_without_the_provider() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    cache = FakeFoodEstimateCache()
    service = FoodAnalysisService(analyzer, cache)

    first = await service.describe(USER_ID, "Un café con nata")
    second = await service.describe(USER_ID, "un  café con nata.")

    assert len(analyzer.calls) == 1
    assert first.from_cache is False
    assert second.from_cache is True
    assert second.total_kcal == first.total_kcal
    assert [item.name for item in second.items] == [item.name for item in first.items]


async def test_another_account_does_not_read_the_first_ones_estimate() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    service = FoodAnalysisService(analyzer, FakeFoodEstimateCache())

    await service.describe(USER_ID, "café con nata")
    await service.describe(uuid4(), "café con nata")

    assert len(analyzer.calls) == 2


async def test_a_remembered_estimate_survives_an_unconfigured_provider() -> None:
    cache = FakeFoodEstimateCache()
    stored = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE), cache)
    await stored.describe(USER_ID, "café con nata")

    without_provider = FoodAnalysisService(None, cache)
    estimate = await without_provider.describe(USER_ID, "café con nata")

    assert estimate.from_cache is True


async def test_an_unknown_description_still_needs_a_provider() -> None:
    service = FoodAnalysisService(None, FakeFoodEstimateCache())

    with pytest.raises(FoodAnalysisDisabledError):
        await service.describe(USER_ID, "tortilla de patatas")


def test_the_same_meal_typed_differently_shares_a_key() -> None:
    assert normalize_description("  Un CAFÉ con nata. ") == normalize_description(
        "un café con nata"
    )
    assert normalize_description("café  con   nata") == "café con nata"


async def test_a_picture_alone_is_enough_to_work_from() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    service = FoodAnalysisService(analyzer)
    photo = MealPhoto(content=b"\xff\xd8\xff" + b"0" * 32, media_type="image/jpeg")

    estimate = await service.describe(USER_ID, "", photo=photo)

    assert estimate.items
    assert analyzer.photos == [photo]


async def test_with_neither_words_nor_picture_there_is_nothing_to_do() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE))

    with pytest.raises(InvalidAnalysisResponseError):
        await service.describe(USER_ID, "   ")


async def test_two_pictures_of_different_plates_are_not_the_same_estimate() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    cache = FakeFoodEstimateCache()
    first = MealPhoto(content=b"\xff\xd8\xff" + b"a" * 32, media_type="image/jpeg")
    second = MealPhoto(content=b"\xff\xd8\xff" + b"b" * 32, media_type="image/jpeg")

    await service_with(analyzer, cache).describe(USER_ID, "", photo=first)
    await service_with(analyzer, cache).describe(USER_ID, "", photo=second)

    assert len(analyzer.calls) == 2


def service_with(analyzer: FakeFoodAnalyzer, cache: FakeFoodEstimateCache) -> FoodAnalysisService:
    return FoodAnalysisService(analyzer, cache)
