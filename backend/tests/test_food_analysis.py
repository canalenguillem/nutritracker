import json
from decimal import Decimal

import pytest

from app.services.food_analysis import (
    EstimatedItem,
    FoodAnalysisDisabledError,
    FoodAnalysisError,
    FoodAnalysisService,
    FoodEstimate,
    InvalidAnalysisResponseError,
)
from app.services.openai_food_analyzer import _to_estimate
from fakes import FakeFoodAnalyzer

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
        await service.describe("café con nata")


async def test_the_service_totals_the_items_itself() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE))

    estimate = await service.describe("café con nata")

    # The provider claimed 999; the sum of the items is what counts.
    assert estimate.total_kcal == Decimal("60.00")


async def test_the_service_passes_the_account_language() -> None:
    analyzer = FakeFoodAnalyzer(estimate=COFFEE)
    service = FoodAnalysisService(analyzer)

    await service.describe("  café con nata  ", "es")

    assert analyzer.calls == [("café con nata", "es")]


async def test_an_empty_description_is_refused() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=COFFEE))

    with pytest.raises(InvalidAnalysisResponseError):
        await service.describe("   ")


async def test_an_estimate_without_food_is_refused() -> None:
    empty = FoodEstimate(summary="", items=[], total_kcal=Decimal("0"))
    service = FoodAnalysisService(FakeFoodAnalyzer(estimate=empty))

    with pytest.raises(InvalidAnalysisResponseError):
        await service.describe("una piedra")


async def test_a_provider_failure_surfaces_as_an_analysis_error() -> None:
    service = FoodAnalysisService(FakeFoodAnalyzer(error=FoodAnalysisError()))

    with pytest.raises(FoodAnalysisError):
        await service.describe("café con nata")


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
