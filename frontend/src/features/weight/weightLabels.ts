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

/**
 * Described by what a day looks like, not by how often someone trains.
 *
 * The usual wording ("moderate" for three to five sessions a week) counts
 * training, which is recorded separately here, so borrowing it made people pick
 * a level one or two steps too high.
 */
export const activityOptions = [
  { value: "sedentary", label: "Sentado casi todo el día" },
  { value: "light", label: "De pie o andando un rato al día" },
  { value: "moderate", label: "En movimiento buena parte del día" },
  { value: "active", label: "Trabajo físico la mayor parte del día" },
  { value: "very_active", label: "Trabajo físico duro todo el día" },
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
