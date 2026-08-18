import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { intensityOptions } from "../features/exercises/exerciseLabels";
import { useCreateExercise } from "../features/exercises/useExercises";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import { exerciseFormSchema } from "../schemas/exerciseSchema";
import type { ExerciseFormValues } from "../types/exercise";

const pad = (value: number): string => String(value).padStart(2, "0");

const todayValue = (now: Date): string =>
  `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

const timeValue = (now: Date): string => `${pad(now.getHours())}:${pad(now.getMinutes())}`;

export const AddExercisePage = () => {
  const navigate = useNavigate();
  const createExercise = useCreateExercise();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [now] = useState(() => new Date());

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ExerciseFormValues>({
    resolver: zodResolver(exerciseFormSchema),
    defaultValues: {
      activityName: "",
      durationMinutes: "",
      intensity: "moderate",
      day: todayValue(now),
      time: timeValue(now),
      confirmedCalories: "",
      weightKg: "",
      notes: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      await createExercise.mutateAsync(values);
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
            Actividad
          </p>
          <h1>Añade ejercicio</h1>
          <p>
            Anota qué has hecho y cuánto ha durado. Estimamos el gasto, pero si tu reloj o la
            máquina te dan otra cifra, la tuya manda.
          </p>
        </div>

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          <FormField
            label="Actividad"
            type="text"
            placeholder="Brooklyn Fitboxing"
            error={errors.activityName?.message}
            {...register("activityName")}
          />

          <div className="add-meal__when">
            <FormField
              label="Duración (minutos)"
              type="text"
              inputMode="numeric"
              placeholder="47"
              error={errors.durationMinutes?.message}
              {...register("durationMinutes")}
            />

            <div className="form-field">
              <label className="form-field__label" htmlFor="exercise-intensity">
                Intensidad
              </label>
              <select
                className="form-field__input"
                id="exercise-intensity"
                {...register("intensity")}
              >
                {intensityOptions.map((option) => (
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

          <div className="add-meal__when">
            <FormField
              label="Calorías (opcional)"
              type="text"
              inputMode="decimal"
              hint="Si tu reloj o la máquina te dan una cifra, ponla aquí."
              error={errors.confirmedCalories?.message}
              {...register("confirmedCalories")}
            />

            <FormField
              label="Tu peso en kg (opcional)"
              type="text"
              inputMode="decimal"
              hint="Sin el peso no podemos estimar el gasto. Se recuerda para la próxima."
              error={errors.weightKg?.message}
              {...register("weightKg")}
            />
          </div>

          <div className="form-field">
            <label className="form-field__label" htmlFor="exercise-notes">
              Notas
            </label>
            <textarea
              className="form-field__input form-field__input--area"
              id="exercise-notes"
              rows={3}
              placeholder="Clase de los martes, guantes nuevos…"
              {...register("notes")}
            />
            {errors.notes ? (
              <p className="form-field__error" role="alert">
                {errors.notes.message}
              </p>
            ) : null}
          </div>

          <p className="dashboard__disclaimer">
            El gasto es una estimación a partir de la actividad, la intensidad, el tiempo y tu
            peso. No sustituye una medición.
          </p>

          <div className="add-meal__actions">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando…" : "Guardar ejercicio"}
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
