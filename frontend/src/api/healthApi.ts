import { readinessResponseSchema } from "../schemas/healthSchema";
import type {
  Availability,
  ReadinessReport,
  ReadinessResponse,
  ServiceHealth,
} from "../types/health";
import { httpClient } from "./httpClient";

const serviceLabels: Readonly<Record<string, string>> = {
  backend: "API",
  database: "Base de datos",
  mariadb: "Base de datos",
  redis: "Caché",
};

const getAvailability = (
  status: ReadinessResponse["status"],
): Availability => (status === "healthy" ? "available" : "unavailable");

const getServiceLabel = (serviceId: string): string => {
  const knownLabel = serviceLabels[serviceId.toLowerCase()];

  if (knownLabel) {
    return knownLabel;
  }

  const normalizedLabel = serviceId.replaceAll(/[_-]/g, " ").trim();

  return normalizedLabel
    ? normalizedLabel.charAt(0).toUpperCase() + normalizedLabel.slice(1)
    : "Servicio";
};

const toReadinessReport = (response: ReadinessResponse): ReadinessReport => {
  const services: readonly ServiceHealth[] = Object.entries(response.services).map(
    ([serviceId, status]) => ({
      id: serviceId,
      label: getServiceLabel(serviceId),
      availability: getAvailability(status),
    }),
  );

  return {
    availability: getAvailability(response.status),
    appName: response.app_name,
    environment: response.environment,
    version: response.version,
    checkedAt: response.timestamp,
    services,
  };
};

export const getReadiness = async (): Promise<ReadinessReport> => {
  const response = await httpClient.get<unknown>("/health/ready", {
    validateStatus: (status) =>
      (status >= 200 && status < 300) || status === 503,
  });
  const parsedResponse = readinessResponseSchema.parse(response.data);

  return toReadinessReport(parsedResponse);
};
