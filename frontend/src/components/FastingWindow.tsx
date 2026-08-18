import { formatFastingLength, formatTime } from "../features/meals/mealLabels";
import type { DailySummary } from "../types/meal";

interface FastingWindowProps {
  readonly summary: DailySummary;
}

export const FastingWindow = ({ summary }: FastingWindowProps) => {
  if (summary.fastingHours === null || summary.fastingStartedAt === null) {
    return null;
  }

  const length = formatFastingLength(summary.fastingHours);
  const from = formatTime(summary.fastingStartedAt);

  return (
    <div className="fasting">
      <p className="fasting__label">{summary.fastingOngoing ? "Ayuno en curso" : "Ayuno"}</p>
      <p className="fasting__value">{length}</p>
      <p className="fasting__detail">
        {summary.fastingOngoing
          ? `Desde tu última comida, a las ${from}.`
          : `De las ${from} a las ${formatTime(summary.fastingEndedAt ?? "")}.`}{" "}
        Sale del hueco entre comidas, así que no hay nada que registrar.
      </p>
    </div>
  );
};
