import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createExercise,
  deleteExercise,
  getExercise,
  getExercises,
  updateExercise,
} from "../../api/exercisesApi";

export const exerciseKeys = {
  day: (day: string) => ["exercises", "day", day] as const,
  one: (exerciseId: string) => ["exercises", "one", exerciseId] as const,
};

export const useDayExercises = (day: string | undefined) =>
  useQuery({
    queryKey: exerciseKeys.day(day ?? ""),
    queryFn: () => getExercises(day as string),
    enabled: Boolean(day),
  });

const useExerciseCacheReset = () => {
  const queryClient = useQueryClient();

  return async () => {
    // The daily summary counts the exercise, so it has to be refreshed too.
    await queryClient.invalidateQueries({ queryKey: ["exercises"] });
    await queryClient.invalidateQueries({ queryKey: ["meals"] });
  };
};

export const useCreateExercise = () => {
  const resetCaches = useExerciseCacheReset();

  return useMutation({ mutationFn: createExercise, onSuccess: resetCaches });
};

export const useDeleteExercise = () => {
  const resetCaches = useExerciseCacheReset();

  return useMutation({ mutationFn: deleteExercise, onSuccess: resetCaches });
};

export const useExercise = (exerciseId: string | undefined) =>
  useQuery({
    queryKey: exerciseKeys.one(exerciseId ?? ""),
    queryFn: () => getExercise(exerciseId as string),
    enabled: Boolean(exerciseId),
  });

export const useUpdateExercise = () => {
  const resetCaches = useExerciseCacheReset();

  return useMutation({ mutationFn: updateExercise, onSuccess: resetCaches });
};
