import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";

import { applicationConfig } from "./config/environment";
import { AuthProvider } from "./features/auth/AuthProvider";
import { AppRouter } from "./routes/AppRouter";

export const App = () => {
  useEffect(() => {
    document.title = applicationConfig.name;
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
};
