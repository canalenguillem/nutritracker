import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useFieldArray, useForm } from "react-hook-form";

import { EstimatePanel } from "../components/EstimatePanel";
import { FormField } from "../components/FormField";
import { mealTypeOptions } from "../features/meals/mealLabels";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import { useCreateMeal, useDescribeMeal } from "../features/meals/useMeals";
import { mealFormSchema } from "../schemas/mealSchema";
import type { FoodEstimate, MealFormValues, MealItemFormValues } from "../types/meal";

const EMPTY_ITEM: MealItemFormValues = {
  name: "",
  quantity: "",
  unit: "g",
  kcal: "",
  protein_g: "",
  fat_g: "",
  carbohydrates_g: "",
};

/** The form accepts the comma, so write the estimate the way it reads in Spanish. */
const toFieldValue = (value: number): string => String(value).replace(".", ",");

const toFormItems = (estimate: FoodEstimate): MealItemFormValues[] =>
  estimate.items.map((item) => ({
    name: item.name,
    quantity: toFieldValue(item.quantity),
    unit: item.unit,
    kcal: toFieldValue(item.kcal),
    protein_g: toFieldValue(item.proteinG),
    fat_g: toFieldValue(item.fatG),
    carbohydrates_g: toFieldValue(item.carbohydratesG),
  }));

const pad = (value: number): string => String(value).padStart(2, "0");

const todayValue = (now: Date): string =>
  `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

const timeValue = (now: Date): string => `${pad(now.getHours())}:${pad(now.getMinutes())}`;

export const AddMealPage = () => {
  const navigate = useNavigate();
  const createMeal = useCreateMeal();
  const describeMeal = useDescribeMeal();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [estimateError, setEstimateError] = useState<string | null>(null);
  const [estimate, setEstimate] = useState<FoodEstimate | null>(null);
  const [description, setDescription] = useState("");
  const [now] = useState(() => new Date());

  const {
    control,
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<MealFormValues>({
    resolver: zodResolver(mealFormSchema),
    defaultValues: {
      mealType: "lunch",
      day: todayValue(now),
      time: timeValue(now),
      notes: "",
      items: [EMPTY_ITEM],
    },
  });

  const { fields, append, remove, replace } = useFieldArray({ control, name: "items" });

  const onEstimate = async () => {
    setEstimateError(null);

    try {
      const result = await describeMeal.mutateAsync(description);
      setEstimate(result);
      replace(toFormItems(result));
    } catch (error) {
      setEstimate(null);
      setEstimateError(getMealErrorMessage(error));
    }
  };

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      await createMeal.mutateAsync(values);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmissionError(getMealErrorMessage(error));
    }
  });

  return (
    <section className="add-meal">
      <div className="container add-meal__content">
        <div className="add-meal__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            Registro manual
          </p>
          <h1>Añade una comida</h1>
          <p>
            Escribe lo que has comido y sus valores. Nada se estima por ti: los totales salen de
            lo que introduzcas.
          </p>
        </div>

        <section className="describe" aria-label="Describir la comida">
          <label className="form-field__label" htmlFor="meal-description">
            ¿No sabes los valores? Describe lo que has comido
          </label>
          <p className="describe__hint">
            Por ejemplo: «un café con nata» o «dos tostadas con aceite y tomate».
          </p>
          <div className="describe__row">
            <input
              className="form-field__input"
              id="meal-description"
              type="text"
              value={description}
              placeholder="Un café con nata"
              onChange={(event) => setDescription(event.target.value)}
              disabled={describeMeal.isPending}
            />
            <button
              className="button button--secondary"
              type="button"
              onClick={() => void onEstimate()}
              disabled={describeMeal.isPending || description.trim().length === 0}
            >
              {describeMeal.isPending ? "Estimando…" : "Estimar valores"}
            </button>
          </div>
          {estimateError ? (
            <p className="auth-form__error" role="alert">
              {estimateError}
            </p>
          ) : null}
        </section>

        {estimate ? <EstimatePanel estimate={estimate} /> : null}

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          <div className="add-meal__when">
            <div className="form-field">
              <label className="form-field__label" htmlFor="meal-type">
                Tipo de comida
              </label>
              <select className="form-field__input" id="meal-type" {...register("mealType")}>
                {mealTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <FormField label="Día" type="date" error={errors.day?.message} {...register("day")} />
            <FormField
              label="Hora"
              type="time"
              error={errors.time?.message}
              {...register("time")}
            />
          </div>

          <div className="add-meal__items">
            <div className="add-meal__items-head">
              <h2>Alimentos</h2>
              <button
                className="button button--secondary button--small"
                type="button"
                onClick={() => append(EMPTY_ITEM)}
              >
                Añadir alimento
              </button>
            </div>

            {fields.map((field, index) => (
              <fieldset className="meal-item-fields" key={field.id}>
                <legend>Alimento {index + 1}</legend>

                <div className="meal-item-fields__identity">
                  <FormField
                    label="Alimento"
                    type="text"
                    placeholder="Arroz integral"
                    error={errors.items?.[index]?.name?.message}
                    {...register(`items.${index}.name`)}
                  />
                  <FormField
                    label="Cantidad"
                    type="text"
                    inputMode="decimal"
                    placeholder="150"
                    error={errors.items?.[index]?.quantity?.message}
                    {...register(`items.${index}.quantity`)}
                  />
                  <FormField
                    label="Unidad"
                    type="text"
                    placeholder="g"
                    error={errors.items?.[index]?.unit?.message}
                    {...register(`items.${index}.unit`)}
                  />
                </div>

                <div className="meal-item-fields__macros">
                  <FormField
                    label="Calorías (kcal)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.kcal?.message}
                    {...register(`items.${index}.kcal`)}
                  />
                  <FormField
                    label="Proteínas (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.protein_g?.message}
                    {...register(`items.${index}.protein_g`)}
                  />
                  <FormField
                    label="Carbohidratos (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.carbohydrates_g?.message}
                    {...register(`items.${index}.carbohydrates_g`)}
                  />
                  <FormField
                    label="Grasas (g)"
                    type="text"
                    inputMode="decimal"
                    error={errors.items?.[index]?.fat_g?.message}
                    {...register(`items.${index}.fat_g`)}
                  />
                </div>

                {fields.length > 1 ? (
                  <button
                    className="meal-item-fields__remove"
                    type="button"
                    onClick={() => remove(index)}
                  >
                    Quitar este alimento
                  </button>
                ) : null}
              </fieldset>
            ))}
          </div>

          <div className="form-field">
            <label className="form-field__label" htmlFor="meal-notes">
              Notas
            </label>
            <textarea
              className="form-field__input form-field__input--area"
              id="meal-notes"
              rows={3}
              placeholder="Con aceite de oliva, poca sal…"
              {...register("notes")}
            />
            {errors.notes ? (
              <p className="form-field__error" role="alert">
                {errors.notes.message}
              </p>
            ) : null}
          </div>

          <div className="add-meal__actions">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando…" : "Guardar comida"}
            </button>
            <Link className="text-link" to="/dashboard">
              Cancelar
            </Link>
          </div>
        </form>
      </div>
    </section>
  );
};
