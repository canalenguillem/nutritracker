import { formatEnergy } from "../features/meals/mealLabels";
import { useHistory } from "../features/meals/useMeals";
import type { DailySummary } from "../types/meal";

const DAYS = 7;

interface DayStripProps {
  readonly selectedDay: string;
  readonly onSelect: (day: string) => void;
}

const weekdayOf = (isoDay: string): string => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);

  return new Intl.DateTimeFormat("es-ES", { weekday: "narrow" }).format(
    new Date(year, month - 1, day),
  );
};

const dayNumberOf = (isoDay: string): string => isoDay.split("-")[2] ?? "";

/** The tallest bar sets the scale, so the week is compared against itself. */
const scaleOf = (days: readonly DailySummary[]): number =>
  Math.max(...days.map((day) => Math.max(day.kcal, day.exerciseKcal)), 1);

export const DayStrip = ({ selectedDay, onSelect }: DayStripProps) => {
  const history = useHistory(DAYS);
  const days = history.data ?? [];

  if (days.length === 0) {
    return null;
  }

  const scale = scaleOf(days);

  return (
    <section className="day-strip" aria-label="Últimos días">
      <h2>Últimos siete días</h2>
      <ol className="day-strip__list">
        {days.map((day) => {
          const isSelected = day.logDate === selectedDay;

          return (
            <li key={day.logDate}>
              <button
                type="button"
                className={
                  isSelected ? "day-strip__day day-strip__day--current" : "day-strip__day"
                }
                onClick={() => onSelect(day.logDate)}
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
                  {day.mealCount === 0 && day.exerciseCount === 0
                    ? "—"
                    : `${formatEnergy(day.kcal)}`}
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
