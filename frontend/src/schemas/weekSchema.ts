import { z } from "zod";

const decimal = z.string().nullable();

export const weekReviewResponseSchema = z
  .object({
    week_start: z.string(),
    generated_at: z.string(),
    is_final: z.boolean(),
    headline: z.string(),
    observations: z.array(z.string()),
    comparison: z.string().nullable(),
    watch_out: z.string().nullable(),
  })
  .passthrough();

export const weekDayResponseSchema = z
  .object({
    log_date: z.string(),
    food_kcal: z.string(),
    exercise_kcal: z.string(),
    balance_kcal: decimal,
    sleep_hours: decimal,
    has_food: z.boolean(),
    has_exercise: z.boolean(),
  })
  .passthrough();

export const weekResponseSchema = z
  .object({
    week_start: z.string(),
    week_end: z.string(),
    is_complete: z.boolean(),
    days: z.array(weekDayResponseSchema),
    days_with_food: z.number(),
    days_with_exercise: z.number(),
    days_with_sleep: z.number(),
    total_food_kcal: z.string(),
    average_food_kcal: decimal,
    total_exercise_kcal: z.string(),
    average_sleep_hours: decimal,
    average_balance_kcal: decimal,
    weight_change_kg: decimal,
    can_review: z.boolean(),
    has_previous_review: z.boolean(),
    review: weekReviewResponseSchema.nullable(),
  })
  .passthrough();
