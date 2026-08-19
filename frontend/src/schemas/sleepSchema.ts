import { z } from "zod";

export const sleepQualitySchema = z.enum(["poor", "fair", "good", "very_good"]);

export const sleptNightResponseSchema = z
  .object({
    id: z.string().uuid(),
    started_at: z.string(),
    ended_at: z.string(),
    quality: sleepQualitySchema.nullable(),
    notes: z.string().nullable(),
    hours: z.string(),
  })
  .passthrough();

export const sleepFormSchema = z.object({
  day: z.string().min(1, "Indica el día en que te levantaste."),
  bedTime: z.string().min(1, "Indica a qué hora te acostaste."),
  wakeTime: z.string().min(1, "Indica a qué hora te levantaste."),
  quality: z.union([sleepQualitySchema, z.literal("")]),
  notes: z.string().trim().max(2000, "La nota es demasiado larga."),
});
