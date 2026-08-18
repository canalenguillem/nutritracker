import { z } from "zod";

import { parseAmount } from "./mealSchema";

const MIN_WEIGHT = 20;
const MAX_WEIGHT = 500;

export const weightEntryResponseSchema = z
  .object({
    id: z.string().uuid(),
    weight_kg: z.string(),
    measured_at: z.string(),
    notes: z.string().nullable(),
  })
  .passthrough();

export const weightPointResponseSchema = z
  .object({
    measured_on: z.string(),
    weight_kg: z.string(),
    trend_kg: z.string(),
  })
  .passthrough();

export const weightHistoryResponseSchema = z
  .object({
    points: z.array(weightPointResponseSchema),
    latest_weight_kg: z.string().nullable(),
    latest_trend_kg: z.string().nullable(),
    change_7_days_kg: z.string().nullable(),
    change_30_days_kg: z.string().nullable(),
    target_weight_kg: z.string().nullable(),
    body_mass_index: z.string().nullable(),
  })
  .passthrough();

export const profileResponseSchema = z
  .object({
    id: z.string().uuid(),
    height_cm: z.string().nullable(),
    current_weight_kg: z.string().nullable(),
    target_weight_kg: z.string().nullable(),
    birth_date: z.string().nullable(),
    biological_sex: z.string().nullable(),
    activity_level: z.string(),
    primary_goal: z.string(),
  })
  .passthrough();

export const weightFormSchema = z.object({
  weightKg: z
    .string()
    .trim()
    .min(1, "Indica tu peso.")
    .refine((value) => {
      const weight = parseAmount(value);
      return Number.isFinite(weight) && weight > MIN_WEIGHT && weight <= MAX_WEIGHT;
    }, "Indica un peso en kilos válido."),
  day: z.string().min(1, "Indica el día."),
  time: z.string().min(1, "Indica la hora."),
  notes: z.string().trim().max(2000, "La nota es demasiado larga."),
});

const optionalMeasure = (message: string, minimum: number, maximum: number) =>
  z
    .string()
    .trim()
    .refine((value) => {
      if (value.length === 0) {
        return true;
      }
      const amount = parseAmount(value);
      return Number.isFinite(amount) && amount > minimum && amount <= maximum;
    }, message);

export const profileFormSchema = z.object({
  heightCm: optionalMeasure("Indica una estatura válida en centímetros.", 50, 260),
  targetWeightKg: optionalMeasure("Indica un peso objetivo válido.", 20, 500),
  birthDate: z.string(),
  biologicalSex: z.enum(["female", "male", "unspecified"]),
  activityLevel: z.enum(["sedentary", "light", "moderate", "active", "very_active"]),
  primaryGoal: z.enum(["lose_weight", "maintain_weight", "gain_muscle"]),
});
