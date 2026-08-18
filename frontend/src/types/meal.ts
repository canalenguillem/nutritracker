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

/** Energy the macronutrients alone describe, and whether it contradicts the total. */
export interface MacroCheck {
  readonly kcalFromMacros: number;
  readonly macrosDisagree: boolean;
}

export interface MealItem extends Macros, MacroCheck {
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
  readonly exerciseKcal: number;
  readonly exerciseCount: number;
  /** Food minus exercise. On its own not a deficit; see the balance. */
  readonly netKcal: number;
  readonly balanceStatus: "estimated" | "needs_profile";
  readonly restingKcal: number | null;
  readonly livingKcal: number | null;
  /** What the training added above resting, which daily living already covers. */
  readonly exerciseAboveRestingKcal: number | null;
  readonly totalExpenditureKcal: number | null;
  readonly balanceKcal: number | null;
}

export interface EstimatedItem extends Macros, MacroCheck {
  readonly name: string;
  readonly quantity: number;
  readonly unit: string;
  readonly confidence: number | null;
  readonly assumptions: readonly string[];
}

export interface ClarificationQuestion {
  readonly key: string;
  readonly question: string;
  readonly options: readonly string[];
}

export interface FoodEstimate {
  readonly summary: string;
  readonly items: readonly EstimatedItem[];
  readonly totalKcal: number;
  readonly questions: readonly ClarificationQuestion[];
  readonly confidence: number | null;
  readonly warning: string;
  readonly fromCache: boolean;
}
