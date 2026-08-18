import { z } from "zod";

import { parseAmount } from "./mealSchema";

const MAX_CALORIES = 99999.99;
const MAX_MINUTES = 24 * 60;

export const exerciseIntensitySchema = z.enum(["low", "moderate", "high", "very_high"]);

export const exerciseSourceSchema = z.enum(["manual", "device", "imported"]);

export const exerciseResponseSchema = z
  .object({
    id: z.string().uuid(),
    activity_name: z.string(),
    duration_minutes: z.number().int(),
    intensity: exerciseIntensitySchema,
    source: exerciseSourceSchema,
    performed_at: z.string(),
    estimated_calories: z.string().nullable(),
    confirmed_calories: z.string().nullable(),
    counted_calories: z.string(),
    notes: z.string().nullable(),
  })
  .passthrough();

export const exerciseListResponseSchema = z.array(exerciseResponseSchema);

const optionalAmount = (message: string, max: number) =>
  z
    .string()
    .trim()
    .refine((value) => {
      if (value.length === 0) {
        return true;
      }
      const amount = parseAmount(value);
      return Number.isFinite(amount) && amount >= 0 && amount <= max;
    }, message);

export const exerciseFormSchema = z.object({
  activityName: z
    .string()
    .trim()
    .min(1, "Escribe la actividad.")
    .max(120, "El nombre es demasiado largo."),
  durationMinutes: z
    .string()
    .trim()
    .min(1, "Indica cuánto duró.")
    .refine((value) => {
      const minutes = parseAmount(value);
      return Number.isInteger(minutes) && minutes > 0 && minutes <= MAX_MINUTES;
    }, "Indica los minutos, entre 1 y 1440."),
  intensity: exerciseIntensitySchema,
  day: z.string().min(1, "Indica el día."),
  time: z.string().min(1, "Indica la hora."),
  confirmedCalories: optionalAmount("Indica unas calorías válidas.", MAX_CALORIES),
  weightKg: optionalAmount("Indica un peso válido.", 500),
  notes: z.string().trim().max(2000, "La nota es demasiado larga."),
});
