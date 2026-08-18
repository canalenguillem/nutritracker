import axios, { type InternalAxiosRequestConfig } from "axios";

import { applicationConfig } from "../config/environment";
import { getAccessToken } from "./accessTokenStore";
import { refreshSessionOnce } from "./sessionRefresh";

/** Endpoints that establish a session and must never be retried after a refresh. */
const SESSION_ENDPOINTS = ["/auth/login", "/auth/register", "/auth/refresh", "/auth/logout"];

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  hasRetriedAfterRefresh?: boolean;
}

export const httpClient = axios.create({
  baseURL: applicationConfig.apiBaseUrl,
  timeout: applicationConfig.apiTimeoutMs,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const accessToken = getAccessToken();

  if (accessToken) {
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return config;
});

httpClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) {
      throw error;
    }

    const request = error.config as RetriableRequestConfig | undefined;
    const requestUrl = request?.url ?? "";
    const isRetriable =
      request !== undefined &&
      request.hasRetriedAfterRefresh !== true &&
      !SESSION_ENDPOINTS.some((endpoint) => requestUrl.startsWith(endpoint));

    if (!isRetriable) {
      throw error;
    }

    const renewedAccessToken = await refreshSessionOnce();

    if (!renewedAccessToken) {
      throw error;
    }

    request.hasRetriedAfterRefresh = true;

    return httpClient.request(request);
  },
);
