const DEFAULT_APP_NAME = "NutriTrack AI";
const DEFAULT_API_BASE_URL = "/api/v1";
const DEFAULT_API_TIMEOUT_MS = 10_000;

const getNonEmptyValue = (value: string | undefined, fallback: string): string => {
  const normalizedValue = value?.trim();

  return normalizedValue ? normalizedValue : fallback;
};

const getPositiveNumber = (value: string | undefined, fallback: number): number => {
  const parsedValue = Number(value);

  return Number.isFinite(parsedValue) && parsedValue > 0 ? parsedValue : fallback;
};

const trimTrailingSlash = (value: string): string => value.replace(/\/$/, "");

export const applicationConfig = Object.freeze({
  name: getNonEmptyValue(import.meta.env.VITE_APP_NAME, DEFAULT_APP_NAME),
  apiBaseUrl: trimTrailingSlash(
    getNonEmptyValue(import.meta.env.VITE_API_BASE_URL, DEFAULT_API_BASE_URL),
  ),
  apiTimeoutMs: getPositiveNumber(
    import.meta.env.VITE_API_TIMEOUT_MS,
    DEFAULT_API_TIMEOUT_MS,
  ),
});
