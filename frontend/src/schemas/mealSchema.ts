import { z } from "zod";

const MAX_AMOUNT = 999999.99;

export const mealTypeSchema = z.enum(["breakfast", "lunch", "dinner", "snack"]);

export const mealSourceSchema = z.enum(["photo_ai", "manual", "imported"]);

export const mealStatusSchema = z.enum([
  "pending",
  "processing",
  "needs_review",
  "confirmed",
  "failed",
  "cancelled",
]);

export const mealItemResponseSchema = z
  .object({
    id: z.string().uuid(),
    name: z.string(),
    quantity: z.string(),
    unit: z.string(),
    kcal: z.string(),
    protein_g: z.string(),
    fat_g: z.string(),
    carbohydrates_g: z.string(),
    user_confirmed: z.boolean(),
    kcal_from_macros: z.string(),
    macros_disagree: z.boolean(),
  })
  .passthrough();

export const mealResponseSchema = z
  .object({
    id: z.string().uuid(),
    meal_type: mealTypeSchema,
    eaten_at: z.string(),
    source: mealSourceSchema,
    status: mealStatusSchema,
    notes: z.string().nullable(),
    total_kcal: z.string(),
    protein_g: z.string(),
    fat_g: z.string(),
    carbohydrates_g: z.string(),
    items: z.array(mealItemResponseSchema),
  })
  .passthrough();

export const mealListResponseSchema = z.array(mealResponseSchema);

export const dailySummaryResponseSchema = z
  .object({
    log_date: z.string(),
    meal_count: z.number().int(),
    total_kcal: z.string(),
    protein_g: z.string(),
    fat_g: z.string(),
    carbohydrates_g: z.string(),
    exercise_kcal: z.string(),
    exercise_count: z.number().int(),
    net_kcal: z.string(),
    balance_status: z.enum(["estimated", "needs_profile"]),
    resting_kcal: z.string().nullable(),
    living_kcal: z.string().nullable(),
    exercise_above_resting_kcal: z.string().nullable(),
    total_expenditure_kcal: z.string().nullable(),
    balance_kcal: z.string().nullable(),
  })
  .passthrough();

/** Accepts the comma used as a decimal separator in Spanish. */
export const parseAmount = (value: string): number => Number(value.trim().replace(",", "."));

const amountField = (message: string, { allowZero = true } = {}) =>
  z
    .string()
    .trim()
    .min(1, message)
    .refine((value) => {
      const amount = parseAmount(value);
      if (!Number.isFinite(amount) || amount > MAX_AMOUNT) {
        return false;
      }
      return allowZero ? amount >= 0 : amount > 0;
    }, message);

export const mealItemFormSchema = z.object({
  name: z.string().trim().min(1, "Escribe el alimento.").max(180, "El nombre es demasiado largo."),
  quantity: amountField("Indica una cantidad mayor que cero.", { allowZero: false }),
  unit: z.string().trim().min(1, "Indica la unidad.").max(32, "La unidad es demasiado larga."),
  kcal: amountField("Indica las calorías."),
  protein_g: amountField("Indica las proteínas."),
  fat_g: amountField("Indica las grasas."),
  carbohydrates_g: amountField("Indica los carbohidratos."),
});

export const mealFormSchema = z.object({
  mealType: mealTypeSchema,
  day: z.string().min(1, "Indica el día."),
  time: z.string().min(1, "Indica la hora."),
  notes: z.string().trim().max(2000, "La nota es demasiado larga."),
  items: z.array(mealItemFormSchema).min(1, "Añade al menos un alimento."),
});

export const estimatedItemResponseSchema = z
  .object({
    name: z.string(),
    quantity: z.string(),
    unit: z.string(),
    kcal: z.string(),
    protein_g: z.string(),
    fat_g: z.string(),
    carbohydrates_g: z.string(),
    confidence: z.string().nullable(),
    assumptions: z.array(z.string()),
    kcal_from_macros: z.string(),
    macros_disagree: z.boolean(),
  })
  .passthrough();

export const clarificationQuestionResponseSchema = z
  .object({
    key: z.string(),
    question: z.string(),
    options: z.array(z.string()),
  })
  .passthrough();

export const foodEstimateResponseSchema = z
  .object({
    summary: z.string(),
    items: z.array(estimatedItemResponseSchema),
    total_kcal: z.string(),
    questions: z.array(clarificationQuestionResponseSchema),
    confidence: z.string().nullable(),
    warning: z.string(),
    from_cache: z.boolean(),
  })
  .passthrough();
