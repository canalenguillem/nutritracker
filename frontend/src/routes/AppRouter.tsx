import { Navigate, Route, Routes } from "react-router-dom";

import { PublicLayout } from "../layouts/PublicLayout";
import { HomePage } from "../pages/HomePage";

export const AppRouter = () => (
  <Routes>
    <Route element={<PublicLayout />}>
      <Route index element={<HomePage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes>
);
