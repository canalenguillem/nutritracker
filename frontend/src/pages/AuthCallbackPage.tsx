import { Link, Navigate, useSearchParams } from "react-router-dom";

import { PageLoader } from "../components/PageLoader";
import { getCallbackErrorMessage } from "../features/auth/authErrors";
import { useAuth } from "../features/auth/useAuth";

export const AuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const { status } = useAuth();
  const callbackError = searchParams.get("error");

  if (callbackError) {
    return (
      <div className="page-loader">
        <p className="auth-form__error" role="alert">
          {getCallbackErrorMessage(callbackError)}
        </p>
        <Link className="text-link" to="/login">
          Volver al inicio de sesión
        </Link>
      </div>
    );
  }

  if (status === "loading") {
    return <PageLoader message="Completando el acceso…" />;
  }

  return <Navigate to={status === "authenticated" ? "/dashboard" : "/login"} replace />;
};
