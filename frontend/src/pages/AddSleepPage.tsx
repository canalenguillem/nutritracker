import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { PageLoader } from "../components/PageLoader";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import { qualityOptions } from "../features/sleep/sleepLabels";
import { useNightById, useRecordNight, useUpdateNight } from "../features/sleep/useSleep";
import { sleepFormSchema } from "../schemas/sleepSchema";
import type { SleepFormValues } from "../types/sleep";

const pad = (value: number): string => String(value).padStart(2, "0");

const todayValue = (now: Date): string =>
  `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

export const AddSleepPage = () => {
  const navigate = useNavigate();
  const { entryId } = useParams();
  const isEditing = Boolean(entryId);
  const existing = useNightById(entryId);
  const recordNight = useRecordNight();
  const updateNight = useUpdateNight();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [now] = useState(() => new Date());

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SleepFormValues>({
    resolver: zodResolver(sleepFormSchema),
    defaultValues: {
      day: todayValue(now),
      bedTime: "23:30",
      wakeTime: "07:00",
      quality: "",
      notes: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      if (entryId) {
        await updateNight.mutateAsync({ entryId, values });
      } else {
        await recordNight.mutateAsync(values);
      }
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmissionError(getMealErrorMessage(error));
    }
  });

  // Fill the form from the night being corrected.
  useEffect(() => {
    const night = existing.data;
    if (!night) {
      return;
    }

    const started = new Date(night.startedAt);
    const ended = new Date(night.endedAt);
    const pad2 = (value: number): string => String(value).padStart(2, "0");

    reset({
      day: `${ended.getFullYear()}-${pad2(ended.getMonth() + 1)}-${pad2(ended.getDate())}`,
      bedTime: `${pad2(started.getHours())}:${pad2(started.getMinutes())}`,
      wakeTime: `${pad2(ended.getHours())}:${pad2(ended.getMinutes())}`,
      quality: night.quality ?? "",
      notes: night.notes ?? "",
    });
  }, [existing.data, reset]);

  if (isEditing && existing.isPending) {
    return <PageLoader message="Cargando la noche…" />;
  }

  return (
    <section className="add-meal">
      <div className="container add-meal__content">
        <div className="add-meal__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            {isEditing ? "Corregir" : "Descanso"}
          </p>
          <h1>{isEditing ? "Edita la noche" : "Añade tu sueño"}</h1>
          <p>
            Apunta a qué hora te acostaste y a qué hora te levantaste. La noche se guarda en el
            día en que te despiertas, que es al que afecta.
          </p>
        </div>

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          <div className="add-meal__when">
            <FormField
              label="Día en que te levantaste"
              type="date"
              error={errors.day?.message}
              {...register("day")}
            />
            <FormField
              label="Me acosté a las"
              type="time"
              hint="Si fue antes de medianoche, contamos la noche anterior."
              error={errors.bedTime?.message}
              {...register("bedTime")}
            />
            <FormField
              label="Me levanté a las"
              type="time"
              error={errors.wakeTime?.message}
              {...register("wakeTime")}
            />

            <div className="form-field">
              <label className="form-field__label" htmlFor="sleep-quality">
                Qué tal dormiste
              </label>
              <select className="form-field__input" id="sleep-quality" {...register("quality")}>
                {qualityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-field">
            <label className="form-field__label" htmlFor="sleep-notes">
              Notas
            </label>
            <textarea
              className="form-field__input form-field__input--area"
              id="sleep-notes"
              rows={2}
              placeholder="Me desperté un par de veces, cené tarde…"
              {...register("notes")}
            />
            {errors.notes ? (
              <p className="form-field__error" role="alert">
                {errors.notes.message}
              </p>
            ) : null}
          </div>

          <p className="dashboard__disclaimer">
            Guardamos las horas tal y como las escribes. No estimamos nada del sueño: si te
            despertaste a media noche, anótalo y réstalo tú.
          </p>

          <div className="add-meal__actions">
            <button className="button button--primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Guardando…" : isEditing ? "Guardar cambios" : "Guardar sueño"}
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
