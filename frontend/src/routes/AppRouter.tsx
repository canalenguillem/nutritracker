import { Navigate, Route, Routes } from "react-router-dom";

import { AuthLayout } from "../layouts/AuthLayout";
import { PrivateLayout } from "../layouts/PrivateLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { AddExercisePage } from "../pages/AddExercisePage";
import { AddMealPage } from "../pages/AddMealPage";
import { AddSleepPage } from "../pages/AddSleepPage";
import { AuthCallbackPage } from "../pages/AuthCallbackPage";
import { DashboardPage } from "../pages/DashboardPage";
import { HomePage } from "../pages/HomePage";
import { LoginPage } from "../pages/LoginPage";
import { ProfilePage } from "../pages/ProfilePage";
import { WeightPage } from "../pages/WeightPage";
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
        {/* Sign-up is closed for now; RegisterPage stays for when it reopens. */}
      </Route>
    </Route>

    <Route path="auth/callback" element={<AuthCallbackPage />} />

    <Route element={<ProtectedRoute />}>
      <Route element={<PrivateLayout />}>
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="meals/new" element={<AddMealPage />} />
        <Route path="exercises/new" element={<AddExercisePage />} />
        <Route path="sleep/new" element={<AddSleepPage />} />
        <Route path="weight" element={<WeightPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
    </Route>

    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);
