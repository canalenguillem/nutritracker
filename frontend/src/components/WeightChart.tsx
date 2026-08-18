import type { WeightPoint } from "../types/weight";

const WIDTH = 720;
const HEIGHT = 240;
const PADDING_X = 8;
const PADDING_Y = 18;

interface WeightChartProps {
  readonly points: readonly WeightPoint[];
  readonly targetWeightKg: number | null;
  /** The day the trend would meet the target, drawn as a dashed continuation. */
  readonly reachesTargetOn: string | null;
}

const toOrdinal = (isoDay: string): number => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);

  return Date.UTC(year, month - 1, day) / 86_400_000;
};

export const WeightChart = ({
  points,
  targetWeightKg,
  reachesTargetOn,
}: WeightChartProps) => {
  if (points.length === 0) {
    return null;
  }

  const days = points.map((point) => toOrdinal(point.measuredOn));
  const firstDay = days[0] ?? 0;
  const lastReadingDay = days[days.length - 1] ?? firstDay;
  const latest = points[points.length - 1];

  // The projection extends the horizontal range, so the meeting point fits.
  const projectedDay =
    reachesTargetOn !== null && targetWeightKg !== null ? toOrdinal(reachesTargetOn) : null;
  const lastDay = projectedDay !== null ? Math.max(lastReadingDay, projectedDay) : lastReadingDay;
  const daySpan = Math.max(lastDay - firstDay, 1);

  const values = points.flatMap((point) => [point.weightKg, point.trendKg]);
  if (targetWeightKg !== null) {
    values.push(targetWeightKg);
  }
  const lowest = Math.min(...values);
  const highest = Math.max(...values);
  // A flat series would divide by zero, and a hair of range keeps it centred.
  const valueSpan = Math.max(highest - lowest, 0.5);

  const toX = (day: number): number =>
    PADDING_X + ((day - firstDay) / daySpan) * (WIDTH - PADDING_X * 2);
  const toY = (value: number): number =>
    HEIGHT - PADDING_Y - ((value - lowest) / valueSpan) * (HEIGHT - PADDING_Y * 2);

  const trendPath = points
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      const x = toX(days[index] ?? firstDay).toFixed(1);

      return `${command}${x} ${toY(point.trendKg).toFixed(1)}`;
    })
    .join(" ");

  const summary =
    `Evolución del peso entre ${points[0]?.measuredOn} y ` +
    `${latest?.measuredOn}, de ${lowest.toFixed(1)} a ${highest.toFixed(1)} kilos.` +
    (reachesTargetOn !== null
      ? ` La tendencia alcanzaría el objetivo el ${reachesTargetOn}.`
      : "");

  return (
    <figure className="weight-chart">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={summary}>
        {targetWeightKg !== null ? (
          <line
            className="weight-chart__target"
            x1={PADDING_X}
            x2={WIDTH - PADDING_X}
            y1={toY(targetWeightKg)}
            y2={toY(targetWeightKg)}
          />
        ) : null}

        {points.length > 1 ? <path className="weight-chart__trend" d={trendPath} /> : null}

        {projectedDay !== null && targetWeightKg !== null && latest ? (
          <>
            <line
              className="weight-chart__projection"
              x1={toX(lastReadingDay)}
              y1={toY(latest.trendKg)}
              x2={toX(projectedDay)}
              y2={toY(targetWeightKg)}
            />
            <circle
              className="weight-chart__goal"
              cx={toX(projectedDay)}
              cy={toY(targetWeightKg)}
              r={5}
            />
          </>
        ) : null}

        {points.map((point, index) => (
          <circle
            key={point.measuredOn}
            className="weight-chart__reading"
            cx={toX(days[index] ?? firstDay)}
            cy={toY(point.weightKg)}
            r={3}
          />
        ))}
      </svg>
      <figcaption>
        <span className="weight-chart__key weight-chart__key--trend">Tendencia</span>
        <span className="weight-chart__key weight-chart__key--reading">
          Lo que marcó la báscula
        </span>
        {targetWeightKg !== null ? (
          <span className="weight-chart__key weight-chart__key--target">Objetivo</span>
        ) : null}
        {projectedDay !== null ? (
          <span className="weight-chart__key weight-chart__key--projection">
            A este ritmo
          </span>
        ) : null}
      </figcaption>
    </figure>
  );
};
