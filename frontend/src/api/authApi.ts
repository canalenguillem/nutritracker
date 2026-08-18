import { applicationConfig } from "../config/environment";
import { sessionResponseSchema, userResponseSchema } from "../schemas/authSchema";
import type {
  AuthenticatedUser,
  LoginFormValues,
  RegisterFormValues,
  Session,
  UserResponse,
} from "../types/auth";
import { httpClient } from "./httpClient";

export const googleLoginUrl = `${applicationConfig.apiBaseUrl}/auth/google/login`;

const toAuthenticatedUser = (response: UserResponse): AuthenticatedUser => ({
  id: response.id,
  email: response.email,
  displayName: response.display_name,
  role: response.role,
  avatarUrl: response.avatar_url,
});

const toSession = (data: unknown): Session => {
  const parsedResponse = sessionResponseSchema.parse(data);

  return {
    user: toAuthenticatedUser(parsedResponse.user),
    accessToken: parsedResponse.access_token,
    expiresIn: parsedResponse.expires_in,
  };
};

export const registerAccount = async (values: RegisterFormValues): Promise<Session> => {
  const response = await httpClient.post<unknown>("/auth/register", {
    email: values.email,
    display_name: values.displayName,
    password: values.password,
  });

  return toSession(response.data);
};

export const login = async (values: LoginFormValues): Promise<Session> => {
  const response = await httpClient.post<unknown>("/auth/login", {
    email: values.email,
    password: values.password,
  });

  return toSession(response.data);
};

export const refreshSession = async (): Promise<Session> => {
  const response = await httpClient.post<unknown>("/auth/refresh");

  return toSession(response.data);
};

export const logout = async (): Promise<void> => {
  await httpClient.post("/auth/logout");
};

export const getCurrentUser = async (): Promise<AuthenticatedUser> => {
  const response = await httpClient.get<unknown>("/auth/me");

  return toAuthenticatedUser(userResponseSchema.parse(response.data));
};
