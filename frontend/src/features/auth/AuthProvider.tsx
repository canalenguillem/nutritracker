import { type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { setAccessToken } from "../../api/accessTokenStore";
import { login, logout, refreshSession, registerAccount } from "../../api/authApi";
import { refreshSessionOnce, registerSessionRefreshHandler } from "../../api/sessionRefresh";
import type {
  AuthStatus,
  AuthenticatedUser,
  LoginFormValues,
  RegisterFormValues,
  Session,
} from "../../types/auth";
import { AuthContext, type AuthContextValue } from "./authContext";

interface AuthState {
  readonly status: AuthStatus;
  readonly user: AuthenticatedUser | null;
}

const INITIAL_STATE: AuthState = { status: "loading", user: null };
const ANONYMOUS_STATE: AuthState = { status: "anonymous", user: null };

interface AuthProviderProps {
  readonly children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [state, setState] = useState<AuthState>(INITIAL_STATE);
  const queryClient = useQueryClient();

  const applySession = useCallback((session: Session) => {
    setAccessToken(session.accessToken);
    setState({ status: "authenticated", user: session.user });
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setState(ANONYMOUS_STATE);
  }, []);

  // The access token only lives in memory, so every reload rebuilds the session
  // from the refresh cookie. The same handler renews expired access tokens.
  useEffect(() => {
    registerSessionRefreshHandler(async () => {
      try {
        const session = await refreshSession();
        applySession(session);

        return session.accessToken;
      } catch {
        clearSession();

        return null;
      }
    });

    return () => registerSessionRefreshHandler(null);
  }, [applySession, clearSession]);

  useEffect(() => {
    void refreshSessionOnce().then(() => {
      setState((current) => (current.status === "loading" ? ANONYMOUS_STATE : current));
    });
  }, []);

  const signIn = useCallback(
    async (values: LoginFormValues) => {
      applySession(await login(values));
    },
    [applySession],
  );

  const signUp = useCallback(
    async (values: RegisterFormValues) => {
      applySession(await registerAccount(values));
    },
    [applySession],
  );

  const signOut = useCallback(async () => {
    try {
      await logout();
    } finally {
      clearSession();
      queryClient.clear();
    }
  }, [clearSession, queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({ status: state.status, user: state.user, signIn, signUp, signOut }),
    [signIn, signOut, signUp, state.status, state.user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
