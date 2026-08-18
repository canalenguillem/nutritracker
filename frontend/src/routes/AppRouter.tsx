import { Navigate, Route, Routes } from "react-router-dom";

import { AuthLayout } from "../layouts/AuthLayout";
import { PrivateLayout } from "../layouts/PrivateLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { AuthCallbackPage } from "../pages/AuthCallbackPage";
import { DashboardPage } from "../pages/DashboardPage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { GuestRoute } from "./GuestRoute";
import { ProtectedRoute } from "./ProtectedRoute";

export const AppRouter = () => (
  <Routes>
    <Route element={<PublicLayout />}>
      <Route index element={<HomePage />} />
    </Route>

    <Route element={<GuestRoute />}>
      <Route element={<AuthLayout />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
    </Route>

    <Route path="auth/callback" element={<AuthCallbackPage />} />

    <Route element={<ProtectedRoute />}>
      <Route element={<PrivateLayout />}>
        <Route path="dashboard" element={<DashboardPage />} />
      </Route>
    </Route>

    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);
