import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createMeal,
  deleteMeal,
  describeMeal,
  getDailySummary,
  getHistory,
  getMeals,
  getRecentMeals,
} from "../../api/mealsApi";

export const mealKeys = {
  summary: (day?: string) => ["meals", "summary", day ?? "today"] as const,
  day: (day: string) => ["meals", "day", day] as const,
  recent: (query: string) => ["meals", "recent", query] as const,
  history: (days: number) => ["meals", "history", days] as const,
};

/** Without a date the API answers for today in the account's own timezone. */
export const useDailySummary = (day?: string) =>
  useQuery({
    queryKey: mealKeys.summary(day),
    queryFn: () => getDailySummary(day),
  });

export const useDayMeals = (day: string | undefined) =>
  useQuery({
    queryKey: mealKeys.day(day ?? ""),
    queryFn: () => getMeals(day as string),
    enabled: Boolean(day),
  });

const useMealCacheReset = () => {
  const queryClient = useQueryClient();

  return () => queryClient.invalidateQueries({ queryKey: ["meals"] });
};

export const useCreateMeal = () => {
  const resetMealCache = useMealCacheReset();

  return useMutation({
    mutationFn: createMeal,
    onSuccess: resetMealCache,
  });
};

export const useDeleteMeal = () => {
  const resetMealCache = useMealCacheReset();

  return useMutation({
    mutationFn: deleteMeal,
    onSuccess: resetMealCache,
  });
};

export const useDescribeMeal = () => useMutation({ mutationFn: describeMeal });

export const useRecentMeals = (query: string) =>
  useQuery({
    queryKey: mealKeys.recent(query.trim()),
    queryFn: () => getRecentMeals(query),
    staleTime: 60_000,
  });

export const useHistory = (days: number) =>
  useQuery({ queryKey: mealKeys.history(days), queryFn: () => getHistory(days) });
