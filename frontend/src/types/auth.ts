import type { z } from "zod";

import type {
  loginFormSchema,
  registerFormSchema,
  sessionResponseSchema,
  userResponseSchema,
} from "../schemas/authSchema";

export type UserResponse = z.infer<typeof userResponseSchema>;

export type SessionResponse = z.infer<typeof sessionResponseSchema>;

export type LoginFormValues = z.infer<typeof loginFormSchema>;

export type RegisterFormValues = z.infer<typeof registerFormSchema>;

export type UserRole = UserResponse["role"];

export type AuthStatus = "loading" | "authenticated" | "anonymous";

export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  readonly displayName: string;
  readonly role: UserRole;
  readonly avatarUrl: string | null;
}

export interface Session {
  readonly user: AuthenticatedUser;
  readonly accessToken: string;
  readonly expiresIn: number;
}
