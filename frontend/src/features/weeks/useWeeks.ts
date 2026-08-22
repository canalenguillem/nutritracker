import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getWeek, reviewWeek } from "../../api/weeksApi";

export const weekKeys = {
  one: (week: string) => ["weeks", week] as const,
};

export const useWeek = (week: string | undefined) =>
  useQuery({
    queryKey: weekKeys.one(week ?? ""),
    queryFn: () => getWeek(week as string),
    enabled: Boolean(week),
  });

export const useReviewWeek = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: reviewWeek,
    onSuccess: (week) => {
      // The answer that came back is the week itself, so it can be kept
      // instead of being asked for again.
      queryClient.setQueryData(weekKeys.one(week.weekStart), week);
    },
  });
};
