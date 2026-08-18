import { createContext } from "react";

import type {
  AuthStatus,
  AuthenticatedUser,
  LoginFormValues,
  RegisterFormValues,
} from "../../types/auth";

export interface AuthContextValue {
  readonly status: AuthStatus;
  readonly user: AuthenticatedUser | null;
  readonly signIn: (values: LoginFormValues) => Promise<void>;
  readonly signUp: (values: RegisterFormValues) => Promise<void>;
  readonly signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
