import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createExercise, deleteExercise, getExercises } from "../../api/exercisesApi";

export const exerciseKeys = {
  day: (day: string) => ["exercises", "day", day] as const,
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
