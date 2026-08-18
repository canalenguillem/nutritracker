import type { MealType } from "../../types/meal";

const mealTypeLabels: Readonly<Record<MealType, string>> = {
  breakfast: "Desayuno",
  lunch: "Comida",
  dinner: "Cena",
  snack: "Tentempié",
};

export const mealTypeOptions = [
  { value: "breakfast", label: mealTypeLabels.breakfast },
  { value: "lunch", label: mealTypeLabels.lunch },
  { value: "dinner", label: mealTypeLabels.dinner },
  { value: "snack", label: mealTypeLabels.snack },
] as const;

export const getMealTypeLabel = (mealType: MealType): string => mealTypeLabels[mealType];

export const formatEnergy = (kcal: number): string =>
  new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 }).format(kcal);

export const formatGrams = (grams: number): string =>
  new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 }).format(grams);

export const formatQuantity = (quantity: number, unit: string): string =>
  `${new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 }).format(quantity)} ${unit}`;

export const formatTime = (instant: string): string =>
  new Intl.DateTimeFormat("es-ES", { hour: "2-digit", minute: "2-digit" }).format(
    new Date(instant),
  );

export const formatDay = (day: string): string => {
  const [year = 0, month = 1, date = 1] = day.split("-").map(Number);

  return new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date(year, month - 1, date));
};
