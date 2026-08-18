import axios from "axios";
import { ZodError } from "zod";

const GENERIC_MESSAGE = "No se pudo completar la operación. Inténtalo de nuevo.";

const messagesByStatus: Readonly<Record<number, string>> = {
  401: "El correo electrónico o la contraseña no son correctos.",
  403: "Esta cuenta no está activa. Ponte en contacto con el soporte.",
  409: "Ya existe una cuenta con este correo electrónico.",
  422: "Revisa los datos introducidos.",
  429: "Demasiados intentos. Espera unos minutos antes de volver a intentarlo.",
  503: "El inicio de sesión con Google no está disponible ahora mismo.",
};

/** Errors reported by the backend when it redirects back from Google. */
const messagesByCallbackError: Readonly<Record<string, string>> = {
  access_denied: "Has cancelado el acceso con Google.",
  account_inactive: "Esta cuenta no está activa. Ponte en contacto con el soporte.",
  email_already_registered:
    "Ya existe una cuenta con este correo electrónico. Inicia sesión con tu contraseña.",
  google_exchange_failed: "No se pudo completar el acceso con Google. Inténtalo de nuevo.",
  invalid_state: "La sesión de acceso con Google ha caducado. Vuelve a intentarlo.",
  missing_authorization_code: "Google no devolvió la información necesaria para continuar.",
};

export const getAuthErrorMessage = (error: unknown): string => {
  if (error instanceof ZodError) {
    return "El servicio respondió con un formato inesperado.";
  }

  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") {
      return "La solicitud tardó más de lo esperado.";
    }

    if (!error.response) {
      return "No se pudo conectar con el servicio en este momento.";
    }

    return messagesByStatus[error.response.status] ?? GENERIC_MESSAGE;
  }

  return GENERIC_MESSAGE;
};

export const getCallbackErrorMessage = (callbackError: string): string =>
  messagesByCallbackError[callbackError] ?? "No se pudo completar el acceso con Google.";
