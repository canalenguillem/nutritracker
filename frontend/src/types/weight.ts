import type { z } from "zod";

import type {
  profileFormSchema,
  profileResponseSchema,
  weightFormSchema,
  weightHistoryResponseSchema,
} from "../schemas/weightSchema";

export type WeightHistoryResponse = z.infer<typeof weightHistoryResponseSchema>;

export type ProfileResponse = z.infer<typeof profileResponseSchema>;

export type WeightFormValues = z.infer<typeof weightFormSchema>;

export type ProfileFormValues = z.infer<typeof profileFormSchema>;

export interface WeightPoint {
  readonly measuredOn: string;
  readonly weightKg: number;
  readonly trendKg: number;
}

export interface WeightHistory {
  readonly points: readonly WeightPoint[];
  readonly latestWeightKg: number | null;
  readonly latestTrendKg: number | null;
  readonly change7DaysKg: number | null;
  readonly change30DaysKg: number | null;
  readonly targetWeightKg: number | null;
  readonly bodyMassIndex: number | null;
}

export interface Profile {
  readonly heightCm: number | null;
  readonly currentWeightKg: number | null;
  readonly targetWeightKg: number | null;
  readonly birthDate: string | null;
  readonly biologicalSex: string | null;
  readonly activityLevel: string;
  readonly primaryGoal: string;
}
