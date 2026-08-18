import type { z } from "zod";

import type {
  exerciseFormSchema,
  exerciseResponseSchema,
} from "../schemas/exerciseSchema";

export type ExerciseResponse = z.infer<typeof exerciseResponseSchema>;

export type ExerciseFormValues = z.infer<typeof exerciseFormSchema>;

export type ExerciseIntensity = ExerciseResponse["intensity"];

export interface Exercise {
  readonly id: string;
  readonly activityName: string;
  readonly durationMinutes: number;
  readonly intensity: ExerciseIntensity;
  readonly performedAt: string;
  readonly estimatedCalories: number | null;
  readonly confirmedCalories: number | null;
  readonly countedCalories: number;
  readonly notes: string | null;
}
