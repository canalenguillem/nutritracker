import type { SleepQuality } from "../../types/sleep";

const qualityLabels: Readonly<Record<SleepQuality, string>> = {
  poor: "Mal",
  fair: "Regular",
  good: "Bien",
  very_good: "Muy bien",
};

export const qualityOptions = [
  { value: "", label: "Prefiero no decirlo" },
  { value: "poor", label: qualityLabels.poor },
  { value: "fair", label: qualityLabels.fair },
  { value: "good", label: qualityLabels.good },
  { value: "very_good", label: qualityLabels.very_good },
] as const;

export const getQualityLabel = (quality: SleepQuality): string => qualityLabels[quality];

export const formatSleepLength = (hours: number): string => {
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);

  if (minutes === 0) {
    return `${wholeHours} h`;
  }
  if (minutes === 60) {
    return `${wholeHours + 1} h`;
  }

  return `${wholeHours} h ${minutes} min`;
};
