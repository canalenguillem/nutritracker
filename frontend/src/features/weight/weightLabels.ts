const kilos = new Intl.NumberFormat("es-ES", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const signedKilos = new Intl.NumberFormat("es-ES", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "exceptZero",
});

export const formatKilos = (value: number): string => `${kilos.format(value)} kg`;

export const formatChange = (value: number): string => `${signedKilos.format(value)} kg`;

export const formatBodyMassIndex = (value: number): string =>
  new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 }).format(value);

export const formatMeasuredOn = (isoDay: string): string => {
  const [year = 0, month = 1, day = 1] = isoDay.split("-").map(Number);

  return new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short" }).format(
    new Date(year, month - 1, day),
  );
};

export const activityOptions = [
  { value: "sedentary", label: "Sedentario" },
  { value: "light", label: "Poco activo" },
  { value: "moderate", label: "Moderado" },
  { value: "active", label: "Activo" },
  { value: "very_active", label: "Muy activo" },
] as const;

export const goalOptions = [
  { value: "lose_weight", label: "Perder peso" },
  { value: "maintain_weight", label: "Mantenerme" },
  { value: "gain_muscle", label: "Ganar músculo" },
] as const;

export const sexOptions = [
  { value: "unspecified", label: "Prefiero no decirlo" },
  { value: "female", label: "Mujer" },
  { value: "male", label: "Hombre" },
] as const;
