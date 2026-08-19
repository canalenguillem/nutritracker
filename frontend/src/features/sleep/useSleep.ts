import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createNight,
  deleteNight,
  getNight,
  getNightById,
  updateNight,
} from "../../api/sleepApi";

export const sleepKeys = {
  night: (day: string) => ["sleep", day] as const,
  one: (entryId: string) => ["sleep", "one", entryId] as const,
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

export const useNightById = (entryId: string | undefined) =>
  useQuery({
    queryKey: sleepKeys.one(entryId ?? ""),
    queryFn: () => getNightById(entryId as string),
    enabled: Boolean(entryId),
  });

export const useUpdateNight = () => {
  const resetCache = useSleepCacheReset();

  return useMutation({ mutationFn: updateNight, onSuccess: resetCache });
};
