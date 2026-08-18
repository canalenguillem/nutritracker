import type { ExerciseIntensity } from "../../types/exercise";

const intensityLabels: Readonly<Record<ExerciseIntensity, string>> = {
  low: "Suave",
  moderate: "Moderada",
  high: "Fuerte",
  very_high: "Muy fuerte",
};

export const intensityOptions = [
  { value: "low", label: intensityLabels.low },
  { value: "moderate", label: intensityLabels.moderate },
  { value: "high", label: intensityLabels.high },
  { value: "very_high", label: intensityLabels.very_high },
] as const;

export const getIntensityLabel = (intensity: ExerciseIntensity): string =>
  intensityLabels[intensity];

export const formatDuration = (minutes: number): string => {
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;

  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
};
