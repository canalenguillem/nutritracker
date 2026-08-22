import { addDays, formatEnergy, fromIsoDay, mondayOf } from "../features/meals/mealLabels";
import { useHistory } from "../features/meals/useMeals";
import type { DailySummary } from "../types/meal";

interface DayStripProps {
  readonly selectedDay: string;
  readonly today: string;
  readonly onSelect: (day: string) => void;
}

const weekdayOf = (isoDay: string): string =>
  new Intl.DateTimeFormat("es-ES", { weekday: "narrow" }).format(fromIsoDay(isoDay));

const dayNumberOf = (isoDay: string): string => isoDay.split("-")[2] ?? "";

/** Never step past today: a week ahead of it has no days to read. */
const minIso = (day: string, limit: string): string => (day > limit ? limit : day);

const weekLabel = (monday: string, sunday: string): string => {
  const short = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short" });

  return `${short.format(fromIsoDay(monday))} – ${short.format(fromIsoDay(sunday))}`;
};

/** The tallest bar sets the scale, so the week is compared against itself. */
const scaleOf = (days: readonly DailySummary[]): number =>
  Math.max(...days.map((day) => Math.max(day.kcal, day.exerciseKcal)), 1);

export const DayStrip = ({ selectedDay, today, onSelect }: DayStripProps) => {
  // The week runs Monday to Sunday, and it is the week of the day being read,
  // so stepping back into last week brings that week's strip with it.
  const monday = mondayOf(selectedDay);
  const sunday = addDays(monday, 6);
  const history = useHistory(monday, sunday);
  const days = history.data ?? [];

  if (days.length === 0) {
    return null;
  }

  const scale = scaleOf(days);
  const isThisWeek = mondayOf(today) === monday;

  return (
    <section className="day-strip" aria-label="Semana">
      <div className="day-strip__head">
        <button
          className="day-picker__step"
          type="button"
          onClick={() => onSelect(addDays(monday, -7))}
          aria-label="Semana anterior"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="m12 4-6 6 6 6" />
          </svg>
        </button>

        <h2>{isThisWeek ? "Esta semana" : weekLabel(monday, sunday)}</h2>

        <button
          className="day-picker__step"
          type="button"
          onClick={() => onSelect(minIso(addDays(monday, 7), today))}
          disabled={isThisWeek}
          aria-label="Semana siguiente"
        >
          <svg viewBox="0 0 20 20" aria-hidden="true">
            <path d="m8 4 6 6-6 6" />
          </svg>
        </button>
      </div>
      <ol className="day-strip__list">
        {days.map((day) => {
          const isSelected = day.logDate === selectedDay;
          const isFuture = day.logDate > today;

          return (
            <li key={day.logDate}>
              <button
                type="button"
                className={
                  isSelected ? "day-strip__day day-strip__day--current" : "day-strip__day"
                }
                onClick={() => onSelect(day.logDate)}
                disabled={isFuture}
                aria-current={isSelected ? "date" : undefined}
              >
                <span className="day-strip__bars" aria-hidden="true">
                  <span
                    className="day-strip__bar day-strip__bar--food"
                    style={{ height: `${(day.kcal / scale) * 100}%` }}
                  />
                  <span
                    className="day-strip__bar day-strip__bar--exercise"
                    style={{ height: `${(day.exerciseKcal / scale) * 100}%` }}
                  />
                </span>
                <span className="day-strip__weekday">{weekdayOf(day.logDate)}</span>
                <span className="day-strip__number">{dayNumberOf(day.logDate)}</span>
                <span className="day-strip__kcal">
                  {isFuture || (day.mealCount === 0 && day.exerciseCount === 0)
                    ? "—"
                    : formatEnergy(day.kcal)}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      <p className="day-strip__key">
        <span className="day-strip__key-item day-strip__key-item--food">Comida</span>
        <span className="day-strip__key-item day-strip__key-item--exercise">Ejercicio</span>
        <span className="day-strip__hint">Toca un día para verlo entero.</span>
      </p>
    </section>
  );
};
