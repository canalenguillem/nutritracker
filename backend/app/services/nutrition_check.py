from decimal import ROUND_HALF_UP, Decimal

ZERO_PLACES = Decimal("1")

# Atwater factors: what a gram of each yields once digested.
KCAL_PER_PROTEIN_G = Decimal("4")
KCAL_PER_CARBOHYDRATE_G = Decimal("4")
KCAL_PER_FAT_G = Decimal("9")

# Rounding and the coarser factors for fibre or alcohol make small gaps normal,
# and food tables agree with each other within about a tenth. Past that, the two
# figures are describing different amounts of food.
TOLERANCE_RATIO = Decimal("0.10")
TOLERANCE_KCAL = Decimal("25")


def kcal_from_macros(protein_g: Decimal, fat_g: Decimal, carbohydrates_g: Decimal) -> Decimal:
    """What the macronutrients alone say the energy should be."""
    total = (
        protein_g * KCAL_PER_PROTEIN_G
        + carbohydrates_g * KCAL_PER_CARBOHYDRATE_G
        + fat_g * KCAL_PER_FAT_G
    )
    return total.quantize(ZERO_PLACES, rounding=ROUND_HALF_UP)


def macros_disagree(
    kcal: Decimal, protein_g: Decimal, fat_g: Decimal, carbohydrates_g: Decimal
) -> bool:
    """Whether the stated energy and the macronutrients contradict each other.

    An estimate saying 900 kcal while its macronutrients add up to 1030 is wrong
    one way or the other, and worth showing before it lands in the day's total.
    """
    from_macros = kcal_from_macros(protein_g, fat_g, carbohydrates_g)

    # Nothing to compare when neither figure carries any energy.
    if from_macros == 0 and kcal == 0:
        return False

    gap = abs(from_macros - kcal)
    if gap <= TOLERANCE_KCAL:
        return False

    reference = max(from_macros, kcal)
    return reference > 0 and gap / reference > TOLERANCE_RATIO
