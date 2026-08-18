import axios from "axios";
import { ZodError } from "zod";

const GENERIC_MESSAGE = "No se pudo completar la operación. Inténtalo de nuevo.";

/** Codes the API names explicitly, where the status alone is not enough. */
const messagesByCode: Readonly<Record<string, string>> = {
  IMAGE_TOO_LARGE: "La foto pesa demasiado. Prueba con una imagen más pequeña.",
  INVALID_IMAGE: "El archivo no es una imagen JPEG, PNG o WebP.",
};

const messagesByStatus: Readonly<Record<number, string>> = {
  401: "Tu sesión ha caducado. Vuelve a iniciar sesión.",
  403: "No tienes acceso a este contenido.",
  404: "Este registro ya no existe.",
  422: "Revisa los datos introducidos.",
  429: "Has hecho demasiadas peticiones seguidas. Espera un momento.",
  502: "No se pudo estimar la comida. Prueba a describirla de otra forma.",
  503: "El estimador todavía no está configurado. Puedes introducir los valores a mano.",
};

export const getMealErrorMessage = (error: unknown): string => {
  if (error instanceof ZodError) {
    return "El servicio respondió con un formato inesperado.";
  }

  if (axios.isAxiosError(error)) {
    if (error.code === "ECONNABORTED") {
      return "La estimación tardó más de lo esperado. Inténtalo de nuevo.";
    }

    if (!error.response) {
      return "No se pudo conectar con el servicio en este momento.";
    }

    const code = (error.response.data as { error?: { code?: string } } | undefined)?.error?.code;
    if (code && messagesByCode[code]) {
      return messagesByCode[code] as string;
    }

    return messagesByStatus[error.response.status] ?? GENERIC_MESSAGE;
  }

  return GENERIC_MESSAGE;
};
