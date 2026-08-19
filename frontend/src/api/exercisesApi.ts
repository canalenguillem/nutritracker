import {
  exerciseListResponseSchema,
  exerciseResponseSchema,
} from "../schemas/exerciseSchema";
import { parseAmount } from "../schemas/mealSchema";
import type { Exercise, ExerciseFormValues, ExerciseResponse } from "../types/exercise";
import { httpClient } from "./httpClient";
import { toInstant } from "./mealsApi";

const toExercise = (response: ExerciseResponse): Exercise => ({
  id: response.id,
  activityName: response.activity_name,
  durationMinutes: response.duration_minutes,
  intensity: response.intensity,
  performedAt: response.performed_at,
  estimatedCalories:
    response.estimated_calories === null ? null : Number(response.estimated_calories),
  confirmedCalories:
    response.confirmed_calories === null ? null : Number(response.confirmed_calories),
  countedCalories: Number(response.counted_calories),
  notes: response.notes,
});

const optionalAmount = (value: string): string | null => {
  const trimmed = value.trim();
  return trimmed.length === 0 ? null : parseAmount(trimmed).toFixed(2);
};

export const getExercises = async (day: string): Promise<Exercise[]> => {
  const response = await httpClient.get<unknown>("/exercises", { params: { date: day } });

  return exerciseListResponseSchema.parse(response.data).map(toExercise);
};

export const createExercise = async (values: ExerciseFormValues): Promise<Exercise> => {
  const response = await httpClient.post<unknown>("/exercises", {
    activity_name: values.activityName.trim(),
    duration_minutes: Math.round(parseAmount(values.durationMinutes)),
    intensity: values.intensity,
    performed_at: toInstant(values.day, values.time),
    confirmed_calories: optionalAmount(values.confirmedCalories),
    weight_kg: optionalAmount(values.weightKg),
    notes: values.notes.trim() || null,
  });

  return toExercise(exerciseResponseSchema.parse(response.data));
};

export const getExercise = async (exerciseId: string): Promise<Exercise> => {
  const response = await httpClient.get<unknown>(`/exercises/${exerciseId}`);

  return toExercise(exerciseResponseSchema.parse(response.data));
};

export const updateExercise = async ({
  exerciseId,
  values,
}: {
  readonly exerciseId: string;
  readonly values: ExerciseFormValues;
}): Promise<Exercise> => {
  const response = await httpClient.patch<unknown>(`/exercises/${exerciseId}`, {
    activity_name: values.activityName.trim(),
    duration_minutes: Math.round(parseAmount(values.durationMinutes)),
    intensity: values.intensity,
    performed_at: toInstant(values.day, values.time),
    confirmed_calories: optionalAmount(values.confirmedCalories),
    notes: values.notes.trim() || null,
  });

  return toExercise(exerciseResponseSchema.parse(response.data));
};

export const deleteExercise = async (exerciseId: string): Promise<void> => {
  await httpClient.delete(`/exercises/${exerciseId}`);
};
