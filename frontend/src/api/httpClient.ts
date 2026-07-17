import axios from "axios";

import { applicationConfig } from "../config/environment";

export const httpClient = axios.create({
  baseURL: applicationConfig.apiBaseUrl,
  timeout: applicationConfig.apiTimeoutMs,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});
