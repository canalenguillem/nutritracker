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

/** Hours as a person says them: "16 h 20 min", not "16,33 h". */
export const formatFastingLength = (hours: number): string => {
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);

  if (minutes === 0) {
    return `${wholeHours} h`;
  }
  if (minutes === 60) {
    return `${wholeHours + 1} h`;
  }

  return `${wholeHours} h ${minutes} min`;
};

const pad = (value: number): string => String(value).padStart(2, "0");

export const toIsoDay = (day: Date): string =>
  `${day.getFullYear()}-${pad(day.getMonth() + 1)}-${pad(day.getDate())}`;

export const fromIsoDay = (isoDay: string): Date => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);

  return new Date(year, month - 1, day);
};

/** The Monday opening the week a day belongs to, as weeks are read here. */
export const mondayOf = (isoDay: string): string => {
  const day = fromIsoDay(isoDay);
  // getDay() calls Sunday 0, so Monday has to be pulled back by six, not one.
  const backwards = day.getDay() === 0 ? 6 : day.getDay() - 1;
  day.setDate(day.getDate() - backwards);

  return toIsoDay(day);
};

export const addDays = (isoDay: string, days: number): string => {
  const day = fromIsoDay(isoDay);
  day.setDate(day.getDate() + days);

  return toIsoDay(day);
};
