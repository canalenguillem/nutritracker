import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createNight, deleteNight, getNight } from "../../api/sleepApi";

export const sleepKeys = {
  night: (day: string) => ["sleep", day] as const,
};

export const useNight = (day: string | undefined) =>
  useQuery({
    queryKey: sleepKeys.night(day ?? ""),
    queryFn: () => getNight(day as string),
    enabled: Boolean(day),
  });

const useSleepCacheReset = () => {
  const queryClient = useQueryClient();

  return () => queryClient.invalidateQueries({ queryKey: ["sleep"] });
};

export const useRecordNight = () => {
  const resetCache = useSleepCacheReset();

  return useMutation({ mutationFn: createNight, onSuccess: resetCache });
};

export const useDeleteNight = () => {
  const resetCache = useSleepCacheReset();

  return useMutation({ mutationFn: deleteNight, onSuccess: resetCache });
};
