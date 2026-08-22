import { getMealErrorMessage } from "../features/meals/mealErrors";
import { formatEnergy, fromIsoDay } from "../features/meals/mealLabels";
import { useReviewWeek, useWeek } from "../features/weeks/useWeeks";
import type { Week } from "../types/week";

interface WeekSummaryProps {
  /** The Monday of the week being read. */
  readonly weekStart: string;
}

const formatGenerated = (instant: string): string =>
  new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(instant));

const formatHours = (hours: number): string =>
  `${hours.toFixed(1).replace(".", ",")} h`;

const formatWeight = (kilos: number): string => {
  const rounded = Math.abs(kilos).toFixed(1).replace(".", ",");

  return `${kilos > 0 ? "+" : kilos < 0 ? "−" : ""}${rounded} kg`;
};

/** Seven days recorded and three days recorded are not the same week. */
const recordedLabel = (days: number): string =>
  `${days} ${days === 1 ? "día" : "días"} de 7`;

const dayCount = (week: Week): number =>
  week.days.filter((day) => day.hasFood || day.hasExercise || day.sleepHours !== null).length;

const weekTitle = (week: Week): string => {
  const short = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long" });

  return `${short.format(fromIsoDay(week.weekStart))} – ${short.format(fromIsoDay(week.weekEnd))}`;
};

export const WeekSummary = ({ weekStart }: WeekSummaryProps) => {
  const weekQuery = useWeek(weekStart);
  const review = useReviewWeek();

  if (weekQuery.isPending || !weekQuery.data) {
    return null;
  }

  const week = weekQuery.data;
  const written = week.review;
  const hasSomething = dayCount(week) > 0;
  // A closed week is written up once and keeps what it said, so that the week
  // after it has something fixed to be compared against.
  const isClosed = written?.isFinal === true;
  const isBusy = review.isPending && review.variables === weekStart;

  return (
    <article className="week-summary">
      <div className="week-summary__head">
        <div>
          <h2>Resumen de la semana</h2>
          <p className="week-summary__range">
            {weekTitle(week)} · {recordedLabel(dayCount(week))}
            {week.isComplete ? "" : " · semana en curso"}
          </p>
        </div>
        {week.canReview && hasSomething && !isClosed ? (
          <button
            className="button button--primary button--small"
            type="button"
            onClick={() => review.mutate(weekStart)}
            disabled={isBusy}
          >
            {isBusy ? "Analizando…" : written ? "Actualizar resumen" : "Generar resumen"}
          </button>
        ) : null}
      </div>

      <dl className="week-summary__figures">
        <div>
          <dt>Comida</dt>
          <dd>{week.averageKcal === null ? "—" : `${formatEnergy(week.averageKcal)} kcal/día`}</dd>
          <span>{recordedLabel(week.daysWithFood)}</span>
        </div>
        <div>
          <dt>Ejercicio</dt>
          <dd>{formatEnergy(week.totalExerciseKcal)} kcal</dd>
          <span>{recordedLabel(week.daysWithExercise)}</span>
        </div>
        <div>
          <dt>Sueño</dt>
          <dd>
            {week.averageSleepHours === null ? "—" : `${formatHours(week.averageSleepHours)}/noche`}
          </dd>
          <span>{recordedLabel(week.daysWithSleep)}</span>
        </div>
        <div>
          <dt>Peso</dt>
          <dd>{week.weightChangeKg === null ? "—" : formatWeight(week.weightChangeKg)}</dd>
          <span>tendencia</span>
        </div>
      </dl>

      {review.isError ? (
        <p className="auth-form__error" role="alert">
          {getMealErrorMessage(review.error)}
        </p>
      ) : null}

      {!hasSomething ? (
        <p className="week-summary__empty">
          Esa semana no tiene nada registrado, así que no hay nada que resumir.
        </p>
      ) : null}

      {written ? (
        <div className="week-summary__review">
          <p className="week-summary__headline">{written.headline}</p>
          <ul className="week-summary__observations">
            {written.observations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          {written.comparison ? (
            <p className="week-summary__comparison">
              <span>Frente a la semana anterior</span>
              {written.comparison}
            </p>
          ) : null}
          {!written.comparison && !week.hasPreviousReview ? (
            <p className="week-summary__comparison">
              <span>Frente a la semana anterior</span>
              No hay resumen de la semana anterior con el que compararla todavía.
            </p>
          ) : null}
          {written.watchOut ? (
            <p className="week-summary__watch">{written.watchOut}</p>
          ) : null}
          <p className="week-summary__note">
            {isClosed
              ? `Resumen cerrado el ${formatGenerated(written.generatedAt)}. La semana ya ha terminado, así que se queda como está.`
              : `Generado el ${formatGenerated(written.generatedAt)}, con la semana todavía en curso.`}
          </p>
        </div>
      ) : null}

      {!written && hasSomething && !week.canReview ? (
        <p className="week-summary__empty">
          Los resúmenes con IA no están configurados en este servidor.
        </p>
      ) : null}
    </article>
  );
};
