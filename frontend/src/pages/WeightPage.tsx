import { useState } from "react";
import { Link } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { FormField } from "../components/FormField";
import { PageLoader } from "../components/PageLoader";
import { TargetProjection } from "../components/TargetProjection";
import { WeightChart } from "../components/WeightChart";
import { getMealErrorMessage } from "../features/meals/mealErrors";
import {
  formatBodyMassIndex,
  formatChange,
  formatKilos,
  formatMeasuredOn,
} from "../features/weight/weightLabels";
import { useRecordWeight, useWeightHistory } from "../features/weight/useWeight";
import { weightFormSchema } from "../schemas/weightSchema";
import type { WeightFormValues } from "../types/weight";

const pad = (value: number): string => String(value).padStart(2, "0");

const todayValue = (now: Date): string =>
  `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

const timeValue = (now: Date): string => `${pad(now.getHours())}:${pad(now.getMinutes())}`;

export const WeightPage = () => {
  const history = useWeightHistory();
  const recordWeight = useRecordWeight();
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [now] = useState(() => new Date());

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WeightFormValues>({
    resolver: zodResolver(weightFormSchema),
    defaultValues: {
      weightKg: "",
      day: todayValue(now),
      time: timeValue(now),
      notes: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmissionError(null);

    try {
      await recordWeight.mutateAsync(values);
      reset({ weightKg: "", day: values.day, time: values.time, notes: "" });
    } catch (error) {
      setSubmissionError(getMealErrorMessage(error));
    }
  });

  if (history.isPending) {
    return <PageLoader message="Cargando tu peso…" />;
  }

  const data = history.data;
  const points = data?.points ?? [];
  const recent = [...points].reverse().slice(0, 14);

  return (
    <section className="add-meal">
      <div className="container add-meal__content">
        <div className="add-meal__heading">
          <p className="eyebrow">
            <span aria-hidden="true">✦</span>
            Peso
          </p>
          <h1>Tu peso, día a día</h1>
          <p>
            Pésate cuando quieras y fíjate en la tendencia, no en el número del día. La báscula
            recoge agua y comida además de grasa; la tendencia se queda con lo que importa.
          </p>
        </div>

        {data && data.latestTrendKg !== null ? (
          <article className="dashboard__card">
            <div className="weight-summary">
              <div className="weight-summary__headline">
                <p className="weight-summary__label">Tendencia</p>
                <p className="weight-summary__value">{formatKilos(data.latestTrendKg)}</p>
                {data.latestWeightKg !== null ? (
                  <p className="weight-summary__aside">
                    Última báscula: {formatKilos(data.latestWeightKg)}
                  </p>
                ) : null}
              </div>

              <dl className="weight-summary__stats">
                <div>
                  <dt>7 días</dt>
                  <dd>{data.change7DaysKg === null ? "—" : formatChange(data.change7DaysKg)}</dd>
                </div>
                <div>
                  <dt>30 días</dt>
                  <dd>{data.change30DaysKg === null ? "—" : formatChange(data.change30DaysKg)}</dd>
                </div>
                <div>
                  <dt>Objetivo</dt>
                  <dd>
                    {data.targetWeightKg === null ? "—" : formatKilos(data.targetWeightKg)}
                  </dd>
                </div>
                <div>
                  <dt>IMC estimado</dt>
                  <dd>
                    {data.bodyMassIndex === null ? "—" : formatBodyMassIndex(data.bodyMassIndex)}
                  </dd>
                </div>
              </dl>
            </div>

            <WeightChart
              points={points}
              targetWeightKg={data.targetWeightKg}
              reachesTargetOn={data.projection.reachesTargetOn}
            />

            <TargetProjection
              projection={data.projection}
              targetWeightKg={data.targetWeightKg}
            />

            <p className="dashboard__disclaimer">
              El IMC es una estimación y no dice nada sobre tu composición corporal.
              {data.targetWeightKg === null
                ? " Puedes fijar tu objetivo y tu estatura en el perfil."
                : ""}
            </p>
          </article>
        ) : null}

        <form className="add-meal__form" onSubmit={(event) => void onSubmit(event)} noValidate>
          {submissionError ? (
            <p className="auth-form__error" role="alert">
              {submissionError}
            </p>
          ) : null}

          <div className="add-meal__when">
            <FormField
              label="Peso (kg)"
              type="text"
              inputMode="decimal"
              placeholder="80,4"
              error={errors.weightKg?.message}
              {...register("weightKg")}
            />
            <FormField label="Día" type="date" error={errors.day?.message} {...register("day")} />
            <FormField
              label="Hora"
              type="time"
              error={errors.time?.message}
              {...register("time")}
            />
          </div>

          <div className="form-field">
            <label className="form-field__label" htmlFor="weight-notes">
              Notas
            </label>
            <textarea
              className="form-field__input form-field__input--area"
              id="weight-notes"
              rows={2}
              placeholder="En ayunas, después de entrenar…"
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
              {isSubmitting ? "Guardando…" : "Guardar peso"}
            </button>
            <Link className="text-link" to="/dashboard">
              Volver al panel
            </Link>
          </div>
        </form>

        {recent.length > 0 ? (
          <article className="dashboard__card">
            <h2>Últimos registros</h2>
            <ul className="weight-list">
              {recent.map((point) => (
                <li key={point.measuredOn}>
                  <span className="weight-list__day">{formatMeasuredOn(point.measuredOn)}</span>
                  <span className="weight-list__weight">{formatKilos(point.weightKg)}</span>
                  <span className="weight-list__trend">
                    tendencia {formatKilos(point.trendKg)}
                  </span>
                </li>
              ))}
            </ul>
          </article>
        ) : (
          <p className="dashboard__placeholder">
            Aún no hay registros. El primero fija el punto de partida; la tendencia empieza a
            tener sentido a los pocos días.
          </p>
        )}
      </div>
    </section>
  );
};
