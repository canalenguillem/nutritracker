import { parseAmount } from "../schemas/mealSchema";
import {
  profileResponseSchema,
  weightHistoryResponseSchema,
} from "../schemas/weightSchema";
import type {
  Profile,
  ProfileFormValues,
  ProfileResponse,
  WeightFormValues,
  WeightHistory,
  WeightHistoryResponse,
} from "../types/weight";
import { httpClient } from "./httpClient";
import { toInstant } from "./mealsApi";

const optionalNumber = (value: string | null): number | null =>
  value === null ? null : Number(value);

const optionalAmount = (value: string): string | null => {
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : parseAmount(trimmed).toFixed(2);
};

const toHistory = (response: WeightHistoryResponse): WeightHistory => ({
  points: response.points.map((point) => ({
    measuredOn: point.measured_on,
    weightKg: Number(point.weight_kg),
    trendKg: Number(point.trend_kg),
  })),
  latestWeightKg: optionalNumber(response.latest_weight_kg),
  latestTrendKg: optionalNumber(response.latest_trend_kg),
  change7DaysKg: optionalNumber(response.change_7_days_kg),
  change30DaysKg: optionalNumber(response.change_30_days_kg),
  targetWeightKg: optionalNumber(response.target_weight_kg),
  bodyMassIndex: optionalNumber(response.body_mass_index),
  projection: {
    status: response.projection.status,
    kgPerWeek: optionalNumber(response.projection.kg_per_week),
    reachesTargetOn: response.projection.reaches_target_on,
    daysToTarget: response.projection.days_to_target,
  },
});

const toProfile = (response: ProfileResponse): Profile => ({
  heightCm: optionalNumber(response.height_cm),
  currentWeightKg: optionalNumber(response.current_weight_kg),
  targetWeightKg: optionalNumber(response.target_weight_kg),
  birthDate: response.birth_date,
  biologicalSex: response.biological_sex,
  activityLevel: response.activity_level,
  primaryGoal: response.primary_goal,
  dailyCalorieTarget: optionalNumber(response.daily_calorie_target),
});

export const getWeightHistory = async (): Promise<WeightHistory> => {
  const response = await httpClient.get<unknown>("/weights/history");

  return toHistory(weightHistoryResponseSchema.parse(response.data));
};

export const createWeight = async (values: WeightFormValues): Promise<void> => {
  await httpClient.post("/weights", {
    weight_kg: parseAmount(values.weightKg).toFixed(2),
    measured_at: toInstant(values.day, values.time),
    notes: values.notes.trim() || null,
  });
};

export const deleteWeight = async (entryId: string): Promise<void> => {
  await httpClient.delete(`/weights/${entryId}`);
};

export const getProfile = async (): Promise<Profile> => {
  const response = await httpClient.get<unknown>("/profile");

  return toProfile(profileResponseSchema.parse(response.data));
};

export const updateProfile = async (values: ProfileFormValues): Promise<Profile> => {
  const response = await httpClient.patch<unknown>("/profile", {
    height_cm: optionalAmount(values.heightCm),
    target_weight_kg: optionalAmount(values.targetWeightKg),
    birth_date: values.birthDate.trim() || null,
    biological_sex: values.biologicalSex,
    activity_level: values.activityLevel,
    primary_goal: values.primaryGoal,
    daily_calorie_target: optionalAmount(values.dailyCalorieTarget),
  });

  return toProfile(profileResponseSchema.parse(response.data));
};
