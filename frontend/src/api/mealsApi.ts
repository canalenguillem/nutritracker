import { z } from "zod";

import {
  dailySummaryResponseSchema,
  foodEstimateResponseSchema,
  mealListResponseSchema,
  mealResponseSchema,
  parseAmount,
} from "../schemas/mealSchema";
import type {
  DailySummary,
  DailySummaryResponse,
  FoodEstimate,
  Meal,
  MealFormValues,
  MealItem,
  MealItemResponse,
  MealResponse,
} from "../types/meal";
import { httpClient } from "./httpClient";

const pad = (value: number): string => String(Math.floor(Math.abs(value))).padStart(2, "0");

/**
 * Combine the day and time fields into an instant the API can place on the
 * timeline. Sending the browser offset keeps a 00:30 supper on the right day.
 */
export const toInstant = (day: string, time: string): string => {
  const [year = 0, month = 1, date = 1] = day.split("-").map(Number);
  const [hours = 0, minutes = 0] = time.split(":").map(Number);
  const local = new Date(year, month - 1, date, hours, minutes, 0, 0);
  const offsetMinutes = -local.getTimezoneOffset();
  const sign = offsetMinutes < 0 ? "-" : "+";

  return `${day}T${time}:00${sign}${pad(offsetMinutes / 60)}:${pad(offsetMinutes % 60)}`;
};

const toAmount = (value: string): string => parseAmount(value).toFixed(2);

const toMealItem = (response: MealItemResponse): MealItem => ({
  id: response.id,
  name: response.name,
  quantity: Number(response.quantity),
  unit: response.unit,
  kcal: Number(response.kcal),
  proteinG: Number(response.protein_g),
  fatG: Number(response.fat_g),
  carbohydratesG: Number(response.carbohydrates_g),
  kcalFromMacros: Number(response.kcal_from_macros),
  macrosDisagree: response.macros_disagree,
});

const toMeal = (response: MealResponse): Meal => ({
  id: response.id,
  mealType: response.meal_type,
  eatenAt: response.eaten_at,
  source: response.source,
  notes: response.notes,
  kcal: Number(response.total_kcal),
  proteinG: Number(response.protein_g),
  fatG: Number(response.fat_g),
  carbohydratesG: Number(response.carbohydrates_g),
  items: response.items.map(toMealItem),
});

const toDailySummary = (response: DailySummaryResponse): DailySummary => ({
  logDate: response.log_date,
  mealCount: response.meal_count,
  exerciseKcal: Number(response.exercise_kcal),
  exerciseCount: response.exercise_count,
  netKcal: Number(response.net_kcal),
  fastingHours: response.fasting_hours === null ? null : Number(response.fasting_hours),
  fastingStartedAt: response.fasting_started_at,
  fastingEndedAt: response.fasting_ended_at,
  fastingOngoing: response.fasting_ongoing,
  balanceStatus: response.balance_status,
  restingKcal: response.resting_kcal === null ? null : Number(response.resting_kcal),
  livingKcal: response.living_kcal === null ? null : Number(response.living_kcal),
  exerciseAboveRestingKcal:
    response.exercise_above_resting_kcal === null
      ? null
      : Number(response.exercise_above_resting_kcal),
  totalExpenditureKcal:
    response.total_expenditure_kcal === null
      ? null
      : Number(response.total_expenditure_kcal),
  balanceKcal: response.balance_kcal === null ? null : Number(response.balance_kcal),
  kcal: Number(response.total_kcal),
  proteinG: Number(response.protein_g),
  fatG: Number(response.fat_g),
  carbohydratesG: Number(response.carbohydrates_g),
});

export const getDailySummary = async (day?: string): Promise<DailySummary> => {
  const response = await httpClient.get<unknown>("/meals/summary", {
    params: day ? { date: day } : undefined,
  });

  return toDailySummary(dailySummaryResponseSchema.parse(response.data));
};

