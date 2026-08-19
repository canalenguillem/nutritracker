import { formatDay } from "../features/meals/mealLabels";

interface DayPickerProps {
  readonly selectedDay: string;
  readonly today: string;
  readonly onSelect: (day: string) => void;
}

const shift = (isoDay: string, days: number): string => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);
  const moved = new Date(year, month - 1, day + days);
  const pad = (value: number): string => String(value).padStart(2, "0");

  return `${moved.getFullYear()}-${pad(moved.getMonth() + 1)}-${pad(moved.getDate())}`;
};

export const DayPicker = ({ selectedDay, today, onSelect }: DayPickerProps) => {
  const isToday = selectedDay === today;

  return (
    <div className="day-picker">
      <button
        className="day-picker__step"
        type="button"
        onClick={() => onSelect(shift(selectedDay, -1))}
        aria-label="Día anterior"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path d="m12 4-6 6 6 6" />
        </svg>
      </button>

      <p className="day-picker__label">{isToday ? "Hoy" : formatDay(selectedDay)}</p>

      <button
        className="day-picker__step"
        type="button"
        onClick={() => onSelect(shift(selectedDay, 1))}
        disabled={isToday}
        aria-label="Día siguiente"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path d="m8 4 6 6-6 6" />
        </svg>
      </button>

      {isToday ? null : (
        <button className="day-picker__today" type="button" onClick={() => onSelect(today)}>
          Volver a hoy
        </button>
      )}
    </div>
  );
};
