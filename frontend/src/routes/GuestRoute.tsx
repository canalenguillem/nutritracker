import { Navigate, Outlet } from "react-router-dom";

import { PageLoader } from "../components/PageLoader";
import { useAuth } from "../features/auth/useAuth";

export const GuestRoute = () => {
  const { status } = useAuth();

  if (status === "loading") {
    return <PageLoader message="Comprobando tu sesión…" />;
  }

  if (status === "authenticated") {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
};