export const getHistory = async (days: number): Promise<DailySummary[]> => {
  const response = await httpClient.get<unknown>("/meals/history", { params: { days } });

  return z.array(dailySummaryResponseSchema).parse(response.data).map(toDailySummary);
};

export const getMeals = async (day: string): Promise<Meal[]> => {
  const response = await httpClient.get<unknown>("/meals", { params: { date: day } });

  return mealListResponseSchema.parse(response.data).map(toMeal);
};

export const createMeal = async (values: MealFormValues): Promise<Meal> => {
  const response = await httpClient.post<unknown>("/meals", {
    meal_type: values.mealType,
    eaten_at: toInstant(values.day, values.time),
    notes: values.notes.trim() || null,
    items: values.items.map((item) => ({
      name: item.name.trim(),
      quantity: toAmount(item.quantity),
      unit: item.unit.trim(),
      kcal: toAmount(item.kcal),
      protein_g: toAmount(item.protein_g),
      fat_g: toAmount(item.fat_g),
      carbohydrates_g: toAmount(item.carbohydrates_g),
    })),
  });

  return toMeal(mealResponseSchema.parse(response.data));
};

export const getMeal = async (mealId: string): Promise<Meal> => {
  const response = await httpClient.get<unknown>(`/meals/${mealId}`);

  return toMeal(mealResponseSchema.parse(response.data));
};

export const updateMeal = async ({
  mealId,
  values,
}: {
  readonly mealId: string;
  readonly values: MealFormValues;
}): Promise<Meal> => {
  const response = await httpClient.patch<unknown>(`/meals/${mealId}`, {
    meal_type: values.mealType,
    eaten_at: toInstant(values.day, values.time),
    notes: values.notes.trim() || null,
    items: values.items.map((item) => ({
      name: item.name.trim(),
      quantity: toAmount(item.quantity),
      unit: item.unit.trim(),
      kcal: toAmount(item.kcal),
      protein_g: toAmount(item.protein_g),
      fat_g: toAmount(item.fat_g),
      carbohydrates_g: toAmount(item.carbohydrates_g),
    })),
  });

  return toMeal(mealResponseSchema.parse(response.data));
};

export const deleteMeal = async (mealId: string): Promise<void> => {
  await httpClient.delete(`/meals/${mealId}`);
};

export const describeMeal = async ({
  description,
  photo,
}: {
  readonly description: string;
  readonly photo?: File | null;
}): Promise<FoodEstimate> => {
  const form = new FormData();
  form.append("description", description);
  if (photo) {
    form.append("photo", photo);
  }

  const response = await httpClient.post<unknown>("/meals/describe", form);
  const estimate = foodEstimateResponseSchema.parse(response.data);

  return {
    summary: estimate.summary,
    totalKcal: Number(estimate.total_kcal),
    confidence: estimate.confidence === null ? null : Number(estimate.confidence),
    warning: estimate.warning,
    fromCache: estimate.from_cache,
    items: estimate.items.map((item) => ({
      name: item.name,
      quantity: Number(item.quantity),
      unit: item.unit,
      kcal: Number(item.kcal),
      proteinG: Number(item.protein_g),
      fatG: Number(item.fat_g),
      carbohydratesG: Number(item.carbohydrates_g),
      confidence: item.confidence === null ? null : Number(item.confidence),
      assumptions: item.assumptions,
      kcalFromMacros: Number(item.kcal_from_macros),
      macrosDisagree: item.macros_disagree,
    })),
    questions: estimate.questions.map((question) => ({
      key: question.key,
      question: question.question,
      options: question.options,
    })),
  };
};

export const getRecentMeals = async (query: string): Promise<Meal[]> => {
  const response = await httpClient.get<unknown>("/meals/recent", {
    params: query.trim() ? { query: query.trim() } : undefined,
  });

  return mealListResponseSchema.parse(response.data).map(toMeal);
};
