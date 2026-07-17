import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";

import { applicationConfig } from "./config/environment";
import { AppRouter } from "./routes/AppRouter";

export const App = () => {
  useEffect(() => {
    document.title = applicationConfig.name;
  }, []);

  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  );
};
