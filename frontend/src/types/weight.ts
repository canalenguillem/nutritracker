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

export type ProjectionStatus =
  | "reachable"
  | "already_there"
  | "wrong_way"
  | "too_flat"
  | "not_enough_data"
  | "too_far";

export interface TrendProjection {
  readonly status: ProjectionStatus;
  readonly kgPerWeek: number | null;
  readonly reachesTargetOn: string | null;
  readonly daysToTarget: number | null;
}

export interface WeightHistory {
  readonly points: readonly WeightPoint[];
  readonly latestWeightKg: number | null;
  readonly latestTrendKg: number | null;
  readonly change7DaysKg: number | null;
  readonly change30DaysKg: number | null;
  readonly targetWeightKg: number | null;
  readonly bodyMassIndex: number | null;
  readonly projection: TrendProjection;
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
