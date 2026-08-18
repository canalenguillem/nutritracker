import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createWeight,
  getProfile,
  getWeightHistory,
  updateProfile,
} from "../../api/weightsApi";

export const weightKeys = {
  history: ["weights", "history"] as const,
  profile: ["profile"] as const,
};

export const useWeightHistory = () =>
  useQuery({ queryKey: weightKeys.history, queryFn: getWeightHistory });

export const useProfile = () =>
  useQuery({ queryKey: weightKeys.profile, queryFn: getProfile });

export const useRecordWeight = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createWeight,
    onSuccess: async () => {
      // A reading changes the profile weight as well as the history.
      await queryClient.invalidateQueries({ queryKey: weightKeys.history });
      await queryClient.invalidateQueries({ queryKey: weightKeys.profile });
    },
  });
};

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: weightKeys.profile });
      // The body mass index depends on the height.
      await queryClient.invalidateQueries({ queryKey: weightKeys.history });
    },
  });
};
