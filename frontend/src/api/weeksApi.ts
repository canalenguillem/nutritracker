import { weekResponseSchema } from "../schemas/weekSchema";
import type { Week } from "../types/week";
import { httpClient } from "./httpClient";

type WeekResponse = ReturnType<typeof weekResponseSchema.parse>;

const optionalNumber = (value: string | null): number | null =>
  value === null ? null : Number(value);

const toWeek = (response: WeekResponse): Week => ({
  weekStart: response.week_start,
  weekEnd: response.week_end,
  isComplete: response.is_complete,
  days: response.days.map((day) => ({
    logDate: day.log_date,
    kcal: Number(day.food_kcal),
    exerciseKcal: Number(day.exercise_kcal),
    balanceKcal: optionalNumber(day.balance_kcal),
    sleepHours: optionalNumber(day.sleep_hours),
    hasFood: day.has_food,
    hasExercise: day.has_exercise,
  })),
  daysWithFood: response.days_with_food,
  daysWithExercise: response.days_with_exercise,
  daysWithSleep: response.days_with_sleep,
  totalKcal: Number(response.total_food_kcal),
  averageKcal: optionalNumber(response.average_food_kcal),
  totalExerciseKcal: Number(response.total_exercise_kcal),
  averageSleepHours: optionalNumber(response.average_sleep_hours),
  averageBalanceKcal: optionalNumber(response.average_balance_kcal),
  weightChangeKg: optionalNumber(response.weight_change_kg),
  canReview: response.can_review,
  hasPreviousReview: response.has_previous_review,
  review:
    response.review === null
      ? null
      : {
          weekStart: response.review.week_start,
          generatedAt: response.review.generated_at,
          isFinal: response.review.is_final,
          headline: response.review.headline,
          observations: response.review.observations,
          comparison: response.review.comparison,
          watchOut: response.review.watch_out,
        },
});

export const getWeek = async (week: string): Promise<Week> => {
  const response = await httpClient.get<unknown>("/weeks", { params: { week } });

  return toWeek(weekResponseSchema.parse(response.data));
};

export const reviewWeek = async (week: string): Promise<Week> => {
  const response = await httpClient.post<unknown>("/weeks/review", null, { params: { week } });

  return toWeek(weekResponseSchema.parse(response.data));
};
