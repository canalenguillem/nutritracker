import type { z } from "zod";

import type {
  dailySummaryResponseSchema,
  mealFormSchema,
  mealItemFormSchema,
  mealItemResponseSchema,
  mealResponseSchema,
} from "../schemas/mealSchema";

export type MealResponse = z.infer<typeof mealResponseSchema>;

export type MealItemResponse = z.infer<typeof mealItemResponseSchema>;

export type DailySummaryResponse = z.infer<typeof dailySummaryResponseSchema>;

export type MealFormValues = z.infer<typeof mealFormSchema>;

export type MealItemFormValues = z.infer<typeof mealItemFormSchema>;

export type MealType = MealResponse["meal_type"];

export type MealSource = MealResponse["source"];

export interface Macros {
  readonly kcal: number;
  readonly proteinG: number;
  readonly fatG: number;
  readonly carbohydratesG: number;
}

export interface MealItem extends Macros {
  readonly id: string;
  readonly name: string;
  readonly quantity: number;
  readonly unit: string;
}

export interface Meal extends Macros {
  readonly id: string;
  readonly mealType: MealType;
  readonly eatenAt: string;
  readonly source: MealSource;
  readonly notes: string | null;
  readonly items: readonly MealItem[];
}

export interface DailySummary extends Macros {
  readonly logDate: string;
  readonly mealCount: number;
}
