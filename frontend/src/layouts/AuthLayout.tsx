import { Outlet } from "react-router-dom";

import { Brand } from "../components/Brand";

export const AuthLayout = () => (
  <div className="auth-shell">
    <div className="auth-shell__glow" aria-hidden="true" />
    <header className="auth-shell__header">
      <div className="container">
        <Brand />
      </div>
    </header>

    <main className="auth-shell__main">
      <div className="container auth-shell__content">
        <Outlet />
      </div>
    </main>

    <footer className="auth-shell__footer">
      <div className="container">
        <p>
          Los valores nutricionales y el balance calórico son estimaciones y no sustituyen el
          consejo de un profesional sanitario.
        </p>
      </div>
    </footer>
  </div>
);
