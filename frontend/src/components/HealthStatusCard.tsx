import axios from "axios";
import { ZodError } from "zod";

import { useReadiness } from "../features/health/useReadiness";
import type { Availability } from "../types/health";

const environmentLabels: Readonly<Record<string, string>> = {
  development: "desarrollo",
  production: "producción",
  test: "pruebas",
  testing: "pruebas",
};

const getErrorMessage = (error: unknown): string => {
  if (error instanceof ZodError) {
    return "El servicio respondió con un formato inesperado.";
  }

  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") {
      return "La comprobación tardó más de lo esperado.";
    }

    if (!error.response) {
      return "No se pudo conectar con el servicio en este momento.";
    }
  }

  return "No se pudo completar la comprobación de disponibilidad.";
};

const getEnvironmentLabel = (environment: string): string =>
  environmentLabels[environment.toLowerCase()] ?? environment;

const getAvailabilityLabel = (availability: Availability): string =>
  availability === "available" ? "Disponible" : "No disponible";

const formatCheckedAt = (value: string): string =>
  new Intl.DateTimeFormat("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));

export const HealthStatusCard = () => {
  const readinessQuery = useReadiness();

  if (readinessQuery.isPending) {
    return (
      <div className="health-card health-card--loading" aria-live="polite">
        <div className="health-card__heading">
          <span className="status-indicator status-indicator--loading" aria-hidden="true" />
          <div>
            <p className="health-card__eyebrow">Estado del sistema</p>
            <h3>Comprobando disponibilidad</h3>
          </div>
        </div>
        <p className="health-card__message">
          Estamos consultando el servicio. Solo tardará un momento.
        </p>
        <div className="health-card__skeleton" aria-hidden="true">
          <span />
          <span />
        </div>
      </div>
    );
  }

  if (readinessQuery.isError) {
    return (
      <div className="health-card health-card--error" role="status" aria-live="polite">
        <div className="health-card__heading">
          <span className="status-indicator status-indicator--error" aria-hidden="true" />
          <div>
            <p className="health-card__eyebrow">Estado del sistema</p>
            <h3>Servicio no disponible</h3>
          </div>
        </div>
        <p className="health-card__message">{getErrorMessage(readinessQuery.error)}</p>
        <button
          className="button button--secondary button--small"
          type="button"
          onClick={() => void readinessQuery.refetch()}
          disabled={readinessQuery.isFetching}
        >
          {readinessQuery.isFetching ? "Comprobando…" : "Volver a comprobar"}
        </button>
      </div>
    );
  }

  const { data } = readinessQuery;
  const isAvailable = data.availability === "available";

  return (
    <div
      className={`health-card ${
        isAvailable ? "health-card--available" : "health-card--unavailable"
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="health-card__heading">
        <span
          className={`status-indicator ${
            isAvailable ? "status-indicator--available" : "status-indicator--unavailable"
          }`}
          aria-hidden="true"
        />
        <div>
          <p className="health-card__eyebrow">Estado del sistema</p>
          <h3>{isAvailable ? "Todo listo" : "Disponibilidad limitada"}</h3>
        </div>
      </div>

      <p className="health-card__message">
        {isAvailable
          ? "El servicio está preparado para recibir solicitudes."
          : "La aplicación responde, pero uno o más servicios todavía no están preparados."}
      </p>

      <ul className="service-list" aria-label="Servicios comprobados">
        <li className="service-list__item">
          <span>API</span>
          <span className="service-list__value service-list__value--available">
            Conectada
          </span>
        </li>
        {data.services.map((service) => (
          <li className="service-list__item" key={service.id}>
            <span>{service.label}</span>
            <span className={`service-list__value service-list__value--${service.availability}`}>
              {getAvailabilityLabel(service.availability)}
            </span>
          </li>
        ))}
      </ul>

      <div className="health-card__footer">
        <p>
          {data.appName} · v{data.version} · {getEnvironmentLabel(data.environment)}
          <br />
          Última comprobación: {formatCheckedAt(data.checkedAt)}
        </p>
        <button
          className="health-card__refresh"
          type="button"
          onClick={() => void readinessQuery.refetch()}
          disabled={readinessQuery.isFetching}
          aria-label="Actualizar el estado del sistema"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M19 8.5V4.75h-3.75" />
            <path d="M19 4.75a8 8 0 1 0 .65 13.75" />
          </svg>
          {readinessQuery.isFetching ? "Actualizando…" : "Actualizar"}
        </button>
      </div>
    </div>
  );
};
