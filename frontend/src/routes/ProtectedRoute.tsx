import { Navigate, Outlet, useLocation } from "react-router-dom";

import { PageLoader } from "../components/PageLoader";
import { useAuth } from "../features/auth/useAuth";

export const ProtectedRoute = () => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <PageLoader message="Comprobando tu sesión…" />;
  }

  if (status !== "authenticated") {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
};
